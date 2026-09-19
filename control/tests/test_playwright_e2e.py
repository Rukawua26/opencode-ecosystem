"""Smoke E2E del panel con Playwright + Chromium del sistema.

Opcional: se salta si no hay playwright, chromium o el servicio no responde.
No muta nada: solo GETs, filtros y apertura del historial.
"""

from __future__ import annotations

import os
import socket
import unittest

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - entorno sin playwright
    sync_playwright = None

URL = "http://127.0.0.1:8765"
CHROMIUM = "/usr/bin/chromium"


def _panel_up() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8765), timeout=1):
            return True
    except OSError:
        return False


@unittest.skipUnless(
    sync_playwright and os.path.exists(CHROMIUM) and _panel_up(),
    "requiere playwright + /usr/bin/chromium + panel activo en 127.0.0.1:8765",
)
class TestPanelE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._pw = sync_playwright().start()
        cls.browser = cls._pw.chromium.launch(
            headless=True, executable_path=CHROMIUM, args=["--no-sandbox"]
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls._pw.stop()

    def _page(self):
        page = self.browser.new_page()
        self.console_errors: list[str] = []
        self.not_found: list[str] = []
        page.on("console", lambda m: self.console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("response", lambda r: self.not_found.append(r.url)
                if r.status == 404 else None)
        page.goto(URL, wait_until="networkidle")
        return page

    def test_carga_y_salud(self) -> None:
        page = self._page()
        self.assertEqual(page.title(), "Control del ecosistema OpenCode")
        self.assertGreater(page.locator("section.panel").count(), 4)
        self.assertIn("sano", page.locator("#health-pill").inner_text())
        self.assertEqual(self.console_errors, [])
        self.assertEqual(self.not_found, [])
        page.close()

    def test_filtros_e_historial(self) -> None:
        page = self._page()
        total = page.locator(".comp").count()
        page.locator("button.chip").filter(has_text="skill").first.click()
        skills = page.locator(".comp").count()
        self.assertGreater(total, skills)
        self.assertGreater(skills, 0)
        page.locator(".comp").first.click()
        self.assertTrue(page.locator("#hist-modal").is_visible())
        page.keyboard.press("Escape")
        self.assertFalse(page.locator("#hist-modal").is_visible())
        page.close()

    def test_movil_sin_overflow(self) -> None:
        page = self._page()
        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="networkidle")
        overflow = page.evaluate(
            "document.documentElement.scrollWidth"
            " > document.documentElement.clientWidth"
        )
        self.assertFalse(overflow)
        page.close()


if __name__ == "__main__":
    unittest.main()
