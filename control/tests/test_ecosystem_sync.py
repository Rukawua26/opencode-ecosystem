"""Contrato de sync/status del script `opencode-ecosystem` para la memoria de scripts.

Regresion (memoria-señal): `cmd_status` no detectaba drift en `memory/kairos.sh`
ni `memory/autodream.sh`, y `cmd_sync --apply` solo los copiaba si no existian.
Eso permitia "sin drift" con scripts divergidos. Este test fuerza esas dos
carencias con un HOME temporal y verifica el contrato tras el fix.

No toca la memoria viva real: todo corre bajo un HOME construido en /tmp.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # opencode-ecosystem


class EcosystemSyncContract(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="eco-sync-"))
        self.eco = self.home / "opencode-ecosystem"
        self.cfg = self.home / ".config" / "opencode"
        # Copia de la fuente del ecosistema al fake HOME (source de verdad).
        shutil.copytree(REPO, self.eco, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "*.pyc", "odd", "docs", "control", "README.md"))
        (self.eco / "opencode-ecosystem").chmod(
            (self.eco / "opencode-ecosystem").stat().st_mode | stat.S_IXUSR)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        return subprocess.run(
            [str(self.eco / "opencode-ecosystem"), *args],
            cwd=str(self.eco), env=env, text=True, capture_output=True,
        )

    def _sync(self) -> subprocess.CompletedProcess:
        return self._run("sync", "--apply")

    def _status(self) -> subprocess.CompletedProcess:
        return self._run("status")

    def test_sync_apply_instala_scripts_de_memoria(self) -> None:
        r = self._sync()
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("kairos.sh", "autodream.sh"):
            self.assertEqual(
                (self.cfg / "memory" / name).read_text(),
                (self.eco / "memory" / name).read_text(),
                f"{name} no quedó igual a la fuente",
            )
        self.assertTrue(os.access(self.cfg / "memory" / "kairos.sh", os.X_OK))

    def test_status_detecta_drift_en_scripts_de_memoria(self) -> None:
        self._sync()
        # Simula el bug: runtime diverge de la fuente sin pasar por sync.
        (self.cfg / "memory" / "kairos.sh").write_text(
            "# kairos.sh viejo y divergido\n", encoding="utf-8")
        r = self._status()
        self.assertNotEqual(r.returncode, 0, "debe reportar drift")
        self.assertIn("[drift] memory/kairos.sh", r.stdout)

    def test_status_detecta_drift_autodream(self) -> None:
        self._sync()
        (self.cfg / "memory" / "autodream.sh").write_text(
            "# autodream.sh viejo y divergido\n", encoding="utf-8")
        r = self._status()
        self.assertNotEqual(r.returncode, 0, "debe reportar drift")
        self.assertIn("[drift] memory/autodream.sh", r.stdout)

    def test_sync_corrige_drift_y_hace_backup(self) -> None:
        self._sync()
        (self.cfg / "memory" / "kairos.sh").write_text(
            "# kairos.sh viejo\n", encoding="utf-8")
        r = self._sync()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            (self.cfg / "memory" / "kairos.sh").read_text(),
            (self.eco / "memory" / "kairos.sh").read_text(),
        )
        # Quedó un backup con fecha.
        backups = list((self.cfg / "memory").glob("kairos.sh.bak-*"))
        self.assertTrue(backups, "sync debe dejar backup reversible")

    def test_status_sin_drift_tras_sync(self) -> None:
        self._sync()
        r = self._status()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[ok] sin drift", r.stdout)

    def test_memory_md_no_se_sobrescribe(self) -> None:
        self._sync()
        target = self.cfg / "memory" / "MEMORY.md"
        target.write_text("# MEMORY.md vivo, edicion del usuario\n", encoding="utf-8")
        self._sync()
        self.assertEqual(
            target.read_text(), "# MEMORY.md vivo, edicion del usuario\n",
            "sync no debe sobrescribir la memoria viva",
        )

    def test_topics_y_logs_no_se_tocan(self) -> None:
        self._sync()
        topics = self.cfg / "memory" / "topics"
        self.assertFalse(topics.exists(), "sync no debe sembrar memoria personal")
        topics.mkdir()
        (topics / "decisiones.md").write_text("# decisiones\n", encoding="utf-8")
        r = self._sync()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((topics / "decisiones.md").exists())


if __name__ == "__main__":
    unittest.main()
