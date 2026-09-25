"""Traza por tarea: fase actual, tiempo y punto de detencion.

Solo datos ya sanitizados: nunca prompt, workspace, stdout ni respuestas.
Reutiliza db.get_task / latest_child_task / events_for_task.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import db

_VERIFY_AGENT = "odd-verifier"
_PHASE_VERIFY = "fase: verificacion determinista"

_STOP_REASONS = {
    "timeout": "timeout del agente (15 min)",
    "provider_balance": "saldo insuficiente del proveedor",
    "provider_rate": "rate limit del proveedor",
    "infra": "infraestructura: opencode no disponible",
    "contract": "contrato de salida invalido",
    "verification": "verificacion determinista fallo",
    "review": "revision requiere decision humana",
}

_STATUS_PHASE = {
    "pending": "en cola",
    "done": "completada",
    "dead": "detenida",
    "failed": "fallida",
}


def _elapsed_s(task: dict) -> float | None:
    """Segundos desde inicio (hasta finished_at o ahora). None si no arranco."""
    started_raw = task.get("started_at")
    if not started_raw:
        return None
    try:
        started = datetime.fromisoformat(started_raw)
    except ValueError:
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    end_raw = task.get("finished_at")
    try:
        end = datetime.fromisoformat(end_raw) if end_raw else datetime.now(timezone.utc)
    except ValueError:
        end = datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return max(0.0, round((end - started).total_seconds(), 2))


def stop_reason(task: dict) -> str:
    """Traduccion humana del punto de detencion (sin detalles tecnicos crudos)."""
    kind = str(task.get("error_kind") or "")
    if kind in _STOP_REASONS:
        return _STOP_REASONS[kind]
    note = str(task.get("note") or "")
    if task.get("status") == "dead":
        if note.startswith("reconciliador:"):
            return "proceso huerfano, lease vencido (marcado por reconciliador)"
        return ("fallo del agente: " + note[:100]) if note else "detenida sin diagnostico"
    if task.get("status") == "waiting":
        return note[:100] if note else "esperando decision humana"
    return ""


def compute_phase(task: dict, events: list[dict]) -> str:
    """Fase actual: ultimo checkpoint de la tarea o fase generica del estado."""
    status = str(task.get("status") or "")
    if status == "running":
        for e in events:  # vienen DESC (mas reciente primero)
            if e["event"] == _PHASE_VERIFY:
                return "verificacion determinista"
        return "ejecutando agente"
    if status == "waiting":
        if task.get("error_kind") == "review":
            return "revision fallida: esperando decision"
        if str(task.get("note") or "") == "transicion no registrada":
            return "transicion no registrada: esperando control-plane"
        return "bloqueada: esperando decision humana"
    return _STATUS_PHASE.get(status, status or "desconocida")


def build_trace(task_id: int, path: Path | None = None) -> dict | None:
    """Traza sanitizada de una tarea: fase, tiempos, motivo y cadena verifier."""
    task = db.get_task(task_id, path)
    if task is None:
        return None
    events = db.events_for_task(task_id, path=path)
    child = db.latest_child_task(task_id, _VERIFY_AGENT, path)
    verifier = None
    if child is not None:
        verifier = {
            "id": child["id"],
            "status": child["status"],
            "note": child.get("note", ""),
            "error_kind": child.get("error_kind", ""),
            "started_at": child.get("started_at"),
            "finished_at": child.get("finished_at"),
        }
    return {
        "id": task["id"],
        "agent": task["agent"],
        "status": task["status"],
        "attempts": task["attempts"],
        "model": task.get("model", ""),
        "workflow": task.get("workflow", ""),
        "feature": task.get("feature", ""),
        "parent_id": task.get("parent_id"),
        "started_at": task.get("started_at"),
        "finished_at": task.get("finished_at"),
        "lease_until": task.get("lease_until") if task["status"] == "running" else "",
        "result_code": task.get("result_code"),
        "error_kind": task.get("error_kind", ""),
        "note": (task.get("note") or "")[:200],
        "phase": compute_phase(task, events),
        "stop_reason": stop_reason(task),
        "elapsed_s": _elapsed_s(task),
        "timeline": [
            {"ts": e["ts"], "event": e["event"], "status": e["status"],
             "detail": e["detail"], "duration_s": e.get("duration_s")}
            for e in events
        ],
        "verifier": verifier,
    }
