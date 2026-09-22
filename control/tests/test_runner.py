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

    def _ok(self, agent: str, prompt: str, model: str = "", workspace: str = "") -> dict[str, object]:
        return {"code": 0, "duration": 1.0, "note": "", "error_kind": "",
                "result": "success", "summary": "ok", "question": "",
                "next_transition": ""}

    def _fail(self, agent: str, prompt: str, model: str = "", workspace: str = "") -> dict[str, object]:
        return {"code": 1, "duration": 2.0, "note": "boom", "error_kind": "agent",
                "result": "", "summary": "", "question": "", "next_transition": ""}


class TestQueueOps(RunnerFixture):
    def test_add_and_list(self) -> None:
        tid = db.add_task("odd-worker", "haz X", path=self.path)
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
        db.add_task("odd-worker", "implementa", workflow="odd", feature="demo", path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
            runner.run_next(self.path)
        pending = db.next_pending(self.path)
        self.assertIsNotNone(pending)
        self.assertEqual(pending["agent"], "odd-verifier")
        self.assertEqual(pending["workflow"], "odd")

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
        with mock.patch.object(runner, "_run_agent", return_value={
            "code": 124, "duration": 900.0, "note": "timeout", "error_kind": "timeout",
            "result": "", "summary": "", "question": "",
        }):
            t = runner.run_next(self.path)
        self.assertEqual(t["status"], "pending")  # primer intento, reintenta

    def test_no_model_output_stored(self) -> None:
        db.add_task("a", "p", path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
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
            "odd-verifier", "verifica", verification_command="false", path=self.path
        )
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
            result = runner.run_next(self.path)
        self.assertEqual(result["status"], "pending")
        row = db.list_tasks(path=self.path)[0]
        self.assertEqual(row["error_kind"], "verification")

    def test_verifier_check_success_marks_done(self) -> None:
        db.add_task(
            "odd-verifier", "verifica", verification_command="true", path=self.path
        )
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
            result = runner.run_next(self.path)
        self.assertEqual(result["status"], "done")
        events = db.events_for("odd-verifier", path=self.path)
        self.assertTrue(any(e["category"] == "verification" for e in events))

    def test_blocked_without_question_is_contract_error(self) -> None:
        tid = db.add_task("odd-worker", "decide", path=self.path)
        blocked = {"code": 0, "duration": 0.2, "note": "", "error_kind": "",
                   "result": "blocked", "summary": "", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=blocked):
            result = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(row["error_kind"], "contract")
        self.assertIn("QUESTION", row["note"])

    def test_blocked_waits_without_consuming_attempt(self) -> None:
        tid = db.add_task("odd-worker", "decide", path=self.path)
        blocked = {"code": 0, "duration": 0.2, "note": "", "error_kind": "",
                   "result": "blocked", "summary": "falta criterio",
                   "question": "A o B?"}
        with mock.patch.object(runner, "_run_agent", return_value=blocked):
            result = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(result["status"], "waiting")
        self.assertEqual(row["attempts"], 0)
        self.assertEqual(row["note"], "A o B?")

    def test_declared_failure_uses_normal_retry(self) -> None:
        tid = db.add_task("odd-worker", "haz X", path=self.path)
        failed = {"code": 0, "duration": 0.2, "note": "", "error_kind": "",
                  "result": "failed", "summary": "test rojo", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=failed):
            result = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(row["error_kind"], "agent")
        self.assertEqual(row["note"], "test rojo")

    def test_verifier_declared_failure_waits_without_consuming_attempt(self) -> None:
        tid = db.add_task("odd-verifier", "verifica", path=self.path)
        long_summary = "criterio no cumplido: " + "x" * 250
        failed = {"code": 0, "duration": 0.2, "note": "", "error_kind": "",
                  "result": "failed", "summary": long_summary, "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=failed):
            result = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(result["status"], "waiting")
        self.assertEqual(row["status"], "waiting")
        self.assertEqual(row["attempts"], 0)  # intento restaurado
        self.assertEqual(row["error_kind"], "review")
        self.assertEqual(row["note"], long_summary[:200])  # nota acotada, sin stdout
        events = db.events_for("odd-verifier", path=self.path)
        self.assertTrue(any(e["category"] == "review" and e["status"] == "warn"
                            for e in events))
        self.assertEqual(  # sin receipt de exito
            [r for r in events if r["category"] == "receipt"], [])

    def test_verifier_failed_with_transition_review_wins(self) -> None:
        tid = db.add_task("odd-verifier", "verifica", path=self.path)
        outcome = {"code": 0, "duration": 0.1, "note": "", "error_kind": "",
                   "result": "failed", "summary": "revision en rojo", "question": "",
                   "next_transition": "printf secreto-modelo"}
        with mock.patch.object(runner, "_run_agent", return_value=outcome), \
                mock.patch.object(runner.subprocess, "run") as run:
            task = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(task["status"], "waiting")
        self.assertEqual(row["attempts"], 0)
        self.assertEqual(row["error_kind"], "review")
        self.assertEqual(row["note"], "revision en rojo")
        self.assertFalse(any(  # la revision fallida gana: sin evento de transicion
            e["category"] == "transition"
            for e in db.events_for("odd-verifier", path=self.path)
        ))
        run.assert_not_called()

    def test_manual_retry_resumes_review_waiting(self) -> None:
        from control import actions
        tid = db.add_task("odd-verifier", "verifica", path=self.path)
        failed = {"code": 0, "duration": 0.2, "note": "", "error_kind": "",
                  "result": "failed", "summary": "criterio no cumplido", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=failed):
            runner.run_next(self.path)
        with mock.patch.object(actions, "record_event", lambda *a, **k: None), \
                mock.patch.object(actions, "list_tasks",
                                  lambda n=500: db.list_tasks(n, path=self.path)), \
                mock.patch.object(actions, "update_task",
                                  lambda t, **f: db.update_task(t, self.path, **f)):
            self.assertTrue(actions.do_retry(tid)["ok"])
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["error_kind"], "")

    def test_odd_agent_without_result_fails_contract(self) -> None:
        tid = db.add_task("odd-worker", "haz X", path=self.path)
        missing = {"code": 0, "duration": 0.1, "note": "", "error_kind": "",
                   "result": "", "summary": "", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=missing):
            result = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(row["error_kind"], "contract")
        self.assertIn("RESULT", row["note"])

    def test_missing_summary_is_fail_closed(self) -> None:
        tid = db.add_task("odd-worker", "haz X", path=self.path)
        incomplete = {"code": 0, "duration": 0.1, "note": "", "error_kind": "",
                      "result": "success", "summary": "", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=incomplete):
            result = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(row["error_kind"], "contract")
        self.assertIn("SUMMARY", row["note"])

    def test_require_summary_only_for_odd_agents(self) -> None:
        db.add_task("qa-gate", "revisa", path=self.path)
        no_summary = {"code": 0, "duration": 0.1, "note": "", "error_kind": "",
                      "result": "success", "summary": "", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=no_summary):
            result = runner.run_next(self.path)
        self.assertEqual(result["status"], "done")

    def test_done_worker_records_exact_receipt(self) -> None:
        tid = db.add_task("odd-worker", "haz X", path=self.path)
        complete = {"code": 0, "duration": 1.2, "note": "", "error_kind": "",
                    "result": "success", "summary": "implementado T1", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=complete):
            runner.run_next(self.path)
        receipts = [
            r for r in db.events_for("odd-worker", path=self.path)
            if r["category"] == "receipt"
        ]
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["status"], "success")
        self.assertIn(f"task #{tid}", receipts[0]["detail"])
        self.assertIn("verifier pending", receipts[0]["detail"])

    def test_worker_success_always_chains_verifier(self) -> None:
        tid = db.add_task("odd-worker", "haz X", workflow="odd", path=self.path)
        complete = {"code": 0, "duration": 0.8, "note": "", "error_kind": "",
                    "result": "success", "summary": "ok", "question": ""}
        with mock.patch.object(runner, "_run_agent", return_value=complete):
            runner.run_next(self.path)
        pending = db.next_pending(self.path)
        self.assertIsNotNone(pending)
        self.assertEqual(pending["agent"], "odd-verifier")
        self.assertEqual(pending["parent_id"], tid)

    def test_model_next_transition_never_reaches_shell(self) -> None:
        tid = db.add_task("odd-worker", "revisa", path=self.path)
        outcome = {"code": 0, "duration": 0.1, "note": "", "error_kind": "",
                   "result": "success", "summary": "hecho", "question": "",
                   "next_transition": "printf secreto-modelo"}
        with mock.patch.object(runner, "_run_agent", return_value=outcome), \
                mock.patch.object(runner.subprocess, "run") as run:
            task = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(task["status"], "waiting")
        self.assertEqual(row["attempts"], 0)
        self.assertEqual(row["note"], "transicion no registrada")
        self.assertFalse(any(
            "secreto-modelo" in e["detail"]
            for e in db.events_for("odd-worker", path=self.path)
        ))
        run.assert_not_called()

    def test_incomplete_odd_output_with_transition_fails_contract(self) -> None:
        tid = db.add_task("odd-worker", "revisa", path=self.path)
        outcome = {"code": 0, "duration": 0.1, "note": "", "error_kind": "",
                   "result": "", "summary": "", "question": "",
                   "next_transition": "comando-secreto --token abc"}
        with mock.patch.object(runner, "_run_agent", return_value=outcome):
            task = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(task["status"], "pending")
        self.assertEqual(row["attempts"], 1)
        self.assertEqual(row["error_kind"], "contract")
        self.assertIn("RESULT", row["note"])
        self.assertNotIn("comando-secreto", row["note"])
        events = db.events_for("odd-worker", path=self.path)
        self.assertFalse(any("comando-secreto" in e["detail"] for e in events))

    def test_generic_agent_ignores_model_transition_without_shell(self) -> None:
        db.add_task("qa-gate", "revisa", path=self.path)
        outcome = {"code": 0, "duration": 0.1, "note": "", "error_kind": "",
                   "result": "success", "summary": "hecho", "question": "",
                   "next_transition": "printf secreto-modelo"}
        with mock.patch.object(runner, "_run_agent", return_value=outcome), \
                mock.patch.object(runner.subprocess, "run") as run:
            task = runner.run_next(self.path)
        self.assertEqual(task["status"], "done")
        run.assert_not_called()

    def test_opencode_missing_fails_explicit_as_infra(self) -> None:
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            outcome = runner._run_agent("odd-worker", "haz X")
        self.assertEqual(outcome["error_kind"], "infra")
        self.assertIn("opencode no encontrado", outcome["note"])

    def test_result_parser_keeps_last_bounded_value(self) -> None:
        parsed = runner._parse_result_lines(
            "SUMMARY: viejo\nQUESTION: " + "x" * 220 + "\nSUMMARY: nuevo\nRESULT: BLOCKED"
        )
        self.assertEqual(parsed["result"], "BLOCKED")
        self.assertEqual(parsed["summary"], "nuevo")
        self.assertEqual(len(parsed["question"]), 200)


if __name__ == "__main__":
    unittest.main()
