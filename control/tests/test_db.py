"""Tests de db.py (SQLite) y deteccion de cambios."""

from __future__ import annotations

import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from control import db, state
from control.model import Component, Health, Snapshot, TimerInfo


class TestDb(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "t.db"
        db.init_db(self.path)

    def tearDown(self) -> None:
        self.td.cleanup()

    def test_record_and_read(self) -> None:
        db.record_event("kairos", "timer", "reanudado", "ok", "test", path=self.path)
        rows = db.recent_events(10, path=self.path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "kairos")
        self.assertEqual(rows[0]["status"], "ok")

    def test_receipt(self) -> None:
        db.record_receipt("sdd-implement", "ok", 12.5, "tarea T3", path=self.path)
        rows = db.events_for("sdd-implement", path=self.path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["category"], "receipt")
        self.assertAlmostEqual(rows[0]["duration_s"], 12.5)

    def test_detail_truncated(self) -> None:
        db.record_event("x", "timer", "e", "ok", "y" * 500, path=self.path)
        rows = db.recent_events(1, path=self.path)
        self.assertLessEqual(len(rows[0]["detail"]), 300)

    def test_events_for_filters_kind(self) -> None:
        db.record_event("a", "timer", "e1", path=self.path)
        db.record_event("b", "timer", "e2", path=self.path)
        self.assertEqual(len(db.events_for("a", path=self.path)), 1)

    def test_retention_by_days(self) -> None:
        old_ts = "2020-01-01T00:00:00+00:00"
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO events (ts,kind,category,event) VALUES (?,?,?,?)",
                (old_ts, "viejo", "timer", "x"),
            )
        db.record_event("nuevo", "timer", "e", path=self.path)
        kinds = [r["kind"] for r in db.recent_events(10, path=self.path)]
        self.assertNotIn("viejo", kinds)
        self.assertIn("nuevo", kinds)


def _snap(timers: list[TimerInfo], oc: bool, comps: list[str]) -> Snapshot:
    s = Snapshot()
    s.timers = timers
    s.health = Health(ok=True, open_code_active=oc)
    s.components = [Component(kind="skill", name=n) for n in comps]
    return s


class TestDiffEvents(unittest.TestCase):
    def test_no_previous_no_events(self) -> None:
        self.assertEqual(state._diff_events(None, _snap([], True, ["a"])), [])

    def test_no_changes_no_events(self) -> None:
        from dataclasses import replace
        t = TimerInfo(name="opencode-kairos.timer", active=True, result="success")
        a, b = _snap([t], True, ["a"]), _snap([replace(t)], True, ["a"])
        self.assertEqual(state._diff_events(a, b), [])

    def test_timer_stop_detected(self) -> None:
        a = _snap([TimerInfo(name="opencode-kairos.timer", active=True)], True, [])
        b = _snap([TimerInfo(name="opencode-kairos.timer", active=False)], True, [])
        evts = state._diff_events(a, b)
        self.assertEqual(len(evts), 1)
        self.assertEqual(evts[0][2], "parado")
        self.assertEqual(evts[0][3], "error")

    def test_timer_result_failure_detected(self) -> None:
        a = _snap([TimerInfo(name="t.timer", active=True, result="success")], True, [])
        b = _snap([TimerInfo(name="t.timer", active=True, result="failed")], True, [])
        evts = state._diff_events(a, b)
        self.assertEqual(len(evts), 1)
        self.assertEqual(evts[0][3], "error")

    def test_service_down_detected(self) -> None:
        a, b = _snap([], True, []), _snap([], False, [])
        evts = state._diff_events(a, b)
        self.assertEqual(evts[0][2], "cayó")

    def test_component_added_removed(self) -> None:
        a, b = _snap([], True, ["a", "b"]), _snap([], True, ["b", "c"])
        evts = state._diff_events(a, b)
        kinds = {(e[0], e[2]) for e in evts}
        self.assertIn(("c", "añadido"), kinds)
        self.assertIn(("a", "eliminado"), kinds)

    def test_refresh_records_events(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            st = state.StateStore(snapshot_path=Path(td) / "s.json", ttl_seconds=999)
            t_on = [TimerInfo(name="opencode-k.timer", active=True, result="success")]
            t_off = [TimerInfo(name="opencode-k.timer", active=False, result="success")]
            with mock.patch.object(state, "collect_snapshot",
                                   side_effect=[_snap(t_on, True, []), _snap(t_off, True, [])]):
                with mock.patch.object(state, "record_event") as rec:
                    st.refresh(force=True)
                    st.refresh(force=True)
            self.assertTrue(rec.called)
            self.assertEqual(rec.call_args[0][2], "parado")


if __name__ == "__main__":
    unittest.main()
