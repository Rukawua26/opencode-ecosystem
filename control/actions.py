"""Acciones manuales del panel (Etapa 4).

Seguridad:
- Token CSRF por proceso (aleatorio). El cliente debe enviarlo en cabecera
  `X-CSRF-Token`. El servidor comprueba ademas el Origin.
- Lista cerrada de acciones permitidas. No hay shell arbitrario.
- El lanzador tiene lock: solo 1 tarea corre a la vez.
"""

from __future__ import annotations

import secrets
import subprocess
import threading
from datetime import datetime, timezone
from typing import Any

from . import runner
from .db import record_event, add_task, update_task, list_tasks, scrub_task_payload

# Token por proceso. Si reinicias el panel, el navegador pide uno nuevo.
_TOKEN = secrets.token_urlsafe(24)

# Agentes permitidos para encolar desde UI (lista cerrada).
ALLOWED_AGENTS = frozenset({
    "qa-gate", "risk-lens", "resilience-lens", "reliability-lens",
    "readability-lens", "context-compressor", "code-forge-fix-lite",
    "git-atomic-committer", "organic-workflow-lite", "ultraplan-lite",
    "odd-worker", "odd-verifier",
    "build", "plan", "general", "explore",
})
ALLOWED_MODELS = frozenset({
    "",
    "openai/gpt-5.6-sol",
    "openai/gpt-5.6-luna",
    "opencode/nemotron-3-ultra-free",
})

# Servicios cuyo nombre el launcher conoce como reiniciables.
RESTARTABLE_SYSTEMD = frozenset({
    "opencode-ram-guard.timer",
    "opencode-kairos.timer",
})

_runner_lock = threading.Lock()


def token() -> str:
    return _TOKEN


def _log(action: str, status: str, detail: str) -> None:
    record_event("panel", "accion", action, status, detail[:200])


def do_refresh() -> dict[str, Any]:
    """Fuerza recoleccion de snapshot."""
    from .state import get_store
    get_store().refresh(force=True)
    _log("refresh", "ok", "snapshot regenerado desde panel")
    return {"ok": True}


def do_run_next() -> dict[str, Any]:
    """Ejecuta la primera tarea pendiente. Bloqueante, el servidor usa hilos."""
    if not _runner_lock.acquire(blocking=False):
        return {"ok": False, "error": "lanzador ocupado"}
    try:
        task = runner.run_next()
        if task is None:
            _log("run", "ok", "cola vacia")
            return {"ok": True, "detail": "cola vacia"}
        ok = task.get("status") == "done"
        _log("run", "ok" if ok else "warn",
             f"task #{task.get('id')} -> {task.get('status')}")
        return {"ok": ok, "status": task.get("status"), "id": task.get("id")}
    finally:
        _runner_lock.release()


def do_retry(task_id: int) -> dict[str, Any]:
    """Reencola una tarea dead o waiting tras intervencion humana."""
    rows = {t["id"]: t for t in list_tasks(500)}
    t = rows.get(task_id)
    if not t:
        return {"ok": False, "error": "tarea no encontrada"}
    if t["status"] not in ("dead", "waiting"):
        return {"ok": False, "error": f"estado '{t['status']}' no reintentable"}
    update_task(
        task_id,
        status="pending",
        attempts=0,
        started_at="",
        finished_at="",
        result_code=None,
        note=t["note"] + " | reintentada",
        lease_owner="",
        lease_until="",
        error_kind="",
    )
    _log("retry", "ok", f"task #{task_id} reencolada")
    return {"ok": True}


def do_cancel(task_id: int) -> dict[str, Any]:
    """Cancela una tarea pending (marca fail)."""
    rows = {t["id"]: t for t in list_tasks(500)}
    t = rows.get(task_id)
    if not t:
        return {"ok": False, "error": "tarea no encontrada"}
    if t["status"] != "pending":
        return {"ok": False, "error": f"solo pending puede cancelarse (estado {t['status']})"}
    update_task(
        task_id,
        status="dead",
        finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        note=t["note"] + " | cancelada manualmente",
    )
    if t.get("sensitivity") == "sensitive":
        scrub_task_payload(task_id)
    _log("cancel", "ok", f"task #{task_id} cancelada manualmente")
    return {"ok": True}


def do_add_task(
    agent: str,
    prompt: str,
    model: str = "",
    note: str = "",
    model_policy: str = "paid",
    sensitivity: str = "normal",
) -> dict[str, Any]:
    """Encola tarea con agente de la lista permitida."""
    if agent not in ALLOWED_AGENTS:
        return {"ok": False, "error": f"agente '{agent}' no permitido"}
    if model not in ALLOWED_MODELS:
        return {"ok": False, "error": f"modelo '{model}' no permitido"}
    if not prompt or len(prompt) < 4:
        return {"ok": False, "error": "prompt demasiado corto"}
    try:
        tid = add_task(
            agent,
            prompt,
            note=note or "via panel",
            model=model,
            model_policy=model_policy,
            sensitivity=sensitivity,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    _log("add-task", "ok", f"task #{tid} agente={agent}")
    return {"ok": True, "id": tid}


def do_restart(identifier: str) -> dict[str, Any]:
    """Reinicia un timer systemd por nombre exacto (whitelist)."""
    if identifier not in RESTARTABLE_SYSTEMD:
        return {"ok": False, "error": f"{identifier} no reiniciable"}
    try:
        r = subprocess.run(
            ["systemctl", "--user", "restart", identifier],
            capture_output=True, text=True, timeout=10,
        )
        ok = r.returncode == 0
        _log("restart", "ok" if ok else "fail", f"{identifier} rc={r.returncode}")
        return {"ok": ok, "detail": (r.stderr or r.stdout).strip()[:200]}
    except Exception as exc:
        _log("restart", "fail", str(exc))
        return {"ok": False, "error": str(exc)}
