"""Errores de consultas systemd simulados, sin bus ni timers reales."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control import collect
from control.model import ServiceStatus, TimerInfo


class TimerObservationTests(unittest.TestCase):
    def response(self, stdout, code=0):
        return subprocess.CompletedProcess([], code, stdout, "")

    def listing(self):
        return self.response('[{"unit":"opencode-demo.timer"}]')

    def test_listing_errors_never_report_active(self):
        cases = [self.response('[{"unit":"opencode-demo.timer"}]', 1),
                 self.response('invalid'), self.response('{}'),
                 self.response('[null]'), self.response('[{"unit":null}]'),
                 OSError("denied"), subprocess.TimeoutExpired("systemctl", 5)]
        for case in cases:
            with self.subTest(case=case), mock.patch.object(
                collect.subprocess, "run", side_effect=[case]
            ):
                self.assertEqual(collect._systemd_timers(), [])

    def test_detail_errors_never_keep_listing_active(self):
        cases = [self.response("ActiveState=active", 1), self.response(""),
                 self.response("Result=success"), OSError("denied"),
                 subprocess.TimeoutExpired("systemctl", 5)]
        for case in cases:
            with self.subTest(case=case), mock.patch.object(
                collect.subprocess, "run", side_effect=[self.listing(), case]
            ):
                timers = collect._systemd_timers()
                self.assertEqual(len(timers), 1)
                self.assertFalse(timers[0].active)
                self.assertEqual(timers[0].result, "unknown")

    def test_success_and_whitelist(self):
        listing = self.response('[{"unit":"other.timer"}, {"unit":"opencode-demo.timer"}]')
        with mock.patch.object(collect.subprocess, "run", side_effect=[
            listing, self.response("ActiveState=active\nResult=success\nNextElapseUSecRealtime=next\nLastTriggerUSec=last")
        ]) as run:
            timers = collect._systemd_timers()
        self.assertEqual(len(timers), 1)
        self.assertTrue(timers[0].active)
        self.assertEqual((timers[0].result, timers[0].next_run, timers[0].last_run),
                         ("success", "next", "last"))
        self.assertEqual(run.call_count, 2)

    def test_observed_inactive_is_not_a_query_error(self):
        with mock.patch.object(collect.subprocess, "run", side_effect=[
            self.listing(), self.response("ActiveState=inactive\nResult=success")
        ]):
            timers = collect._systemd_timers()
        self.assertFalse(timers[0].active)
        self.assertEqual(timers[0].result, "success")

    def test_listing_error_makes_snapshot_unhealthy(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode") as td, \
             mock.patch.object(collect, "_opencode_service", return_value=ServiceStatus(active=True)), \
             mock.patch.object(collect.subprocess, "run", return_value=self.response("[]", 1)):
            snap = collect.collect_snapshot(Path(td))
        self.assertFalse(snap.health.ok)

    def test_unknown_detail_makes_snapshot_unhealthy_even_with_active_timer(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode") as td, \
             mock.patch.object(collect, "_opencode_service", return_value=ServiceStatus(active=True)), \
             mock.patch.object(collect, "_systemd_timers", return_value=[
                 TimerInfo(name="opencode-good.timer", active=True),
                 TimerInfo(name="opencode-bad.timer", active=False, result="unknown")]):
            snap = collect.collect_snapshot(Path(td))
        self.assertFalse(snap.health.ok)
        self.assertTrue(any("consulta systemd no disponible" in e for e in snap.health.errors))
