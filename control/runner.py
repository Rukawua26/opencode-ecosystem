"""Lanzador de tareas: UNA a la vez, timeout, max 2 intentos, dead-letter."""

from __future__ import annotations

import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .db import (
    add_task,
    claim_next,
    list_tasks,
    record_event,
    scrub_task_payload,
    update_task,
)

TIMEOUT_S = 900          # 15 min por tarea
VERIFY_TIMEOUT_S = 120   # checks deterministas cortos
MAX_ATTEMPTS = 2         # luego -> dead
_VERIFY_AGENT = "sdd-verify"


# patrones -> error_kind. El texto se usa SOLO para clasificar, nunca se guarda.
_ERROR_PATTERNS: tuple[tuple[str, str], ...] = (
    ("Insufficient Balance", "provider_balance"),
    ("rate limit", "provider_rate"),
    ("429", "provider_rate"),
    ("timeout 900s", "timeout"),
    ("opencode no encontrado", "infra"),
)


def _classify_error(stderr_tail: str, note: str) -> str:
    haystack = (stderr_tail + " " + note).lower()
    for needle, kind in _ERROR_PATTERNS:
        if needle.lower() in haystack:
            return kind
    return "agent"


def _workspace_path(workspace: str) -> Path | None:
    """Valida workspace local. Vacío conserva el cwd del proceso."""
    if not workspace:
        return None
    path = Path(workspace).expanduser().resolve()
    home = Path.home().resolve()
    if not path.is_dir() or (path != home and home not in path.parents):
        raise ValueError("workspace inexistente o fuera de HOME")
    return path


def _run_agent(
    agent: str, prompt: str, model: str = "", workspace: str = ""
) -> tuple[int, float, str, str]:
    """Ejecuta `opencode run`. Devuelve (exit, duracion, resumen, error_kind)."""
    started = time.monotonic()
    cmd = ["opencode", "run", prompt, "--agent", agent]
    if model:
        cmd += ["--model", model]
    try:
        cwd = _workspace_path(workspace)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            cwd=str(cwd) if cwd else None,
        )
        duration = round(time.monotonic() - started, 2)
        # stdout/stderr se usan SOLO en memoria para clasificar; nunca persisten.
        transient_output = (proc.stderr or "") + "\n" + (proc.stdout or "")
        kind = "" if proc.returncode == 0 else _classify_error(transient_output, "")
        return proc.returncode, duration, "", kind
    except subprocess.TimeoutExpired:
        return 124, round(time.monotonic() - started, 2), "timeout 900s", "timeout"
    except FileNotFoundError:
        return 127, 0.0, "opencode no encontrado", "infra"
    except ValueError as exc:
        return 2, 0.0, str(exc), "contract"


def _run_verification(command: str, workspace: str) -> tuple[int, str]:
    """Ejecuta el check declarado sin persistir stdout/stderr."""
    if not command:
        return 0, ""
    try:
        cwd = _workspace_path(workspace)
        proc = subprocess.run(
            ["/usr/bin/bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=VERIFY_TIMEOUT_S,
            cwd=str(cwd) if cwd else None,
        )
        return proc.returncode, "" if proc.returncode == 0 else "verification_command fallo"
    except subprocess.TimeoutExpired:
        return 124, "verification_command timeout"
    except (FileNotFoundError, ValueError) as exc:
        return 2, str(exc)


_LEASE_S = TIMEOUT_S + 120  # lease cubre timeout + gracia


def run_next(path: Path | None = None, owner: str = "") -> dict | None:
    """Reclama y ejecuta la primera tarea pendiente con lease atomico."""
    owner = owner or f"runner-{uuid.uuid4().hex[:12]}"
    task = claim_next(owner, _LEASE_S, path)
    if task is None:
        return None
    tid, agent = task["id"], task["agent"]
    attempts = task["attempts"]
    record_event(agent, "task", "iniciada", "", f"task #{tid} intento {attempts}", path=path)

    code, duration, note, error_kind = _run_agent(
        agent, task["prompt"], task.get("model", ""), task.get("workspace", "")
    )
    if code == 0 and agent == _VERIFY_AGENT and task.get("verification_command"):
        verify_code, verify_note = _run_verification(
            task["verification_command"], task.get("workspace", "")
        )
        if verify_code != 0:
            code, note, error_kind = verify_code, verify_note, "verification"
        else:
            record_event(
                agent, "verification", "check determinista", "ok",
                f"task #{tid} verification_command rc=0", path=path,
            )
    finished = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if code == 0:
        update_task(tid, path, status="done", finished_at=finished, result_code=code,
                    lease_owner="", lease_until="", error_kind="")
        record_event(agent, "task", "completada", "ok",
                     f"task #{tid} en {duration}s", duration_s=duration, path=path)
        if agent == "sdd-implement":
            verifier_prompt = (
                f"Verifica en modo read-only la tarea #{tid}. "
                f"Workspace: {task.get('workspace') or '(actual)'}. "
                f"Feature: {task.get('feature') or '(no declarada)'}. "
                f"Tarea original: {task['prompt']}. "
                f"Salidas esperadas: {task.get('expected_outputs') or '(no declaradas)'}. "
                f"Verificacion esperada: {task.get('verification_command') or '(no declarada)'}. "
                "Inspecciona el diff y los checks existentes; no modifiques archivos."
            )
            vid = add_task(
                _VERIFY_AGENT,
                verifier_prompt,
                note=f"encadenada de task #{tid}",
                model=task.get("model", ""),
                parent_id=tid,
                workflow=task.get("workflow", "sdd"),
                workspace=task.get("workspace", ""),
                feature=task.get("feature", ""),
                expected_outputs=task.get("expected_outputs", ""),
                verification_command=task.get("verification_command", ""),
                model_policy=task.get("model_policy", "paid"),
                sensitivity=task.get("sensitivity", "normal"),
                path=path,
            )
            record_event(_VERIFY_AGENT, "task", "encolada", "",
                         f"task #{vid} tras task #{tid}", path=path)
        if task.get("sensitivity") == "sensitive":
            scrub_task_payload(tid, path)
        task["status"] = "done"
    elif error_kind.startswith("provider"):
        # fallo del proveedor: la tarea no tuvo oportunidad real.
        # vuelve a pending SIN consumir intento.
        update_task(tid, path, status="pending", finished_at=finished,
                    result_code=code, note=note, attempts=attempts - 1,
                    lease_owner="", lease_until="", error_kind=error_kind)
        record_event(agent, "task", "error de proveedor", "warn",
                     f"task #{tid} {error_kind} (sin quemar intento)", path=path)
        task["status"] = "pending"
    else:
        status = "pending" if attempts < MAX_ATTEMPTS else "dead"
        update_task(tid, path, status=status, finished_at=finished, result_code=code,
                    note=note, lease_owner="", lease_until="", error_kind=error_kind)
        record_event(agent, "task",
                     "falló" if status != "pending" else "reintento programado",
                     "fail", f"task #{tid} exit={code} {note} kind={error_kind}",
                     duration_s=duration, path=path)
        if status == "dead" and task.get("sensitivity") == "sensitive":
            scrub_task_payload(tid, path)
        task["status"] = status
    task["result_code"] = code
    return task


def queue_summary(path: Path | None = None) -> dict:
    """Conteo por estado para el panel."""
    counts = {"pending": 0, "running": 0, "done": 0, "failed": 0, "dead": 0}
    for t in list_tasks(200, path):
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    return counts
