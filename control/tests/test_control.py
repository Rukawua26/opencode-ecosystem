"""Tests del plano de control (stdlib unittest)."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from control import collect, state
from control.model import Health, Snapshot, TimerInfo


class TestModelDefaults(unittest.TestCase):
    def test_health_default_ok_false(self) -> None:
        h = Health()
        self.assertFalse(h.ok)
        self.assertEqual(h.errors, [])
        self.assertEqual(h.warnings, [])

    def test_snapshot_roundtrip_via_load(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "snap.json"
            snap = Snapshot()
            snap.generated_at = "2026-09-18T00:00:00+00:00"
            snap.counts = {"skills": 10}
            snap.timers = [TimerInfo(name="opencode-x.timer", active=True)]
            snap.health = Health(ok=True, timers_active=1, timers_total=1)
            collect.write_snapshot_atomic(p, snap)
            loaded = collect.load_snapshot(p)
            assert loaded is not None
            self.assertEqual(loaded.counts["skills"], 10)
            self.assertEqual(loaded.timers[0].name, "opencode-x.timer")
            self.assertTrue(loaded.health.ok)

    def test_load_snapshot_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(collect.load_snapshot(Path(td) / "no.json"))


class TestTimerCrosscheck(unittest.TestCase):
    def test_declared_not_active_warns(self) -> None:
        w = collect.crosscheck_timers({"opencode-kairos.timer": "*/30 * * * *"}, [])
        self.assertTrue(any("no activo" in x for x in w))

    def test_active_not_declared_warns(self) -> None:
        t = TimerInfo(name="opencode-ram-guard.timer", active=True)
        w = collect.crosscheck_timers({}, [t])
        self.assertTrue(any("no declarado" in x for x in w))

    def test_declared_inactive_warns(self) -> None:
        t = TimerInfo(name="opencode-kairos.timer", active=False)
        w = collect.crosscheck_timers({"opencode-kairos.timer": ""}, [t])
        self.assertTrue(any("inactivo" in x for x in w))

    def test_match_no_warnings(self) -> None:
        t = TimerInfo(name="opencode-kairos.timer", active=True)
        self.assertEqual(collect.crosscheck_timers({"opencode-kairos.timer": ""}, [t]), [])


class TestStateStoreTTL(unittest.TestCase):
    def _store(self, snap: Snapshot) -> tuple[state.StateStore, mock.Mock]:
        st = state.StateStore(snapshot_path=Path(tempfile.mkdtemp()) / "s.json", ttl_seconds=30)
        collector = mock.Mock(return_value=snap)
        return st, collector

    def _fresh(self) -> Snapshot:
        s = Snapshot()
        s.generated_at = "t"
        return s

    def test_current_within_ttl_no_recollect(self) -> None:
        st, col = self._store(self._fresh())
        with mock.patch.object(state, "collect_snapshot", col):
            st.refresh(force=True)
            self.assertEqual(col.call_count, 1)
            st.current()
            st.current()
            self.assertEqual(col.call_count, 1)  # sin recolectar de nuevo

    def test_current_expired_recollects(self) -> None:
        st, col = self._store(self._fresh())
        st._ttl = 0.01  # noqa: SLF001 - test del contrato TTL
        with mock.patch.object(state, "collect_snapshot", col):
            st.refresh(force=True)
            time.sleep(0.05)
            st.current()
            self.assertEqual(col.call_count, 2)

    def test_force_refresh_always_recollects(self) -> None:
        st, col = self._store(self._fresh())
        with mock.patch.object(state, "collect_snapshot", col):
            st.refresh(force=True)
            st.refresh(force=True)
            self.assertEqual(col.call_count, 2)

    def test_collect_failure_returns_cached_with_warning(self) -> None:
        st, col = self._store(self._fresh())
        with mock.patch.object(state, "collect_snapshot", col):
            first = st.refresh(force=True)
        first_ts = first.generated_at
        col.side_effect = RuntimeError("boom")
        with mock.patch.object(state, "collect_snapshot", col):
            snap = st.refresh(force=True)
        self.assertTrue(any("recoleccion fallo" in w for w in snap.health.warnings))
        self.assertIs(snap, first)  # devuelve el snapshot cacheado
        self.assertEqual(snap.generated_at, first_ts)  # sin re-sellar fecha


if __name__ == "__main__":
    unittest.main()
