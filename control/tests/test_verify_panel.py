"""Tarjeta de "Ultimo cierre" del panel: contrato de render honesto.

No basta con que el JS sea valido: un informe ausente o en curso jamas puede
pintarse como cierre verde. Se ejecuta la funcion real del panel contra datos
sinteticos con un DOM minimo (node, sin navegador).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "control" / "web" / "index.html"

_HARNESS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const data = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const src = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x => x[1]).join('\n');
function pick(name) {
  const i = src.indexOf('function ' + name + '(');
  if (i < 0) throw new Error('falta ' + name);
  let d = 0, end = src.length;
  const j = src.indexOf('{', i);
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (!d) { end = k + 1; break; } }
  }
  const start = src.slice(i - 6, i) === 'async ' ? i - 6 : i;
  return src.slice(start, end);
}
const badge = src.match(/const VERIFY_BADGE = \{[\s\S]*?\};/);
if (!badge) throw new Error('falta VERIFY_BADGE');
const box = { innerHTML: '' };
const document = { getElementById: () => box };
const fetchJSON = async () => data;
const code = [pick('esc'), pick('fmtAge'), pick('verifyBadge'), badge[0], pick('loadVerify')]
  .join('\n') + `
  (async () => { await loadVerify(); console.log(box.innerHTML); })();`;
new Function('document', 'fetchJSON', 'data', 'box', code)(document, fetchJSON, data, box);
"""


def _render(payload: dict) -> str:
    node = shutil.which("node")
    if node is None:
        raise unittest.SkipTest("node no disponible")
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "h.js"
        data = Path(tmp) / "d.json"
        script.write_text(_HARNESS, encoding="utf-8")
        data.write_text(json.dumps(payload), encoding="utf-8")
        done = subprocess.run([node, str(script), str(INDEX), str(data)],
                              text=True, capture_output=True, timeout=60)
        if done.returncode != 0:
            raise AssertionError(f"render fallo: {done.stderr}")
        out = done.stdout
        if not out.strip():
            raise AssertionError(
                "el harness devolvio salida vacia: las aserciones pasarian sin "
                "comprobar nada")
        return out


class VerifyPanelRenderTests(unittest.TestCase):
    def test_verde_sin_checks_no_se_pinta_verde(self) -> None:
        # Regresion del verificador: sin evidencia el panel no puede decir verde.
        out = _render({"available": True, "state": "completed", "overall": "unknown",
                       "checks": [], "failing": [], "exit_code": 0,
                       "age_s": 60.0, "elapsed_s": 30, "stale": False,
                       "why": "no hay evidencia para afirmarla", "note": "limite"})
        self.assertNotIn("cierre verde", out)
        self.assertIn("no hay evidencia", out)

    def test_sin_informe_no_se_pinta_verde(self) -> None:
        out = _render({"available": False, "state": "none", "overall": "unknown",
                       "checks": [], "why": "sin ejecucion registrada",
                       "note": "", "failing": [], "exit_code": None,
                       "age_s": None, "elapsed_s": None, "stale": False})
        self.assertIn("sin ejecucion registrada", out)
        self.assertNotIn("cierre verde", out)
        self.assertIn("./verify.sh", out)

    def test_en_curso_no_se_pinta_verde(self) -> None:
        out = _render({"available": True, "state": "running", "overall": "unknown",
                       "checks": [], "failing": [], "exit_code": None,
                       "age_s": 12.0, "elapsed_s": 12, "stale": False,
                       "why": "hay un cierre registrado como en curso", "note": ""})
        self.assertNotIn("cierre verde", out)
        self.assertIn("en curso", out)

    def test_verde_muestra_cada_check_con_detalle_y_motivo(self) -> None:
        checks = [
            {"name": "hygiene triggers", "scope": "runtime", "result": "warn",
             "detail": "trigger informativo; rc=1", "rc": "1", "elapsed_s": 0,
             "why": "No es un fallo"},
            {"name": "unittest", "scope": "working tree control/tests", "result": "ok",
             "detail": "rc=0", "rc": "0", "elapsed_s": 29,
             "why": "termino correctamente (rc=0)"},
        ]
        out = _render({"available": True, "state": "completed", "overall": "ok",
                       "checks": checks, "failing": [], "exit_code": 0,
                       "age_s": 120.0, "elapsed_s": 30, "stale": False,
                       "why": "", "note": "limite"})
        self.assertIn("cierre verde", out)
        self.assertIn("rc=0", out)
        self.assertIn("unittest", out)
        self.assertIn("working tree control/tests", out)
        self.assertIn("termino correctamente", out)
        self.assertIn("No es un fallo", out)

    def test_rojo_nombra_los_checks_bloqueantes(self) -> None:
        checks = [{"name": "unittest", "scope": "working tree", "result": "fail",
                   "detail": "error; rc=1", "rc": "1", "elapsed_s": 29,
                   "why": "el comando termino con error"}]
        out = _render({"available": True, "state": "completed", "overall": "red",
                       "checks": checks, "failing": ["unittest"], "exit_code": 1,
                       "age_s": 120.0, "elapsed_s": 30, "stale": False,
                       "why": "comprobaciones con resultado bloqueante: unittest",
                       "note": "limite"})
        self.assertIn("cierre rojo", out)
        self.assertIn("checks con resultado bloqueante", out)
        self.assertNotIn("cierre verde", out)

    def test_antiguo_se_marca_como_tal(self) -> None:
        out = _render({"available": True, "state": "completed", "overall": "ok",
                       "checks": [], "failing": [], "exit_code": 0,
                       "age_s": 90000.0, "elapsed_s": 30, "stale": True,
                       "why": "Describe el pasado, no el estado actual",
                       "note": "limite"})
        self.assertIn("antiguo", out)
        self.assertIn("Describe el pasado", out)

    def test_error_de_lectura_no_se_pinta_como_salud(self) -> None:
        # fetchJSON rechaza: el panel debe avisar, nunca mostrar un estado verde
        self.assertIn("fetchJSON", INDEX.read_text(encoding="utf-8"))
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("no se pudo leer el informe del cierre", html)

    def test_el_panel_no_puede_ejecutar_el_cierre(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        # Ninguna accion POST/GET que lance el cierre o la suite.
        for marker in ("/api/actions/verify", "run-verify", "ejecutar verify",
                       "/api/verify/run", "subprocess", "child_process", "execSync"):
            self.assertNotIn(marker, html, f"el panel no debe lanzar el cierre: {marker}")
        # La seccion debe existir de verdad (con tilde, como esta en el HTML).
        self.assertIn("Último cierre", html)

    def test_no_hay_websocket_ni_polling_nuevo(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertNotIn("EventSource", html)
        self.assertNotIn("new WebSocket", html)
        # El informe se engancha al refresco existente, no a un setInterval propio.
        self.assertNotIn("setInterval(loadVerify", html)
        self.assertIn("loadVerify();", html)


if __name__ == "__main__":
    unittest.main()