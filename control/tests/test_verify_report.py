"""Informe privado del cierre: escritura desde verify.sh y lectura saneada."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from control.verify_report import read_report


ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "verify.sh"


def _now_iso(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).strftime(
        "%Y-%m-%dT%H:%M:%S%z")


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _check(name: str, result: str, detail: str = "rc=0", rc: str = "0") -> dict:
    return {"name": name, "scope": "working tree", "result": result,
            "detail": detail, "rc": rc, "elapsed_s": 1}


def _payload(checks, exit_code=0, state="completed", **extra) -> dict:
    out = {"schema": 1, "state": state, "exit_code": exit_code,
           "started_at": _now_iso(), "ended_at": _now_iso(),
           "elapsed_s": 30, "checks": checks}
    out.update(extra)
    return out


class ReportReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "verify-last.json"

    # --- ausencia y corrupcion nunca son verde ---

    def test_ausente_no_es_aprobacion(self) -> None:
        r = read_report(self.path)
        self.assertFalse(r["available"])
        self.assertEqual(r["state"], "none")
        self.assertEqual(r["overall"], "unknown")
        self.assertIn("sin ejecucion registrada", r["why"])
        self.assertEqual(r["checks"], [])

    def test_verde_sin_checks_no_es_verde(self) -> None:
        # Regresion del verificador: exit_code=0 sin evidencia registrada se
        # pintaba como "cierre verde". Puede ocurrir si verify.sh introduce un
        # resultado que el lector no reconoce y todos los checks se descartan.
        _write(self.path, _payload([], exit_code=0))
        r = read_report(self.path)
        self.assertEqual(r["overall"], "unknown")
        self.assertEqual(r["checks"], [])
        self.assertIn("no hay evidencia", r["why"])

    def test_todos_los_checks_descartados_no_es_verde(self) -> None:
        # Resultado desconocido para el lector: se descarta cada check y el
        # informe queda sin evidencia.
        _write(self.path, _payload([_check("x", "skipped")], exit_code=0))
        r = read_report(self.path)
        self.assertEqual(r["overall"], "unknown")
        self.assertIn("no hay evidencia", r["why"])

    def test_sin_codigo_de_salida_no_se_afirma(self) -> None:
        _write(self.path, _payload([_check("unittest", "ok")], exit_code=None))
        r = read_report(self.path)
        self.assertEqual(r["overall"], "unknown")
        self.assertIn("no declara el codigo de salida", r["why"])

    def test_sin_fecha_utilizable_se_trata_como_antiguo(self) -> None:
        # Regresion: sin ended_at legible, age=None se leia como "actual".
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 0,
                           "started_at": "", "ended_at": "", "elapsed_s": 5,
                           "checks": [_check("unittest", "ok")]})
        r = read_report(self.path)
        self.assertIsNone(r["age_s"])
        self.assertTrue(r["stale"])
        self.assertIn("no tiene una fecha utilizable", r["why"])

    def test_json_anidado_profundo_no_revienta(self) -> None:
        # Regresion: RecursionError no estaba cubierto por el except.
        self.path.write_text("[" * 60000 + "]" * 60000, encoding="utf-8")
        r = read_report(self.path)
        self.assertEqual(r["state"], "corrupt")
        self.assertEqual(r["overall"], "unknown")

    def test_interrumpido_no_afirma_informe_anterior(self) -> None:
        # El marcador running sobrescribe el informe previo con os.replace:
        # no existe un cierre anterior que consultar.
        _write(self.path, {"schema": 1, "state": "running", "exit_code": None,
                           "started_at": "2020-01-01T00:00:00+0000",
                           "ended_at": "", "elapsed_s": 5, "checks": []})
        r = read_report(self.path)
        self.assertEqual(r["state"], "interrupted")
        self.assertNotIn("ultimo informe completo", r["why"])
        self.assertIn("sustituyo", r["why"])

    def test_corrupto_no_es_aprobacion(self) -> None:
        self.path.write_text("{no es json", encoding="utf-8")
        r = read_report(self.path)
        self.assertEqual(r["state"], "corrupt")
        self.assertEqual(r["overall"], "unknown")

    def test_esquema_desconocido_no_se_interpreta(self) -> None:
        _write(self.path, {"schema": 99, "state": "completed", "exit_code": 0})
        r = read_report(self.path)
        self.assertEqual(r["state"], "unknown_schema")
        self.assertEqual(r["overall"], "unknown")

    def test_verde_marca_limite_del_informe(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 0,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:30+0000",
                           "elapsed_s": 30, "checks": [_check("unittest", "ok")]})
        r = read_report(self.path)
        self.assertEqual(r["overall"], "ok")
        self.assertIn("no cubre sesiones", r["note"])

    # --- estados que no pueden confundirse ---

    def test_rojo_identifica_el_check_fallido(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 1,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:30+0000",
                           "elapsed_s": 30,
                           "checks": [_check("unittest", "fail", "error; rc=1", "1"),
                                      _check("QA strict", "ok")]})
        r = read_report(self.path)
        self.assertEqual(r["overall"], "red")
        self.assertEqual(r["failing"], ["unittest"])
        self.assertIn("unittest", r["why"])

    def test_warn_no_es_fallo(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 0,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("hygiene triggers", "warn",
                                             "trigger informativo; rc=1", "1")]})
        r = read_report(self.path)
        self.assertEqual(r["overall"], "ok")
        self.assertEqual(r["failing"], [])
        self.assertIn("No es un fallo", r["checks"][0]["why"])

    def test_en_curso_no_se_presenta_como_completado(self) -> None:
        _write(self.path, {"schema": 1, "state": "running", "exit_code": None,
                           "started_at": _now_iso(), "ended_at": "",
                           "elapsed_s": 5, "checks": []})
        r = read_report(self.path)
        self.assertEqual(r["state"], "running")
        self.assertEqual(r["overall"], "unknown")
        self.assertIn("en curso", r["why"])

    def test_en_curso_antiguo_es_interrumpido(self) -> None:
        _write(self.path, {"schema": 1, "state": "running", "exit_code": None,
                           "started_at": "2020-01-01T00:00:00+0000",
                           "ended_at": "", "elapsed_s": 5, "checks": []})
        r = read_report(self.path)
        self.assertEqual(r["state"], "interrupted")
        self.assertEqual(r["overall"], "unknown")
        self.assertIn("interrumpido", r["why"])

    def test_verde_antiguo_no_se_presenta_como_actual(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 0,
                           "started_at": "2020-01-01T00:00:00+0000",
                           "ended_at": "2020-01-01T00:05:00+0000", "elapsed_s": 300,
                           "checks": [_check("unittest", "ok")]})
        r = read_report(self.path)
        self.assertTrue(r["stale"])
        self.assertEqual(r["overall"], "ok")
        self.assertIn("Describe el pasado", r["why"])

    # --- honestidad de la causa ---

    def test_causa_desconocida_lo_dice(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 1,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("raro", "fail", "detalle nunca visto", "9")]})
        r = read_report(self.path)
        self.assertIn("no la salida del comando", r["checks"][0]["why"])

    def test_timeout_explica_sin_inventar(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 1,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("unittest", "incomplete",
                                             "limite de tiempo o terminacion; sin cierre completo",
                                             "124")]})
        r = read_report(self.path)
        self.assertIn("presupuesto de tiempo", r["checks"][0]["why"])

    def test_no_usable_explica_que_no_se_analizo(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 1,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("QA strict", "incomplete",
                                             "error operativo o alcance incompleto; rc=2", "2")]})
        r = read_report(self.path)
        self.assertIn("no cubre", r["checks"][0]["why"])

    # --- saneamiento ---

    def test_campos_desconocidos_se_descartan(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 0,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("unittest", "ok")],
                           "stdout_del_hijo": "secreto",
                           "prompt": "noPersistido"})
        r = read_report(self.path)
        self.assertNotIn("secreto", json.dumps(r))
        self.assertNotIn("noPersistido", json.dumps(r))

    def test_resultado_inventado_se_ignora(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 0,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("raro", "todo-perfecto")]})
        r = read_report(self.path)
        self.assertEqual(r["checks"], [])

    def test_caracteres_de_control_se_neutralizan(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 1,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("x\x1b[2Jevil", "fail", "rc=1", "1")]})
        r = read_report(self.path)
        self.assertNotIn("\x1b", json.dumps(r))
        self.assertNotIn("[2J", json.dumps(r))

    def test_texto_se_acota(self) -> None:
        _write(self.path, {"schema": 1, "state": "completed", "exit_code": 1,
                           "started_at": "2026-10-12T10:00:00+0000",
                           "ended_at": "2026-10-12T10:00:10+0000", "elapsed_s": 10,
                           "checks": [_check("n" * 500, "fail", "d" * 500, "1")]})
        r = read_report(self.path)
        self.assertLessEqual(len(r["checks"][0]["name"]), 60)
        self.assertLessEqual(len(r["checks"][0]["detail"]), 200)


class VerifyWritesReportTests(unittest.TestCase):
    """El contrato de verify.sh: escribe informe privado y no cambia su salida."""

    def run_verify(self, home: Path) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "HOME": str(home)}
        return subprocess.run(["bash", str(VERIFY)], env=env, text=True,
                              capture_output=True, timeout=120)

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        repo = self.home / "opencode-ecosystem"
        (repo / "scripts").mkdir(parents=True)
        (repo / "control" / "tests").mkdir(parents=True)
        (repo / "control" / "tests" / "test_local.py").write_text(
            "import unittest\nclass L(unittest.TestCase):\n"
            "    def test_x(self): self.assertTrue(True)\n", encoding="utf-8")
        shutil = __import__("shutil")
        for name in ("hygiene.sh", "qa-gate.sh"):
            shutil.copyfile(ROOT / "scripts" / name, repo / "scripts" / name)
        shutil.copyfile(ROOT / "opencode-ecosystem", repo / "opencode-ecosystem")
        shutil.copyfile(ROOT / "validate-skills.py", repo / "validate-skills.py")
        (repo / "skills").mkdir()

    def test_informe_privado_con_permisos_y_atomico(self) -> None:
        done = self.run_verify(self.home)
        report = self.home / ".local" / "share" / "opencode-control" / "verify-last.json"
        self.assertTrue(report.is_file(), done.stdout + done.stderr)
        self.assertEqual(stat.S_IMODE(report.stat().st_mode), 0o600)
        raw = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(raw["schema"], 1)
        self.assertIn(raw["state"], ("completed", "running"))
        self.assertEqual(raw["exit_code"], done.returncode)
        # Sin temporales Left: la escritura es atomica
        leftovers = [p.name for p in report.parent.iterdir() if p.name != "verify-last.json"]
        self.assertEqual(leftovers, [], f"temporales sin limpiar: {leftovers}")

    def test_informe_no_contiene_salida_de_los_hijos(self) -> None:
        secret = "SALIDA_SECRETA_DEL_HIJO"
        (self.home / "opencode-ecosystem" / "control" / "tests" / "test_local.py").write_text(
            f"import unittest\nclass L(unittest.TestCase):\n"
            f"    def test_x(self): self.assertTrue(True)\n# {secret}\n", encoding="utf-8")
        done = self.run_verify(self.home)
        report = self.home / ".local" / "share" / "opencode-control" / "verify-last.json"
        text = report.read_text(encoding="utf-8")
        self.assertNotIn(secret, text)
        self.assertNotIn(secret, done.stdout + done.stderr)

    def test_stdout_conserva_el_formato_por_check(self) -> None:
        # Fixture aislado: ~/tools no existe y no hay repo git, asi que varios
        # checks fallan. Lo que se verifica aqui es el CONTRACTO de salida, no
        # el resultado: una linea por check con estado, detalle y alcance.
        done = self.run_verify(self.home)
        self.assertIn("alcance:", done.stdout)
        report = self.home / ".local" / "share" / "opencode-control" / "verify-last.json"
        raw = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(raw["exit_code"], done.returncode)
        self.assertTrue(done.stdout.rstrip().endswith(
            "[ok] verify verde" if done.returncode == 0 else "[fail] verify rojo"))
        names = [c["name"] for c in raw["checks"]]
        for expected in ("hygiene triggers", "skills fuente", "unittest", "QA strict"):
            self.assertIn(expected, names)
        for check in raw["checks"]:
            self.assertIn(check["result"], ("ok", "warn", "fail", "unavailable", "incomplete"))
            self.assertTrue(check["scope"], f"check sin alcance: {check}")

    def test_argumentos_invalidos_siguen_siendo_2(self) -> None:
        env = {**os.environ, "HOME": str(self.home)}
        done = subprocess.run(["bash", str(VERIFY), "extra"], env=env, text=True,
                              capture_output=True, timeout=60)
        self.assertEqual(done.returncode, 2)
        self.assertIn("argumentos invalidos", done.stdout)


if __name__ == "__main__":
    unittest.main()