"""Tests de acciones manuales (CSRF, whitelist, reintentos)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control import actions, db, runner


class ActionsFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.td.name) / "t.db"
        db.init_db(self.dbpath)
        # redirigir el acceso a datos de actions hacia la DB temporal
        self.patches = [
            mock.patch.object(actions, "record_event", lambda *a, **k: None),
            mock.patch.object(actions, "add_task",
                              lambda *a, **k: db.add_task(*a, path=self.dbpath, **k)),
            mock.patch.object(actions, "list_tasks",
                              lambda n=500: db.list_tasks(n, path=self.dbpath)),
            mock.patch.object(actions, "update_task",
                              lambda tid, **f: db.update_task(tid, self.dbpath, **f)),
            mock.patch.object(actions, "scrub_task_payload",
                              lambda tid: db.scrub_task_payload(tid, self.dbpath)),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self.td.cleanup()


class TestToken(unittest.TestCase):
    def test_token_exists_and_stable(self) -> None:
        t1 = actions.token()
        self.assertGreater(len(t1), 16)
        self.assertEqual(t1, actions.token())


class TestAddTask(ActionsFixture):
    def test_rejects_unknown_agent(self) -> None:
        r = actions.do_add_task("rm-rf", "haz algo")
        self.assertFalse(r["ok"])
        self.assertIn("no permitido", r["error"])

    def test_rejects_empty_prompt(self) -> None:
        r = actions.do_add_task("qa-gate", "xy")
        self.assertFalse(r["ok"])

    def test_accepts_allowed_agent(self) -> None:
        model = "openai/gpt-5.6-luna"
        r = actions.do_add_task("qa-gate", "revisa el staged diff", model=model)
        self.assertTrue(r["ok"])
        self.assertIn("id", r)
        row = db.list_tasks(path=self.dbpath)[0]
        self.assertEqual(row["agent"], "qa-gate")
        self.assertEqual(row["model"], model)

    def test_rejects_unknown_model(self) -> None:
        r = actions.do_add_task("qa-gate", "revisa esto", model="evil/model")
        self.assertFalse(r["ok"])
        self.assertIn("no permitido", r["error"])

    def test_rejects_sensitive_free(self) -> None:
        r = actions.do_add_task(
            "qa-gate", "revisa esto", model="opencode/nemotron-3-ultra-free",
            model_policy="free-allowed", sensitivity="sensitive",
        )
        self.assertFalse(r["ok"])


class TestRetryCancel(ActionsFixture):
    def test_retry_only_on_dead(self) -> None:
        tid = db.add_task("qa-gate", "p", path=self.dbpath)
        # pending no reintentable
        r = actions.do_retry(tid)
        self.assertFalse(r["ok"])
        # marcar dead y reintentar
        db.update_task(tid, self.dbpath, status="dead")
        r = actions.do_retry(tid)
        self.assertTrue(r["ok"])
        row = [t for t in db.list_tasks(path=self.dbpath) if t["id"] == tid][0]
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["attempts"], 0)

    def test_cancel_only_pending(self) -> None:
        tid = db.add_task("qa-gate", "p", path=self.dbpath)
        r = actions.do_cancel(tid)
        self.assertTrue(r["ok"])
        row = [t for t in db.list_tasks(path=self.dbpath) if t["id"] == tid][0]
        self.assertEqual(row["status"], "dead")
        # done no se cancela
        tid2 = db.add_task("qa-gate", "p2", path=self.dbpath)
        db.update_task(tid2, self.dbpath, status="done")
        self.assertFalse(actions.do_cancel(tid2)["ok"])

    def test_not_found(self) -> None:
        self.assertFalse(actions.do_retry(999)["ok"])
        self.assertFalse(actions.do_cancel(999)["ok"])

    def test_cancel_sensitive_scrubs_payload(self) -> None:
        tid = db.add_task(
            "qa-gate", "dato sensible", sensitivity="sensitive", path=self.dbpath
        )
        self.assertTrue(actions.do_cancel(tid)["ok"])
        row = db.list_tasks(path=self.dbpath, include_private=True)[0]
        self.assertEqual(row["prompt"], "[purged]")
        self.assertTrue(row["finished_at"])


class TestRestart(ActionsFixture):
    @mock.patch.object(actions.subprocess, "run")
    def test_restart_whitelisted(self, mrun: mock.Mock) -> None:
        mrun.return_value = actions.subprocess.CompletedProcess([], 0, "", "")
        r = actions.do_restart("opencode-kairos.timer")
        self.assertTrue(r["ok"])
        self.assertEqual(mrun.call_args[0][0][:3], ["systemctl", "--user", "restart"])

    def test_restart_rejects_unknown(self) -> None:
        r = actions.do_restart("sshd.service")
        self.assertFalse(r["ok"])
        self.assertIn("no reiniciable", r["error"])


class TestRunNext(ActionsFixture):
    def test_empty_queue_ok(self) -> None:
        with mock.patch.object(actions.runner, "run_next", return_value=None):
            r = actions.do_run_next()
        self.assertTrue(r["ok"])

    def test_busy_lock(self) -> None:
        actions._runner_lock.acquire()
        try:
            r = actions.do_run_next()
            self.assertFalse(r["ok"])
            self.assertIn("ocupado", r["error"])
        finally:
            actions._runner_lock.release()


if __name__ == "__main__":
    unittest.main()
