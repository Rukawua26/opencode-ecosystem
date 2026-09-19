"""Estado en memoria con refresco TTL y snapshot persistente."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .collect import (
    ECO_ROOT,
    SNAPSHOT_PATH,
    collect_snapshot,
    load_snapshot,
    write_snapshot_atomic,
)
from .db import record_event
from .model import Snapshot


def _diff_events(old: Snapshot | None, new: Snapshot) -> list[tuple[str, str, str, str, str]]:
    """Devuelve (kind, category, event, status, detail) de cambios reales."""
    evts: list[tuple[str, str, str, str, str]] = []
    if old is None:
        return evts
    # servicio opencode
    if old.health.open_code_active != new.health.open_code_active:
        evts.append((
            "opencode-service", "servicio",
            "cayó" if old.health.open_code_active else "recuperado",
            "error" if old.health.open_code_active else "ok",
            f"open_code_active {old.health.open_code_active} -> {new.health.open_code_active}",
        ))
    # timers
    old_t = {t.name: t for t in old.timers}
    for t in new.timers:
        o = old_t.get(t.name)
        if o is None:
            continue
        if o.active != t.active:
            evts.append((
                t.name, "timer",
                "parado" if o.active else "reanudado",
                "error" if o.active else "ok",
                f"active {o.active} -> {t.active}",
            ))
        elif o.result and t.result and o.result != t.result:
            evts.append((
                t.name, "timer", "resultado cambió",
                "error" if t.result != "success" else "ok",
                f"result {o.result} -> {t.result}",
            ))
    # componentes nuevos/eliminados
    old_c = {c.name for c in old.components}
    new_c = {c.name for c in new.components}
    for name in sorted(new_c - old_c):
        evts.append((name, "componente", "añadido", "ok", ""))
    for name in sorted(old_c - new_c):
        evts.append((name, "componente", "eliminado", "warn", ""))
    return evts


class StateStore:
    """Cache en memoria + persistencia atomica del snapshot.

    Reglas:
    - `current()` devuelve el snapshot si su edad < TTL; si expiro, recolecta.
    - `refresh(force=True)` siempre recolecta.
    - Si la recoleccion falla, devuelve lo ultimo conocido marcado como
      desactualizado (no miente: nunca presenta datos viejos como frescos).
    """

    def __init__(self, snapshot_path: Path | None = None, ttl_seconds: float = 15.0):
        self._path = snapshot_path or SNAPSHOT_PATH
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._cached: Snapshot | None = None
        self._cached_at: float = 0.0
        self._last_error: str = ""

    def _age(self) -> float:
        return time.monotonic() - self._cached_at

    def refresh(self, force: bool = False) -> Snapshot:
        with self._lock:
            fresh = (
                self._cached is not None
                and not force
                and self._age() < self._ttl
            )
            if fresh:
                return self._cached
        try:
            snap = collect_snapshot(ECO_ROOT)
        except Exception as exc:  # defensivo: un recolector roto no tumba el panel
            self._last_error = f"recoleccion fallo: {exc}"
            with self._lock:
                if self._cached is not None:
                    self._cached.health.warnings = [
                        w for w in self._cached.health.warnings
                        if not w.startswith("recoleccion fallo:")
                    ]
                    self._cached.health.warnings.append(self._last_error)
                    return self._cached
            snap = Snapshot()
            snap.health.warnings.append(self._last_error)
            snap.generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            return snap
        snap.generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            write_snapshot_atomic(self._path, snap)
        except OSError as exc:
            snap.health.warnings.append(f"no se pudo persistir snapshot: {exc}")
        self._last_error = ""
        with self._lock:
            prev = self._cached
            self._cached = snap
            self._cached_at = time.monotonic()
        for kind, category, event, status, detail in _diff_events(prev, snap):
            try:
                record_event(kind, category, event, status, detail)
            except Exception:
                pass  # el historial nunca rompe la recoleccion
        return snap

    def current(self) -> Snapshot:
        with self._lock:
            if self._cached is not None and self._age() < self._ttl and not self._last_error:
                return self._cached
        return self.refresh(force=False)

    def stale_seconds(self) -> float:
        """Edad en segundos del dato en cache (0 si no hay)."""
        with self._lock:
            if self._cached is None:
                return -1.0
            return round(self._age(), 1)

    @property
    def ttl(self) -> float:
        return self._ttl



_store: StateStore | None = None


def get_store() -> StateStore:
    global _store
    if _store is None:
        _store = StateStore()
    return _store
