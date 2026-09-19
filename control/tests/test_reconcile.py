"""Tests del reconciliador."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from control import db, reconcile
from control.model import TimerInfo


def _task(tid: int, status: str, started: str | None = None) -> dict:
    return {"id": tid, "agent": "a", "prompt": "p", "status": status,
            "attempts": 1, "created_at": "x", "started_at": started,
            "finished_at": None, "result_code": None, "note": "", "model": ""}


class TestCheck(unittest.TestCase):
    def test_healthy_no_findings(self) -> None:
        r = reconcile.check(tasks=[], timers=[], eco_root=None)
        self.assertTrue(r["ok"])

    def test_orphan_running_detected(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(seconds=3600)).isoformat(timespec="seconds")
        r = reconcile.check(tasks=[_task(1, "running", old)], timers=[], eco_root=None)
        self.assertFalse(r["ok"])
        self.assertEqual(r["findings"][0]["kind"], "task_huerfana")

    def test_fresh_running_not_flagged(self) -> None:
        recent = datetime.now(timezone.utc).isoformat(timespec="seconds")
        r = reconcile.check(tasks=[_task(1, "running", recent)], timers=[], eco_root=None)
        self.assertTrue(r["ok"])

    def test_expired_lease_detected(self) -> None:
        task = _task(1, "running", datetime.now(timezone.utc).isoformat())
        task["lease_until"] = (
            datetime.now(timezone.utc) - timedelta(seconds=30)
        ).isoformat(timespec="seconds")
        r = reconcile.check(tasks=[task], timers=[], eco_root=None)
        self.assertEqual(r["findings"][0]["kind"], "lease_vencido")

    def test_live_lease_not_flagged(self) -> None:
        task = _task(1, "running", datetime.now(timezone.utc).isoformat())
        task["lease_until"] = (
            datetime.now(timezone.utc) + timedelta(seconds=30)
        ).isoformat(timespec="seconds")
        r = reconcile.check(tasks=[task], timers=[], eco_root=None)
        self.assertTrue(r["ok"])

    def test_orphan_naive_ts_assumed_utc(self) -> None:
        naive = (datetime.now(timezone.utc) - timedelta(seconds=3600)).replace(tzinfo=None).isoformat(timespec="seconds")
        r = reconcile.check(tasks=[_task(1, "running", naive)], timers=[], eco_root=None)
        self.assertFalse(r["ok"])

    def test_timer_declared_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "configs"
            cfg.mkdir()
            (cfg / "cron-jobs.json").write_text(
                '{"jobs":[{"name":"inex","schedule":"* * * * *","command":"x"}]}')
            r = reconcile.check(tasks=[], timers=[], eco_root=Path(td))
        self.assertFalse(r["ok"])
        self.assertEqual(r["findings"][0]["kind"], "timer_ausente")

    def test_timer_declared_inactive(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "configs"
            cfg.mkdir()
            (cfg / "cron-jobs.json").write_text(
                '{"jobs":[{"name":"ram-guard","schedule":"* * * * *","command":"x"}]}')
            t = TimerInfo(name="opencode-ram-guard.timer", active=False)
            r = reconcile.check(tasks=[], timers=[t], eco_root=Path(td))
        self.assertEqual(r["findings"][0]["kind"], "timer_inactivo")


class TestApply(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.dbpath = Path(self.td.name) / "t.db"
        self.statepath = Path(self.td.name) / "rstate.json"
        mock.patch.object(db, "DB_PATH", self.dbpath).start()
        mock.patch.object(reconcile, "_STATE_PATH", self.statepath).start()
        self.addCleanup(mock.patch.stopall)
        db.init_db()

    def test_apply_marks_dead_and_records_event(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(seconds=3600)).isoformat(timespec="seconds")
        tid = db.add_task("a", "p")
        db.update_task(tid, status="running", attempts=1, started_at=old)
        r = reconcile.check(tasks=db.list_tasks(), timers=[], eco_root=None)
        out = reconcile.apply_fixes(r)
        self.assertEqual(out["apply"], "ok")
        row = [t for t in db.list_tasks() if t["id"] == tid][0]
        self.assertEqual(row["status"], "dead")
        events = db.events_for("reconciliador")
        self.assertTrue(events)

    def test_apply_cooldown_blocks_second_apply(self) -> None:
        self.statepath.write_text(json.dumps({"last_apply_ts": time.time()}))
        old = (datetime.now(timezone.utc) - timedelta(seconds=3600)).isoformat(timespec="seconds")
        r = reconcile.check(tasks=[_task(1, "running", old)], timers=[], eco_root=None)
        out = reconcile.apply_fixes(r)
        self.assertEqual(out["apply"], "skipped_cooldown")
        self.assertIn("cooldown_remaining_s", out)

    def test_apply_without_findings_does_not_touch_state(self) -> None:
        out = reconcile.apply_fixes(reconcile.check(tasks=[], timers=[], eco_root=None))
        self.assertEqual(out["apply"], "ok")
        self.assertFalse(self.statepath.exists())


if __name__ == "__main__":
    unittest.main()
