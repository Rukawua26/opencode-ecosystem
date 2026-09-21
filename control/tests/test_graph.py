"""Tests del grafo operativo del ecosistema (control.graph)."""

from __future__ import annotations

import json
import unittest
from unittest import mock

from control import graph
from control.model import Health, Snapshot


def _snap(timers_active: int = 3, timers_total: int = 3,
          opencode: bool = True) -> Snapshot:
    snap = Snapshot(generated_at="2026-09-19T00:00:00+00:00")
    snap.counts = {"skills": 10, "agentes": 2}
    snap.health = Health(ok=True, timers_active=timers_active,
                         timers_total=timers_total,
                         open_code_active=opencode)
    return snap


class TestGraph(unittest.TestCase):
    def _graph(self, snap=None, queue=None):
        with mock.patch.object(graph, "queue_summary", return_value=queue):
            return graph.build_graph(snap or _snap())

    def test_estructura_valida(self) -> None:
        g = self._graph()
        ids = {n["id"] for n in g["nodes"]}
        self.assertEqual(len(g["nodes"]), g["node_count"])
        self.assertEqual(len(g["edges"]), g["edge_count"])
        for e in g["edges"]:
            self.assertIn(e["from"], ids)
            self.assertIn(e["to"], ids)
            self.assertIn(e["source"], ("declarado", "observado"))
            self.assertTrue(e["label"])
        for n in g["nodes"]:
            self.assertIn(n["status"], ("ok", "warn", "err", "info"))
            self.assertIn("layer", n)

    def test_estado_timers_inactivo(self) -> None:
        g = self._graph(_snap(timers_active=1))
        timers = next(n for n in g["nodes"] if n["id"] == "timers")
        self.assertEqual(timers["status"], "err")

    def test_estado_opencode_caido(self) -> None:
        g = self._graph(_snap(opencode=False))
        oc = next(n for n in g["nodes"] if n["id"] == "opencode")
        self.assertEqual(oc["status"], "err")

    def test_cola_con_dead_observados_avisa(self) -> None:
        # tareas dead historicas no son un fallo activo: avisan, no alarman
        g = self._graph(queue={"pending": 0, "running": 0, "dead": 2})
        cola = next(n for n in g["nodes"] if n["id"] == "cola")
        self.assertEqual(cola["status"], "warn")

    def test_cola_vacia_es_info(self) -> None:
        g = self._graph(queue={"pending": 0, "running": 0, "dead": 0})
        cola = next(n for n in g["nodes"] if n["id"] == "cola")
        self.assertEqual(cola["status"], "info")

    def test_runner_warn_si_ocupado(self) -> None:
        g = self._graph(queue={"running": 1})
        runner = next(n for n in g["nodes"] if n["id"] == "runner")
        self.assertEqual(runner["status"], "warn")

    def test_cola_caida_no_rompe_grafo(self) -> None:
        def boom():
            raise RuntimeError("db caida")
        with mock.patch.object(graph, "queue_summary", side_effect=boom):
            g = graph.build_graph(_snap())
        self.assertTrue(g["nodes"])
        cola = next(n for n in g["nodes"] if n["id"] == "cola")
        self.assertEqual(cola["status"], "info")

    def test_sanitizado(self) -> None:
        raw = json.dumps(self._graph())
        for campo in ("prompt", "workspace", "verification_command"):
            self.assertNotIn(campo, raw)

    def test_nodos_con_evidencia(self) -> None:
        g = self._graph()
        for n in g["nodes"]:
            self.assertTrue(n["evidence"], f"nodo sin evidencia: {n['id']}")
            self.assertIn(n["source"], ("observado", "declarado"))

    def test_mapeo_eventos_directo(self) -> None:
        g = self._graph()
        kinds = g["node_event_kinds"]
        self.assertEqual(kinds["timers"], "timer")
        self.assertEqual(kinds["reconciliador"], "reconciliador")
        self.assertEqual(kinds["cola"], "task")
        for nid in kinds:
            self.assertIn(nid, {n["id"] for n in g["nodes"]})


if __name__ == "__main__":
    unittest.main()
