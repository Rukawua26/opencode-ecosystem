"""Grafo operativo del ecosistema: nodos agrupados y aristas declaradas.

Solo relaciones declaradas/observadas. Cada nodo es un grupo operativo
(8-12 max): el detalle fino sigue en la vista de componentes.
"""

from __future__ import annotations

from typing import Any

from .model import Snapshot

try:  # la cola nunca debe tumbar el grafo
    from .runner import queue_summary
except Exception:  # pragma: no cover
    queue_summary = None


def _queue_summary_safe() -> dict:
    if queue_summary is None:
        return {}
    try:
        return queue_summary() or {}
    except Exception:
        return {}

_SOURCE_DECL = "declarado"
_SOURCE_OBS = "observado"


def _node(nid: str, title: str, layer: str, status: str, detail: str,
          x: int, y: int, source: str = _SOURCE_OBS,
          evidence: str = "") -> dict[str, Any]:
    return {"id": nid, "title": title, "layer": layer, "status": status,
            "detail": detail, "x": x, "y": y, "source": source,
            "evidence": evidence}


# Mapeo nodo -> kind de eventos para el inspector (solo mapeos directos)
_NODE_EVENT_KIND = {
    "timers": "timer",
    "reconciliador": "reconciliador",
    "cola": "task",
    "runner": "task",
    "agentes": "task",
    "opencode": "servicio",
    "panel": "panel",
}


def _edge(src: str, dst: str, label: str, source: str = _SOURCE_DECL
          ) -> dict[str, str]:
    return {"from": src, "to": dst, "label": label, "source": source}


def build_graph(snap: Snapshot) -> dict[str, Any]:
    """Construye el grafo desde el snapshot actual (sin prompts ni datos privados)."""
    h = snap.health
    timers_ok = h.timers_active == h.timers_total
    cola = _queue_summary_safe()
    dead = int(cola.get("dead", 0) or 0)
    running = int(cola.get("running", 0) or 0)

    nodes = [
        _node("fuentes", "Configuración", "fuentes", "info",
              f"{snap.counts.get('skills', 0)} skills · configs", 90, 60,
              source=_SOURCE_OBS, evidence="skills/, configs/*.jsonc"),
        _node("timers", "Timers systemd", "automatizacion",
              "ok" if timers_ok else "err",
              f"{h.timers_active}/{h.timers_total} activos", 90, 190,
              source=_SOURCE_OBS, evidence="systemctl --user list-timers"),
        _node("reconciliador", "Reconciliador", "automatizacion",
              "ok", "marca dead lo atascado", 90, 320,
              source=_SOURCE_OBS, evidence="control/reconcile.py (timer 5min)"),
        _node("cola", "Cola de tareas", "datos",
              "warn" if dead > 0 else "info",
              f"pend={cola.get('pending', 0)} run={running} dead={dead}",
              380, 190, source=_SOURCE_OBS, evidence="control/db.py tasks"),
        _node("runner", "Runner", "ejecucion",
              "warn" if running else "ok", "1 tarea a la vez", 380, 320,
              source=_SOURCE_OBS, evidence="control/runner.py"),
        _node("agentes", "Agentes", "ejecucion", "info",
              f"{snap.counts.get('agentes', 0)} declarados", 620, 190,
              source=_SOURCE_OBS, evidence="configs/opencode.jsonc"),
        _node("skills", "Skills", "ejecucion", "info",
              f"{snap.counts.get('skills', 0)} instaladas", 620, 60,
              source=_SOURCE_OBS, evidence="skills/*/SKILL.md"),
        _node("opencode", "OpenCode", "servicio",
              "ok" if h.open_code_active else "err",
              "servicio " + ("activo" if h.open_code_active else "inactivo"),
              620, 320, source=_SOURCE_OBS, evidence="opencode service status"),
        _node("eventos", "Eventos SQLite", "datos", "info",
              "recibos y cambios", 380, 450,
              source=_SOURCE_OBS, evidence="~/.local/share/opencode-control/control.db"),
        _node("snapshot", "Snapshot JSON", "datos", "info",
              "estado canónico", 850, 60,
              source=_SOURCE_OBS, evidence="~/.local/share/opencode-control/snapshot.json"),
        _node("panel", "Panel web", "observabilidad",
              "ok" if h.ok else "warn", "127.0.0.1:8765", 850, 320,
              source=_SOURCE_OBS, evidence="control/server.py"),
    ]
    edges = [
        _edge("fuentes", "snapshot", "escanea", _SOURCE_OBS),
        _edge("timers", "reconciliador", "revisa", _SOURCE_OBS),
        _edge("reconciliador", "cola", "marca dead", _SOURCE_OBS),
        _edge("reconciliador", "eventos", "notifica", _SOURCE_OBS),
        _edge("cola", "runner", "consume"),
        _edge("runner", "agentes", "delega"),
        _edge("runner", "eventos", "recibos", _SOURCE_OBS),
        _edge("agentes", "opencode", "usa"),
        _edge("skills", "agentes", "aporta"),
        _edge("timers", "eventos", "resultados", _SOURCE_OBS),
        _edge("snapshot", "panel", "lee", _SOURCE_OBS),
        _edge("eventos", "panel", "muestra", _SOURCE_OBS),
    ]
    return {"nodes": nodes, "edges": edges,
            "node_count": len(nodes), "edge_count": len(edges),
            "node_event_kinds": _NODE_EVENT_KIND}
