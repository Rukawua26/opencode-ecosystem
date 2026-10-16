"""Guardarraíl de regresión de las reglas de permisos.

Motivo (2026-10-16): se comprobó con un canario que `read` denegaba `.env`
mientras `bash` seguía en `allow` y lo leía igual. Estas reglas son la defensa
real; si alguien edita el JSONC y las elimina, el test lo delata en lugar de
dejar documentado como protegido algo que ya no lo está.

Alcance: solo la configuración. No prueba que OpenCode ejecute la regla en
caliente (eso exigiría una ejecución real); evita su desaparición silenciosa.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent.parent / "configs" / "opencode.jsonc"


def load_permission() -> dict:
    """Carga el bloque `permission` del JSONC quitando comentarios de línea."""
    text = CONFIG.read_text(encoding="utf-8")
    # Solo líneas cuyo primer contenido es //: no toca // dentro de URLs.
    return json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M))["permission"]


class TestSecretosNoLegibles(unittest.TestCase):
    def setUp(self) -> None:
        self.perm = load_permission()

    def test_read_deniega_env_y_secrets(self) -> None:
        for regla in ("**/.env*", "**/secrets/**"):
            self.assertEqual(
                self.perm["read"].get(regla), "deny", f"read ya no deniega {regla}"
            )

    def test_edit_deniega_env(self) -> None:
        self.assertEqual(self.perm["edit"].get("**/.env*"), "deny")

    def test_read_conserva_las_reglas_previas(self) -> None:
        for regla in ("~/.ssh/*", "**/*.pem", "**/*.key"):
            self.assertEqual(
                self.perm["read"].get(regla), "deny", f"read perdio {regla}"
            )


class TestBashPideConfirmacion(unittest.TestCase):
    def setUp(self) -> None:
        self.bash = load_permission()["bash"]

    def test_bash_sigue_allow_por_defecto(self) -> None:
        self.assertEqual(self.bash.get("*"), "allow")

    def test_conserva_las_reglas_previas_de_red(self) -> None:
        for regla in ("ssh *", "scp *", "sftp *", "rsync *"):
            self.assertEqual(self.bash.get(regla), "ask", f"bash perdio {regla}")

    def test_lectura_de_secretos_pide_confirmacion(self) -> None:
        for regla in ("* .env*", "*/.env*", "*/secrets/*", "*/secrets/**"):
            self.assertEqual(
                self.bash.get(regla),
                "ask",
                f"bash ya no pide confirmacion en {regla}",
            )


if __name__ == "__main__":
    unittest.main()
