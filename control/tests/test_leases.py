"""Contrato v2, politica de modelos y lease atomico."""

from __future__ import annotations

import multiprocessing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control import db, runner


def _claim_worker(path: str, owner: str, queue: multiprocessing.Queue) -> None:
    task = db.claim_next(owner, 60, Path(path))
    queue.put(task["id"] if task else None)


class LeaseFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.path = Path(self.td.name) / "lease.db"
        db.init_db(self.path)


class TestContractV2(LeaseFixture):
    def test_schema_version_and_columns(self) -> None:
        with sqlite3.connect(self.path) as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(tasks)")}
            version = conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()[0]
        self.assertEqual(version, "2")
        self.assertTrue({"workflow", "workspace", "feature", "lease_owner",
                         "lease_until", "error_kind"} <= cols)

    def test_public_list_redacts_sensitive_contract(self) -> None:
        db.add_task(
            "build", "prompt secreto", workspace=str(Path.home()),
            verification_command="comando secreto", path=self.path,
        )
        row = db.list_tasks(path=self.path)[0]
        self.assertNotIn("prompt", row)
        self.assertNotIn("workspace", row)
        self.assertNotIn("verification_command", row)

    def test_contract_roundtrip(self) -> None:
        tid = db.add_task(
            "odd-worker", "tarea", model="openai/gpt-5.6-luna",
            workflow="odd", workspace=str(Path.home()), feature="001-x",
            expected_outputs="x.txt", verification_command="test -f x.txt",
            model_policy="paid", sensitivity="normal", path=self.path,
        )
        row = next(
            t for t in db.list_tasks(path=self.path, include_private=True)
            if t["id"] == tid
        )
        self.assertEqual(row["workflow"], "odd")
        self.assertEqual(row["expected_outputs"], "x.txt")

    def test_free_model_requires_explicit_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "free-allowed"):
            db.add_task("build", "tarea", model="provider/model-free", path=self.path)

    def test_sensitive_never_uses_free(self) -> None:
        with self.assertRaisesRegex(ValueError, "sensitive"):
            db.add_task(
                "build", "tarea", model="provider/model-free",
                model_policy="free-allowed", sensitivity="sensitive", path=self.path,
            )

    def test_old_terminal_payload_is_purged(self) -> None:
        tid = db.add_task("build", "payload viejo", path=self.path)
        db.update_task(
            tid, self.path, status="done", finished_at="2020-01-01T00:00:00+00:00"
        )
        db.init_db(self.path)
        row = db.list_tasks(path=self.path, include_private=True)[0]
        self.assertEqual(row["prompt"], "[purged]")


class TestAtomicClaim(LeaseFixture):
    def test_claim_sets_owner_lease_and_attempt(self) -> None:
        tid = db.add_task("build", "tarea", path=self.path)
        task = db.claim_next("worker-a", 60, self.path)
        self.assertEqual(task["id"], tid)
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["attempts"], 1)
        self.assertEqual(task["lease_owner"], "worker-a")
        self.assertTrue(task["lease_until"])

    def test_two_processes_only_one_claims(self) -> None:
        db.add_task("build", "tarea", path=self.path)
        queue: multiprocessing.Queue = multiprocessing.Queue()
        workers = [
            multiprocessing.Process(
                target=_claim_worker, args=(str(self.path), f"p{i}", queue)
            )
            for i in range(2)
        ]
        for process in workers:
            process.start()
        for process in workers:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        results = [queue.get(timeout=2), queue.get(timeout=2)]
        self.assertEqual(sum(result is not None for result in results), 1)


class TestRunnerPolicy(LeaseFixture):
    def test_provider_error_does_not_consume_attempt(self) -> None:
        tid = db.add_task("build", "tarea", path=self.path)
        with mock.patch.object(
            runner, "_run_agent", return_value={
                "code": 1, "duration": 0.1, "note": "",
                "error_kind": "provider_balance", "result": "",
                "summary": "", "question": "",
            }
        ):
            result = runner.run_next(self.path)
        row = next(t for t in db.list_tasks(path=self.path) if t["id"] == tid)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(row["attempts"], 0)
        self.assertEqual(row["error_kind"], "provider_balance")
        self.assertEqual(row["lease_owner"], "")

    def test_verifier_inherits_contract(self) -> None:
        tid = db.add_task(
            "odd-worker", "crea x", model="openai/gpt-5.6-luna",
            workflow="odd", workspace=str(Path.home()), feature="001-x",
            expected_outputs="x.txt", verification_command="test -f x.txt",
            path=self.path,
        )
        with mock.patch.object(runner, "_run_agent", return_value={
            "code": 0, "duration": 0.1, "note": "", "error_kind": "",
            "result": "success", "summary": "", "question": "",
        }):
            runner.run_next(self.path)
        verifier = db.next_pending(self.path)
        self.assertEqual(verifier["agent"], "odd-verifier")
        self.assertEqual(verifier["parent_id"], tid)
        self.assertEqual(verifier["model"], "openai/gpt-5.6-luna")
        self.assertEqual(verifier["workspace"], str(Path.home()))
        self.assertIn("Tarea original: crea x", verifier["prompt"])

    def test_sensitive_terminal_task_is_scrubbed(self) -> None:
        tid = db.add_task(
            "build", "dato sensible", sensitivity="sensitive", path=self.path
        )
        with mock.patch.object(runner, "_run_agent", return_value={
            "code": 0, "duration": 0.1, "note": "", "error_kind": "",
            "result": "success", "summary": "", "question": "",
        }):
            runner.run_next(self.path)
        row = next(
            t for t in db.list_tasks(path=self.path, include_private=True)
            if t["id"] == tid
        )
        self.assertEqual(row["prompt"], "[purged]")
