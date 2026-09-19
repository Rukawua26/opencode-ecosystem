"""Tests del diagnostico sanitizado (control.cli doctor)."""

from __future__ import annotations

import json
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
    def _run(self):
        events = [{"ts": "t", "kind": "task", "event": "fallo",
                   "status": "fail", "detail": "x"}]
        return self._dict(events)

    def _dict(self, events, ok: bool = True):
        store = mock.Mock()
        store.refresh.return_value = _snap(ok=ok)
        store.stale_seconds.return_value = 3.0
        with mock.patch.object(cli, "get_store", return_value=store), \
             mock.patch.object(cli, "_systemd_timers", return_value=[]), \
             mock.patch.object(cli, "queue_summary",
                               return_value={"pending": 1, "dead": 0}), \
             mock.patch.object(cli._reconcile, "check",
                               return_value={"ok": True, "findings": []}), \
             mock.patch.object(cli, "recent_events", return_value=events):
            return cli.doctor_dict()

    def test_estructura_y_campos(self) -> None:
        d = self._run()
        self.assertTrue(d["ok"])
        self.assertEqual(d["health"]["timers_active"], 3)
        self.assertIn("queue", d)
        self.assertTrue(d["reconcile"]["ok"])
        self.assertEqual(d["recent_errors"][0]["status"], "fail")

    def test_sanitizado_sin_campos_privados(self) -> None:
        d = self._run()
        raw = json.dumps(d)
        for campo_privado in ("prompt", "workspace", "verification_command",
                              "expected_outputs"):
            self.assertNotIn(campo_privado, raw)

    def test_ok_false_si_salud_mala(self) -> None:
        self.assertFalse(self._dict([], ok=False)["ok"])

    def test_help_sale_con_cero(self) -> None:
        self.assertEqual(cli.main(["--help"]), 0)


if __name__ == "__main__":
    unittest.main()
