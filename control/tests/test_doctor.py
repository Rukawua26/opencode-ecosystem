"""Tests del diagnostico sanitizado (control.cli doctor)."""

from __future__ import annotations

import json
import subprocess
import unittest
from unittest import mock

from control import cli
from control.model import Health, Snapshot


def _snap(ok: bool = True) -> Snapshot:
    snap = Snapshot(generated_at="2026-09-18T00:00:00+00:00")
    snap.health = Health(ok=ok, timers_active=3, timers_total=3,
                         open_code_active=True)
    return snap


class TestDoctor(unittest.TestCase):
    _OPENCODE_OK = {
        "available": True,
        "version": "2.0.12",
        "compatible": True,
        "required": "2.x",
        "capabilities": {
            "run": True,
            "debug_config": True,
            "service_status": True,
        },
    }

    def _run(self):
        events = [{"ts": "t", "kind": "task", "event": "fallo",
                   "status": "fail", "detail": "x"}]
        return self._dict(events)

    def _dict(self, events, ok: bool = True, opencode=None):
        opencode = self._OPENCODE_OK if opencode is None else opencode
        store = mock.Mock()
        store.refresh.return_value = _snap(ok=ok)
        store.stale_seconds.return_value = 3.0
        with mock.patch.object(cli, "get_store", return_value=store), \
             mock.patch.object(cli, "_systemd_timers", return_value=[]), \
             mock.patch.object(cli, "queue_summary",
                               return_value={"pending": 1, "dead": 0}), \
             mock.patch.object(cli._reconcile, "check",
                               return_value={"ok": True, "findings": []}), \
             mock.patch.object(cli, "recent_events", return_value=events), \
             mock.patch.object(cli, "_opencode_diagnostic",
                               return_value=opencode):
            return cli.doctor_dict()

    def test_estructura_y_campos(self) -> None:
        d = self._run()
        self.assertTrue(d["ok"])
        self.assertEqual(d["health"]["timers_active"], 3)
        self.assertIn("queue", d)
        self.assertTrue(d["reconcile"]["ok"])
        self.assertEqual(d["recent_errors"][0]["status"], "fail")
        self.assertEqual(d["opencode"], self._OPENCODE_OK)

    def test_sanitizado_sin_campos_privados(self) -> None:
        d = self._run()
        raw = json.dumps(d)
        for campo_privado in ("prompt", "workspace", "verification_command",
                              "expected_outputs"):
            self.assertNotIn(campo_privado, raw)

    def test_ok_false_si_salud_mala(self) -> None:
        self.assertFalse(self._dict([], ok=False)["ok"])

    def test_opencode_v2_compatible_y_capacidades(self) -> None:
        completed = subprocess.CompletedProcess(
            ["opencode", "--version"], 0, stdout="opencode v2.0.12\n", stderr=""
        )
        with mock.patch.object(cli.subprocess, "run", return_value=completed) as run:
            diagnostic = cli._opencode_diagnostic()

        self.assertEqual(diagnostic, self._OPENCODE_OK)
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["opencode", "--version"])
        self.assertNotIn("shell", kwargs)
        self.assertLessEqual(kwargs["timeout"], 5)
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["errors"], "replace")

    def test_opencode_ausente_es_incompatible(self) -> None:
        with mock.patch.object(cli.subprocess, "run", side_effect=FileNotFoundError):
            diagnostic = cli._opencode_diagnostic()

        self.assertFalse(diagnostic["available"])
        self.assertIsNone(diagnostic["version"])
        self.assertFalse(diagnostic["compatible"])
        self.assertFalse(any(diagnostic["capabilities"].values()))

    def test_opencode_major_incompatible(self) -> None:
        completed = subprocess.CompletedProcess(
            ["opencode", "--version"], 0, stdout="OpenCode v1.9.7", stderr=""
        )
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            diagnostic = cli._opencode_diagnostic()

        self.assertTrue(diagnostic["available"])
        self.assertEqual(diagnostic["version"], "1.9.7")
        self.assertFalse(diagnostic["compatible"])
        self.assertFalse(any(diagnostic["capabilities"].values()))

    def test_opencode_version_malformed_es_incompatible(self) -> None:
        completed = subprocess.CompletedProcess(
            ["opencode", "--version"], 0, stdout="opencode nightly", stderr=""
        )
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            diagnostic = cli._opencode_diagnostic()

        self.assertTrue(diagnostic["available"])
        self.assertIsNone(diagnostic["version"])
        self.assertFalse(diagnostic["compatible"])

    def test_opencode_semver_en_salida_enganosa_es_incompatible(self) -> None:
        completed = subprocess.CompletedProcess(
            ["opencode", "--version"], 0,
            stdout="dependency 2.0.12 failed to initialize", stderr="",
        )
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            diagnostic = cli._opencode_diagnostic()

        self.assertTrue(diagnostic["available"])
        self.assertIsNone(diagnostic["version"])
        self.assertFalse(diagnostic["compatible"])
        self.assertFalse(any(diagnostic["capabilities"].values()))

    def test_opencode_version_unicode_es_incompatible(self) -> None:
        completed = subprocess.CompletedProcess(
            ["opencode", "--version"], 0, stdout="opencode v٢.٠.١٢", stderr=""
        )
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            diagnostic = cli._opencode_diagnostic()

        self.assertTrue(diagnostic["available"])
        self.assertIsNone(diagnostic["version"])
        self.assertFalse(diagnostic["compatible"])

    def test_opencode_componente_enorme_es_incompatible_sin_excepcion(self) -> None:
        completed = subprocess.CompletedProcess(
            ["opencode", "--version"], 0,
            stdout=f"opencode v2.0.{'9' * 10_000}", stderr="",
        )
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            diagnostic = cli._opencode_diagnostic()

        self.assertTrue(diagnostic["available"])
        self.assertIsNone(diagnostic["version"])
        self.assertFalse(diagnostic["compatible"])
        self.assertFalse(any(diagnostic["capabilities"].values()))

    def test_opencode_error_de_decodificacion_es_incompatible(self) -> None:
        error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        with mock.patch.object(cli.subprocess, "run", side_effect=error):
            diagnostic = cli._opencode_diagnostic()

        self.assertTrue(diagnostic["available"])
        self.assertIsNone(diagnostic["version"])
        self.assertFalse(diagnostic["compatible"])
        self.assertFalse(any(diagnostic["capabilities"].values()))

    def test_opencode_salida_reemplazada_es_incompatible(self) -> None:
        completed = subprocess.CompletedProcess(
            ["opencode", "--version"], 0,
            stdout="opencode v2.0.12\ufffd", stderr="",
        )
        with mock.patch.object(cli.subprocess, "run", return_value=completed):
            diagnostic = cli._opencode_diagnostic()

        self.assertTrue(diagnostic["available"])
        self.assertIsNone(diagnostic["version"])
        self.assertFalse(diagnostic["compatible"])
        self.assertFalse(any(diagnostic["capabilities"].values()))

    def test_doctor_falla_si_opencode_no_es_compatible(self) -> None:
        incompatible = {**self._OPENCODE_OK, "compatible": False}
        d = self._dict([], opencode=incompatible)
        self.assertFalse(d["ok"])

    def test_salida_humana_y_json_muestran_opencode_sanitizado(self) -> None:
        report = self._run()
        with mock.patch.object(cli, "doctor_dict", return_value=report), \
                mock.patch("builtins.print") as printer:
            self.assertEqual(cli.cmd_doctor(False), 0)
        human = "\n".join(" ".join(map(str, call.args))
                          for call in printer.call_args_list)
        self.assertIn("version=2.0.12", human)
        self.assertIn("debug_config=True", human)

        with mock.patch.object(cli, "doctor_dict", return_value=report), \
                mock.patch("builtins.print") as printer:
            self.assertEqual(cli.cmd_doctor(True), 0)
        rendered = printer.call_args.args[0]
        self.assertEqual(json.loads(rendered)["opencode"], self._OPENCODE_OK)

    def test_help_sale_con_cero(self) -> None:
        self.assertEqual(cli.main(["--help"]), 0)


if __name__ == "__main__":
    unittest.main()
