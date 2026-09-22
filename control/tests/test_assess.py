"""Tests de `control task assess` y su contrato sanitizado."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control import cli, db


class AssessFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "tasks.db"
        db.init_db(self.path)

    def tearDown(self) -> None:
        self.td.cleanup()

    def worker(self, status: str, finished_at: str = "") -> int:
        tid = db.add_task(
            "odd-worker",
            "prompt-secreto",
            workspace="/workspace/secreto",
            verification_command="comando-secreto",
            path=self.path,
        )
        db.update_task(tid, self.path, status=status, finished_at=finished_at)
        return tid

    def verifier(self, worker_id: int, status: str) -> int:
        tid = db.add_task(
            "odd-verifier", "prompt-verificador-secreto",
            parent_id=worker_id, path=self.path,
        )
        db.update_task(tid, self.path, status=status)
        return tid


class TestAssessStates(AssessFixture):
    def test_worker_no_terminado_es_pending_y_dead_es_failed(self) -> None:
        for status, expected in (("pending", "pending"), ("running", "pending"),
                                 ("waiting", "pending"), ("failed", "pending"),
                                 ("dead", "failed")):
            with self.subTest(status=status):
                tid = self.worker(status, "2026-09-21T10:00:00+00:00")
                result = cli.assess_task(tid, self.path)
                self.assertEqual(result["review_state"], expected)
                self.assertEqual(result["review_due"], "")
                self.assertEqual(result["next_transition"], "")
                self.assertLessEqual(len(result["reason"]), 80)

    def test_worker_done_sin_verifier_es_due(self) -> None:
        tid = self.worker("done", "2026-09-21T10:00:00+00:00")

        self.assertEqual(cli.assess_task(tid, self.path), {
            "task_id": tid,
            "verifier_id": None,
            "review_state": "due",
            "review_due": "2026-09-21T10:00:00+00:00",
            "next_transition": "",
            "reason": "verificador ausente",
        })

    def test_verifier_pending_emite_transicion_exacta(self) -> None:
        worker_id = self.worker("done", "2026-09-21T10:00:00+00:00")
        verifier_id = self.verifier(worker_id, "pending")

        result = cli.assess_task(worker_id, self.path)

        self.assertEqual(result["verifier_id"], verifier_id)
        self.assertEqual(result["review_state"], "due")
        self.assertEqual(result["next_transition"],
                         "python3 -m control.cli task run")

    def test_verifier_pending_no_emite_si_otra_tarea_espera_antes(self) -> None:
        worker_id = self.worker("done", "2026-09-21T10:00:00+00:00")
        db.add_task("qa-gate", "primera en FIFO", path=self.path)
        verifier_id = self.verifier(worker_id, "pending")

        result = cli.assess_task(worker_id, self.path)

        self.assertEqual(result["verifier_id"], verifier_id)
        self.assertEqual(result["review_state"], "due")
        self.assertEqual(result["next_transition"], "")
        self.assertEqual(result["reason"], "verificador espera turno")

    def test_estados_del_verifier(self) -> None:
        cases = {
            "running": ("pending", "verificador en curso"),
            "waiting": ("pending", "verificador esperando decision"),
            "done": ("passed", "verificacion aprobada"),
            "dead": ("failed", "verificacion fallida"),
        }
        for status, (expected, reason) in cases.items():
            with self.subTest(status=status):
                worker_id = self.worker("done", "2026-09-21T10:00:00+00:00")
                self.verifier(worker_id, status)
                result = cli.assess_task(worker_id, self.path)
                self.assertEqual(result["review_state"], expected)
                self.assertEqual(result["next_transition"], "")
                self.assertEqual(result["reason"], reason)

    def test_verifier_waiting_review_es_failed_sin_transicion(self) -> None:
        worker_id = self.worker("done", "2026-09-21T10:00:00+00:00")
        verifier_id = self.verifier(worker_id, "waiting")
        db.update_task(verifier_id, self.path, error_kind="review")

        result = cli.assess_task(worker_id, self.path)

        self.assertEqual(result["verifier_id"], verifier_id)
        self.assertEqual(result["review_state"], "failed")
        self.assertEqual(result["next_transition"], "")
        self.assertEqual(result["reason"], "revision fallida (espera decision)")
        self.assertLessEqual(len(result["reason"]), 80)

    def test_rechaza_inexistente_y_agente_no_worker(self) -> None:
        with self.assertRaisesRegex(ValueError, "no existe"):
            cli.assess_task(999, self.path)
        tid = db.add_task("qa-gate", "revisa", path=self.path)
        with self.assertRaisesRegex(ValueError, "odd-worker"):
            cli.assess_task(tid, self.path)


class TestAssessCli(unittest.TestCase):
    def test_cli_imprime_solo_json_sanitizado(self) -> None:
        result = {
            "task_id": 7,
            "verifier_id": 8,
            "review_state": "due",
            "review_due": "2026-09-21T10:00:00+00:00",
            "next_transition": "python3 -m control.cli task run",
            "reason": "verificador pendiente",
        }
        with mock.patch.object(cli, "assess_task", return_value=result), \
                mock.patch("builtins.print") as printer:
            code = cli.cmd_task(["assess", "7"])

        self.assertEqual(code, 0)
        payload = json.loads(printer.call_args.args[0])
        self.assertEqual(payload, result)
        raw = printer.call_args.args[0]
        for private in ("prompt", "workspace", "verification_command"):
            self.assertNotIn(private, raw)

    def test_cli_rechazo_devuelve_dos(self) -> None:
        with mock.patch.object(cli, "assess_task",
                               side_effect=ValueError("tarea no valida")), \
                mock.patch("builtins.print") as printer:
            code = cli.cmd_task(["assess", "99"])

        self.assertEqual(code, 2)
        self.assertIn("rechazado", printer.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
