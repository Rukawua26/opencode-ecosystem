"""Smoke test del frontend: el JS del panel debe parsear (node --check)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "web" / "index.html"


class TestFrontendJS(unittest.TestCase):
    def test_inline_script_parses(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node no disponible")
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("<script>", html)
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(script)
            tmp = f.name
        res = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"JS roto:\n{res.stderr}")

    def test_csrf_caducado_tiene_mensaje_de_reanudacion(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("Recarga la página", html)
        self.assertIn("csrfHint", html)

    def test_filtros_de_cola_presentes(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        for fid in ("f-status", "f-agent", "f-model", "f-sens",
                    "renderTasks", "taskDuration"):
            self.assertIn(fid, html)

    def test_accesibilidad_basica(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", html)
        self.assertIn(":focus-visible", html)
        self.assertIn('role="button"', html)
        self.assertIn('aria-live="polite"', html)


if __name__ == "__main__":
    unittest.main()
