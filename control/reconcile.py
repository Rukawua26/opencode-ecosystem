"""Reconciliador: vigila inconsistencias entre estado declarado y observado.

Principios:
- Preview por defecto; `--apply` aplica las correcciones.
- No relanza trabajo automaticamente: eso lo decide el humano (run-next)
  o un timer separado. Marcar dead es seguro; ejecutar no.
- Cooldown entre acciones para no tumbar OpenCode en bucle.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import db
from .collect import _declared_timer_units  # reuso, mismo origen de verdad
from .model import Snapshot, TimerInfo
from .runner import TIMEOUT_S

# cooldown entre acciones del reconciliador (minimo 2 min entre applies)
_COOLDOWN_S = 120
# una tarea running que supere este tiempo se considera huerfana
_ORPHAN_AFTER_S = TIMEOUT_S + 300  # timeout + 5 min extra

_STATE_PATH = Path.home() / ".local/share/opencode-control/reconcile-state.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_state() -> dict:
    try:
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, indent=1), encoding="utf-8")


def check(tasks: list[dict] | None = None, timers: list[TimerInfo] | None = None,
          eco_root: Path | None = None) -> dict:
    """Detecta inconsistencias. No modifica nada."""
    findings: list[dict] = []
    now = datetime.now(timezone.utc)
    tasks = tasks if tasks is not None else db.list_tasks(500)
    timers = timers if timers is not None else []

    # 1) tareas huerfanas (lease vencido o running demasiado antiguo)
    for t in tasks:
        if t["status"] != "running":
            continue
        # preferir lease (definitivo); fallback: antigüedad de started_at
        lease_until = t.get("lease_until") or ""
        if lease_until:
            try:
                lease_dt = datetime.fromisoformat(lease_until)
                if lease_dt.tzinfo is None:
                    lease_dt = lease_dt.replace(tzinfo=timezone.utc)
                if now <= lease_dt:
                    continue  # lease vigente, no huerfana
                overdue = (now - lease_dt).total_seconds()
                findings.append({
                    "kind": "lease_vencido",
                    "target": f"task #{t['id']} ({t['agent']})",
                    "action": "marcar dead (lease expirado)",
                    "detail": f"lease vencio hace {int(overdue)}s",
                })
                continue
            except ValueError:
                pass
        # fallback sin lease
        started_raw = t.get("started_at")
        if not started_raw:
            continue
        try:
            started = datetime.fromisoformat(started_raw)
        except ValueError:
            continue
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        age = (now - started).total_seconds()
        if age > _ORPHAN_AFTER_S:
            findings.append({
                "kind": "task_huerfana",
                "target": f"task #{t['id']} ({t['agent']})",
                "action": "marcar dead",
                "detail": f"lleva {int(age)}s > lim {_ORPHAN_AFTER_S}s",
            })

    # 2) timers declarados pero inactivos/ausentes
    declared = _declared_timer_units(eco_root) if eco_root else {}
    observed = {t.name: t for t in timers}
    for unit in declared:
        t = observed.get(unit)
        if t is None:
            findings.append({
                "kind": "timer_ausente",
                "target": unit,
                "action": "notificar",
                "detail": "declarado en cron-jobs.json pero no existe en systemd",
            })
        elif not t.active:
            findings.append({
                "kind": "timer_inactivo",
                "target": unit,
                "action": "notificar (systemd--user start <unit> si se autoriza)",
                "detail": "declarado pero inactivo",
            })
    return {
        "ts": _now_iso(),
        "findings": findings,
        "ok": not findings,
        "tasks_checked": len(tasks),
        "timers_checked": len(declared),
    }


def apply_fixes(report: dict) -> dict:
    """Aplica solo lo seguro: marcar tareas huerfanas como dead."""
    state = _load_state()
    last = state.get("last_apply_ts", 0)
    now = time.time()
    elapsed = now - last
    applied: list[str] = []
    if elapsed < _COOLDOWN_S:
        report["apply"] = "skipped_cooldown"
        report["cooldown_remaining_s"] = int(_COOLDOWN_S - elapsed)
        return report
    for f in report.get("findings", []):
        if f["kind"] in ("task_huerfana", "lease_vencido"):
            try:
                tid = int(f["target"].split("#")[1].split(" ")[0].rstrip(")"))
            except (IndexError, ValueError):
                continue
            task_meta = next((t for t in db.list_tasks(500) if t["id"] == tid), None)
            db.update_task(tid, None, status="dead", lease_owner="",
                           lease_until="",
                           finished_at=_now_iso(),
                           note="reconciliador: " + f["kind"])
            if task_meta and task_meta.get("sensitivity") == "sensitive":
                db.scrub_task_payload(tid)
            db.record_event("reconciliador", "reconcile", "task dead",
                            "warn", f"task #{tid} {f['detail']}")
            applied.append(f["target"])
    if applied or report.get("findings"):
        state["last_apply_ts"] = now
        state["last_report"] = report
        _save_state(state)
    report["apply"] = "ok"
    report["applied"] = applied
    return report
