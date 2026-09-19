"""Tests del lanzador con subprocess mockeado (jamás llama a opencode real)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control import db, runner


class RunnerFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "t.db"
        db.init_db(self.path)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _ok(self, agent: str, prompt: str, model: str = "", workspace: str = "") -> tuple[int, float, str, str]:
        return (0, 1.0, "", "")

    def _fail(self, agent: str, prompt: str, model: str = "", workspace: str = "") -> tuple[int, float, str, str]:
        return (1, 2.0, "boom", "agent")


class TestQueueOps(RunnerFixture):
    def test_add_and_list(self) -> None:
        tid = db.add_task("sdd-implement", "haz X", path=self.path)
        rows = db.list_tasks(path=self.path)
        self.assertEqual(rows[0]["id"], tid)
        self.assertEqual(rows[0]["status"], "pending")

    def test_add_requires_fields(self) -> None:
        with self.assertRaises(ValueError):
            db.add_task("", "prompt", path=self.path)

    def test_next_pending_fifo(self) -> None:
        db.add_task("a", "primero", path=self.path)
        db.add_task("a", "segundo", path=self.path)
        self.assertEqual(db.next_pending(self.path)["prompt"], "primero")


class TestRunner(RunnerFixture):
    def test_empty_queue_returns_none(self) -> None:
        self.assertIsNone(runner.run_next(self.path))

    def test_success_marks_done_and_receipt(self) -> None:
        db.add_task("qa-gate", "revisa", path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
            t = runner.run_next(self.path)
        self.assertEqual(t["status"], "done")
        rows = db.recent_events(10, path=self.path)
        self.assertTrue(any(r["category"] == "task" and r["event"] == "completada"
                            for r in rows))

    def test_success_implementer_chains_verifier(self) -> None:
        db.add_task("sdd-implement", "implementa", path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
            runner.run_next(self.path)
        pending = db.next_pending(self.path)
        self.assertIsNotNone(pending)
        self.assertEqual(pending["agent"], "sdd-verify")

    def test_failure_retries_then_dead(self) -> None:
        tid = db.add_task("qa-gate", "revisa", path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._fail):
            t1 = runner.run_next(self.path)   # intento 1 -> vuelve a pending
            t2 = runner.run_next(self.path)   # intento 2 -> dead
        self.assertEqual(t1["status"], "pending")
        self.assertEqual(t2["status"], "dead")
        row = [r for r in db.list_tasks(path=self.path) if r["id"] == tid][0]
        self.assertEqual(row["attempts"], 2)
        self.assertEqual(row["status"], "dead")

    def test_dead_tasks_not_picked(self) -> None:
        db.add_task("a", "p", path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._fail):
            runner.run_next(self.path)
            runner.run_next(self.path)
            self.assertIsNone(runner.run_next(self.path))  # ya no queda pending

    def test_timeout_causes_failure(self) -> None:
        db.add_task("a", "p", path=self.path)
        with mock.patch.object(runner, "_run_agent", return_value=(124, 900.0, "timeout", "timeout")):
            t = runner.run_next(self.path)
        self.assertEqual(t["status"], "pending")  # primer intento, reintenta

    def test_no_model_output_stored(self) -> None:
        db.add_task("a", "p", path=self.path)
        with mock.patch.object(runner, "_run_agent", return_value=(0, 1.0, "", "")):
            runner.run_next(self.path)
        for r in db.recent_events(50, path=self.path):
            self.assertLessEqual(len(r["detail"]), 300)

    def test_summary_counts(self) -> None:
        db.add_task("a", "1", path=self.path)
        db.add_task("b", "2", path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
            runner.run_next(self.path)
        s = runner.queue_summary(self.path)
        self.assertEqual(s["done"], 1)
        self.assertEqual(s["pending"], 1)

    def test_verifier_requires_deterministic_check(self) -> None:
        db.add_task(
            "sdd-verify", "verifica", verification_command="false", path=self.path
        )
        with mock.patch.object(runner, "_run_agent", return_value=(0, 0.1, "", "")):
            result = runner.run_next(self.path)
        self.assertEqual(result["status"], "pending")
        row = db.list_tasks(path=self.path)[0]
        self.assertEqual(row["error_kind"], "verification")

    def test_verifier_check_success_marks_done(self) -> None:
        db.add_task(
            "sdd-verify", "verifica", verification_command="true", path=self.path
        )
        with mock.patch.object(runner, "_run_agent", return_value=(0, 0.1, "", "")):
            result = runner.run_next(self.path)
        self.assertEqual(result["status"], "done")
        events = db.events_for("sdd-verify", path=self.path)
        self.assertTrue(any(e["category"] == "verification" for e in events))


if __name__ == "__main__":
    unittest.main()
