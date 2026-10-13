"""plugin_doctor.sh: descubrimiento recursivo y superficie de plugins TUI.

Reproduce el punto ciego original: el doctor solo globaba *.js de primer nivel
y por eso reportaba "hooks en uso: vacio" con un plugin TUI .tsx presente.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


DOCTOR = Path.home() / "tools" / "plugin_doctor.sh"

_STUB = """#!/usr/bin/env bash
# cadenas de API consideradas presentes en el "binario"
session.stats
prompt.footer.status
home.footer.status
@opencode/plugin/tui
session.execution.succeeded
[[ "${1:-}" == "--version" ]] && echo "opencode v2.0.99"
exit 0
"""


def _skip_without_doctor() -> str | None:
    return None if DOCTOR.is_file() else "plugin_doctor.sh no disponible"


@unittest.skipUnless(DOCTOR.is_file(), "plugin_doctor.sh no disponible")
class PluginDoctorSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.bin = self.home / "bin"
        self.plugins = self.home / ".config" / "opencode" / "plugins"
        self.plugins.mkdir(parents=True)
        self.bin.mkdir()
        self.stub = self.bin / "opencode"
        self.stub.write_text(_STUB, encoding="utf-8")
        self.stub.chmod(0o755)
        self.pin = self.home / ".config" / "opencode" / ".opencode-version.pin"
        self.pin.write_text("opencode v2.0.99\n", encoding="utf-8")

    def write_plugin(self, rel: str, body: str) -> None:
        path = self.plugins / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    def run_doctor(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "HOME": str(self.home), "OPENCODE_BIN": str(self.stub)}
        return subprocess.run(
            ["bash", str(DOCTOR), *args], env=env, text=True,
            capture_output=True, timeout=60,
        )

    # --- el punto ciego original ---

    def test_tui_tsx_en_subdirectorio_se_detecta(self) -> None:
        self.write_plugin("uso/tui.tsx",
                          'import { Plugin } from "@opencode/plugin/tui"\n'
                          'context.data.on("session.execution.succeeded", () => {})\n')
        done = self.run_doctor()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("plugins detectados: 1", done.stdout)
        self.assertIn("TUI: 1", done.stdout)
        self.assertIn("uso/tui.tsx", done.stdout)

    def test_no_afirma_sano_sin_comprobar_superficie(self) -> None:
        # Un plugin TUI cuya API desaparecio del binario debe fallar, no pasar.
        self.write_plugin("roto/tui.tsx",
                          'import { Plugin } from "@opencode/plugin/tui"\n'
                          'context.data.on("evento.que.brilla", () => {})\n')
        done = self.run_doctor()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("DRIFT", done.stdout)
        self.assertIn("evento.que.brilla", done.stdout)
        self.assertNotIn("[ok] 1 tokens de superficie", done.stdout)

    def test_token_presente_no_prueba_renderizado(self) -> None:
        self.write_plugin("uso/tui.tsx",
                          'import { Plugin } from "@opencode/plugin/tui"\n'
                          'context.data.on("session.execution.succeeded", () => {})\n')
        done = self.run_doctor()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("no prueba el renderizado", done.stdout)

    # --- honestidad en los bordes ---

    def test_plugin_sin_superficie_no_se_declara_sano(self) -> None:
        self.write_plugin("vacio/tui.tsx", "export default {}\n")
        done = self.run_doctor()
        self.assertIn("sin superficie reconocible", done.stdout)
        self.assertIn("no se puede afirmar que este plugin este sano", done.stdout)
        self.assertNotIn("[ok] 0 tokens", done.stdout)

    def test_tsx_sin_import_tui_no_se_clasifica_como_servidor(self) -> None:
        self.write_plugin("raro/principal.tsx", "export default {}\n")
        done = self.run_doctor()
        self.assertIn("TUI: 1", done.stdout)
        self.assertNotIn("servidor: 1", done.stdout)

    def test_sin_plugins_no_inventa_hooks(self) -> None:
        done = self.run_doctor()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("plugins detectados: 0", done.stdout)
        self.assertIn("(sin plugins en", done.stdout)
        self.assertNotIn("todos los hooks encontrados", done.stdout)

    def test_extensiones_reconocidas_en_anidamiento_profundo(self) -> None:
        for rel in ("a/b/c/x.js", "d/e/y.mjs", "f/z.cjs", "g/h/w.ts", "i/j/v.tsx"):
            self.write_plugin(rel, "export default {}\n")
        done = self.run_doctor()
        self.assertIn("plugins detectados: 5", done.stdout)

    def test_hooks_de_servidor_seguyen_funcionando(self) -> None:
        self.write_plugin("serv/index.js", 'export default { "tool.execute.before": 1 }\n')
        done = self.run_doctor()
        self.assertIn("tool.execute.before", done.stdout)
        self.assertIn("hooks en uso (plugins de servidor)", done.stdout)

    def test_no_binary_no_afirma_verificacion_de_superficie(self) -> None:
        self.write_plugin("uso/tui.tsx",
                          'import { Plugin } from "@opencode/plugin/tui"\n'
                          'context.data.on("session.execution.succeeded", () => {})\n')
        done = self.run_doctor("--no-binary")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertNotIn("tokens de superficie", done.stdout)

    # --- contrato que no debe cambiar ---

    def test_deriva_de_pin_sigue_fallando(self) -> None:
        self.pin.write_text("opencode v2.0.98\n", encoding="utf-8")
        self.write_plugin("uso/tui.tsx",
                          'import { Plugin } from "@opencode/plugin/tui"\n'
                          'context.data.on("session.execution.succeeded", () => {})\n')
        done = self.run_doctor()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("VERSION DISTINTA", done.stdout)

    def test_pin_sigue_escribiendo_version(self) -> None:
        self.pin.write_text("opencode v2.0.00\n", encoding="utf-8")
        done = self.run_doctor("pin")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("version pineada: opencode v2.0.99", done.stdout)
        self.assertEqual(self.pin.read_text(encoding="utf-8"), "opencode v2.0.99\n")

    def test_opcion_desconocida_sigue_siendo_error_2(self) -> None:
        done = self.run_doctor("--no-existe")
        self.assertEqual(done.returncode, 2)
        self.assertIn("opcion desconocida", done.stderr)

    def test_no_imprime_contenido_de_plugins(self) -> None:
        secreto = "SEGRETO_EN_PLUGIN_NO_DEBE_APARECER"
        self.write_plugin("uso/tui.tsx",
                          f'import {{ Plugin }} from "@opencode/plugin/tui"\n'
                          f'// {secreto}\n'
                          f'context.data.on("session.execution.succeeded", () => {{}})\n')
        done = self.run_doctor()
        self.assertNotIn(secreto, done.stdout)
        self.assertNotIn(secreto, done.stderr)


class PluginDoctorLocationTests(unittest.TestCase):
    def test_script_esta_en_tools_no_en_el_repo(self) -> None:
        # Documenta por que este test no usa el script del repo: plugin_doctor
        # vive en ~/tools y este cambio requiere autorizacion aparte.
        self.assertTrue(str(DOCTOR).endswith("tools/plugin_doctor.sh"))
        repo_copy = Path(__file__).resolve().parents[2] / "tools" / "plugin_doctor.sh"
        self.assertFalse(repo_copy.exists())


if __name__ == "__main__":
    unittest.main()