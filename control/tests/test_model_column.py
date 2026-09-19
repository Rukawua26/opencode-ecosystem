"""Test de migración y modelo por tarea."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control import db, runner


class TestModelColumn(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "t.db"

    def tearDown(self) -> None:
        self.td.cleanup()

    def test_migration_adds_model_column_on_old_db(self) -> None:
        # crea DB vieja sin columna model
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " agent TEXT NOT NULL, prompt TEXT NOT NULL,"
                " status TEXT NOT NULL DEFAULT 'pending',"
                " attempts INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,"
                " started_at TEXT, finished_at TEXT, result_code INTEGER,"
                " note TEXT NOT NULL DEFAULT '')"
            )
        db.init_db(self.path)  # debe migrar
        tid = db.add_task("a", "p", model="m1", path=self.path)
        row = db.list_tasks(path=self.path)[0]
        self.assertEqual(row["model"], "m1")

    def test_run_agent_passes_model_flag(self) -> None:
        calls = []

        class P:
            returncode = 0
            stdout = "ok"
            stderr = ""

        def fake_run(cmd, **kw):
            calls.append((cmd, kw))
            return P()

        import control.runner as r
        orig = r.subprocess.run
        r.subprocess.run = fake_run
        try:
            r._run_agent("build", "hola", "openai/gpt-5.6-luna")
            self.assertIn("--model", calls[0][0])
            self.assertIn("openai/gpt-5.6-luna", calls[0][0])
            r._run_agent("build", "hola")
            self.assertNotIn("--model", calls[1][0])
        finally:
            r.subprocess.run = orig

    def test_provider_error_detected_from_stdout(self) -> None:
        class P:
            returncode = 1
            stdout = "Error: Insufficient Balance"
            stderr = ""

        with mock.patch.object(runner.subprocess, "run", return_value=P()):
            rc, _, _, kind = runner._run_agent("build", "hola")
        self.assertEqual(rc, 1)
        self.assertEqual(kind, "provider_balance")

    def test_workspace_is_passed_as_cwd(self) -> None:
        class P:
            returncode = 0
            stdout = ""
            stderr = ""

        with tempfile.TemporaryDirectory(dir=Path.home()) as td:
            with mock.patch.object(runner.subprocess, "run", return_value=P()) as run:
                runner._run_agent("build", "hola", workspace=td)
            self.assertEqual(run.call_args.kwargs["cwd"], str(Path(td).resolve()))


if __name__ == "__main__":
    unittest.main()
