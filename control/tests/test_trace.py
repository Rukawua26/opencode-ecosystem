"""Tests de la traza por tarea (control.trace) y su endpoint.

Todo mockeado o contra SQLite en /tmp: nunca llama a opencode real.
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from urllib.request import urlopen
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from control import db, runner, server, trace


class TraceFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "t.db"
        db.init_db(self.path)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _ok(self, agent: str, prompt: str, model: str = "",
            workspace: str = "") -> dict[str, object]:
        return {"code": 0, "duration": 1.0, "note": "", "error_kind": "",
                "result": "success", "summary": "ok", "question": "",
                "next_transition": ""}


class TestEventsForTask(TraceFixture):
    def test_frontera_exacta_task_1_no_matchea_task_10(self) -> None:
        db.record_event("qa-gate", "task", "completada", "ok",
                        "task #1 en 3s", path=self.path)
        db.record_event("qa-gate", "task", "completada", "ok",
                        "task #10 en 3s", path=self.path)
        rows = db.events_for_task(1, path=self.path)
        self.assertEqual(len(rows), 1)
        self.assertIn("task #1 ", rows[0]["detail"])

    def test_sin_referencias_devuelve_vacio(self) -> None:
        db.record_event("panel", "accion", "refresh", "ok", "manual",
                        path=self.path)
        self.assertEqual(db.events_for_task(7, path=self.path), [])


class TestPhaseAndStopReason(unittest.TestCase):
    def test_fases_por_estado(self) -> None:
        self.assertEqual(trace.compute_phase({"status": "pending"}, []), "en cola")
        self.assertEqual(trace.compute_phase({"status": "done"}, []), "completada")
        self.assertEqual(trace.compute_phase({"status": "dead"}, []), "detenida")
        self.assertEqual(trace.compute_phase({"status": "running"}, []),
                         "ejecutando agente")

    def test_fase_running_con_checkpoint_verificacion(self) -> None:
        ev = {"ts": "t", "event": "fase: verificacion determinista",
              "status": "", "detail": "task #1", "duration_s": None}
        self.assertEqual(trace.compute_phase({"status": "running"}, [ev]),
                         "verificacion determinista")

    def test_reintento_no_hereda_fase_verificacion_anterior(self) -> None:
        self.assertEqual(trace.compute_phase({"status": "running"}, [
            {"event": "iniciada"},
            {"event": "fase: verificacion determinista"},
        ]), "ejecutando agente")

    def test_fase_waiting(self) -> None:
        self.assertEqual(
            trace.compute_phase({"status": "waiting", "error_kind": "review"}, []),
            "revision fallida: esperando decision")
        self.assertEqual(
            trace.compute_phase({"status": "waiting", "error_kind": "",
                                 "note": "transicion no registrada"}, []),
            "transicion no registrada: esperando control-plane")
        self.assertEqual(
            trace.compute_phase({"status": "waiting", "error_kind": "",
                                 "note": "falta aprobacion"}, []),
            "bloqueada: esperando decision humana")

    def test_stop_reasons(self) -> None:
        self.assertEqual(
            trace.stop_reason({"status": "dead", "error_kind": "timeout",
                               "note": ""}),
            "timeout del agente (15 min)")
        self.assertEqual(
            trace.stop_reason({"status": "dead", "error_kind": "",
                               "note": "reconciliador: lease_vencido"}),
            "proceso huerfano, lease vencido (marcado por reconciliador)")
        self.assertEqual(trace.stop_reason({"status": "running",
                                            "error_kind": "", "note": ""}), "")


class TestBuildTrace(TraceFixture):
    def test_tarea_inexistente_devuelve_none(self) -> None:
        self.assertIsNone(trace.build_trace(999, self.path))

    def test_traza_de_tarea_completada(self) -> None:
        tid = db.add_task("odd-worker", "implementa X", workflow="odd",
                          path=self.path)
        with mock.patch.object(runner, "_run_agent", side_effect=self._ok):
            runner.run_next(self.path)
        tr = trace.build_trace(tid, self.path)
        assert tr is not None
        self.assertEqual(tr["status"], "done")
        self.assertEqual(tr["phase"], "completada")
        self.assertIsNotNone(tr["elapsed_s"])
        self.assertTrue(any(e["event"] == "completada" for e in tr["timeline"]))
        self.assertIsNotNone(tr["verifier"])  # worker encadena verifier
        self.assertEqual(tr["verifier"]["status"], "pending")

    def test_traza_running_muestra_fase_y_lease(self) -> None:
        tid = db.add_task("qa-gate", "revisa", verification_command="true",
                          path=self.path)
        db.claim_next("test", 100, self.path)
        db.record_event("qa-gate", "task", "fase: verificacion determinista",
                        "", f"task #{tid}", path=self.path)
        tr = trace.build_trace(tid, self.path)
        assert tr is not None
        self.assertEqual(tr["phase"], "verificacion determinista")
        self.assertTrue(tr["lease_until"])
        self.assertEqual(tr["status"], "running")
        self.assertIsNotNone(tr["elapsed_s"])

    def test_traza_sanitizada(self) -> None:
        tid = db.add_task("odd-worker", "prompt secreto", path=self.path)
        tr = trace.build_trace(tid, self.path)
        assert tr is not None
        raw = json.dumps(tr)
        for campo in ("prompt", "workspace", "verification_command",
                       "secreto"):
            self.assertNotIn(campo, raw)


class TestExecutionMetrics(TraceFixture):
    def test_running_fuera_del_limite_sigue_visible_y_sanitizada(self) -> None:
        tid = db.add_task("odd-worker", "prompt secreto", path=self.path)
        db.claim_next("prueba", 60, self.path)
        for _ in range(35):
            db.add_task("qa-gate", "otro", path=self.path)
        self.assertNotIn(tid, [r["id"] for r in db.list_tasks(30, self.path)])
        active = db.running_task(self.path)
        self.assertEqual(active["id"], tid)
        self.assertNotIn("prompt", active)

    def test_resultados_por_agente_y_fases_sin_payload(self) -> None:
        done = db.add_task("odd-worker", "prompt secreto", path=self.path)
        dead = db.add_task("odd-worker", "otro secreto", path=self.path)
        waiting = db.add_task("odd-verifier", "decision", path=self.path)
        now = datetime.now(timezone.utc)
        start = (now - timedelta(seconds=10)).isoformat()
        end = now.isoformat()
        db.update_task(done, self.path, status="done", started_at=start, finished_at=end)
        db.update_task(dead, self.path, status="dead", started_at=start, finished_at=end,
                       error_kind="timeout")
        db.update_task(waiting, self.path, status="waiting", started_at=start, finished_at=end)
        db.record_event("odd-worker", "phase", "agente terminado", "ok",
                        f"task #{done}", duration_s=3.5, path=self.path)
        data = db.execution_metrics(self.path)
        self.assertEqual([(r["agent"], r["status"], r["count"]) for r in data["agents"]],
                         [("odd-verifier", "waiting", 1), ("odd-worker", "dead", 1),
                          ("odd-worker", "done", 1)])
        self.assertEqual(data["phases"][0]["avg_seconds"], 3.5)
        self.assertAlmostEqual(data["agents"][1]["avg_seconds"], 10.0, delta=0.1)
        self.assertEqual(data["dead_errors"][0]["error_kind"], "timeout")
        self.assertNotIn("secreto", json.dumps(data))

    def test_sin_datos_no_infiere_exitos(self) -> None:
        data = db.execution_metrics(self.path)
        self.assertEqual(data["agents"], [])
        self.assertEqual(data["phases"], [])

    def test_endpoint_metricas_no_expone_payload(self) -> None:
        db.add_task("odd-worker", "prompt secreto", path=self.path)
        with mock.patch.object(db, "DB_PATH", self.path), \
                server._Server(("127.0.0.1", 0), server.ControlHandler) as httpd:
            httpd.timeout = 3
            thread = threading.Thread(target=httpd.handle_request)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{httpd.server_port}/api/execution-metrics",
                             timeout=3) as response:
                    data = response.read().decode("utf-8")
                self.assertIn('"window_days": 30', data)
                self.assertNotIn("prompt secreto", data)
            finally:
                thread.join(timeout=4)

    def test_endpoint_cola_incluye_tarea_activa_fuera_del_limite(self) -> None:
        tid = db.add_task("odd-worker", "secreto", path=self.path)
        db.claim_next("prueba", 60, self.path)
        db.add_task("qa-gate", "publica", path=self.path)
        with mock.patch.object(db, "DB_PATH", self.path), \
                server._Server(("127.0.0.1", 0), server.ControlHandler) as httpd:
            httpd.timeout = 3
            thread = threading.Thread(target=httpd.handle_request)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{httpd.server_port}/api/tasks?limit=1",
                             timeout=3) as response:
                    raw = response.read().decode("utf-8")
                data = json.loads(raw)
                self.assertNotEqual(data["tasks"][0]["id"], tid)
                self.assertEqual(data["active_task"]["id"], tid)
                self.assertNotIn("secreto", raw)
            finally:
                thread.join(timeout=4)


if __name__ == "__main__":
    unittest.main()
