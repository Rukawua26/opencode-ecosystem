"""Operaciones mutantes aisladas: nunca usan el HOME instalado."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "opencode-ecosystem"


class MutationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ecosystem-", dir="/tmp/opencode")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.eco = self.home / "opencode-ecosystem"
        self.cfg = self.home / ".config/opencode"
        self.bin = self.home / "bin"
        self.bin.mkdir()
        for base in (self.eco, self.cfg):
            for directory in ("skills/demo", "scripts", "commands", "memory"):
                (base / directory).mkdir(parents=True)
            (base / "skills/demo/SKILL.md").write_text(
                "---\nname: demo\ndescription: Prueba. Usar cuando se verifica.\n---\nContenido.\n")
            (base / "scripts/demo.sh").write_text("#!/bin/sh\nexit 0\n")
            (base / "commands/demo.md").write_text("comando\n")
            for name in ("kairos.sh", "autodream.sh", "MEMORY.md"):
                (base / "memory" / name).write_text("original " + name)
        (self.eco / "configs").mkdir()
        for name in ("opencode.jsonc", "dcp.jsonc", "cron-jobs.json"):
            (self.eco / "configs" / name).write_text("fuente " + name)
            (self.cfg / name).write_text("runtime " + name)
        shutil.copy2(ROOT / "validate-skills.py", self.eco)
        self.manifest = self.cfg / ".ecosystem-managed-files"
        self.manifest.write_text("opencode/opencode.jsonc\nopencode/memory/MEMORY.md\n")

    def run_cli(self, *args):
        env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        return subprocess.run(["bash", str(CLI), *args], env=env, text=True,
                              capture_output=True, timeout=15)

    def fail_command(self, name, condition):
        real = shutil.which(name)
        stub = self.bin / name
        stub.write_text(f'#!/bin/bash\n{condition}\nexec "{real}" "$@"\n')
        stub.chmod(0o755)

    def assert_failed(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("sync aplicado", result.stdout)
        self.assertNotIn("publish aplicado", result.stdout)

    def test_sync_preserves_memory_and_excludes_manifest(self):
        personal = self.cfg / "node_modules/.bin"
        personal.mkdir(parents=True)
        (personal / "tool").symlink_to("../tool/bin")
        (self.cfg / "scripts/personal.sh").write_text("privado")
        (self.cfg / "scripts/personal.sh").chmod(0o600)
        (self.cfg / "scripts/personal-link.sh").symlink_to("../privado")
        self.fail_command("find", '[[ "$1" == */.config/opencode ]] && exit 73')
        result = self.run_cli("sync", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((personal / "tool").readlink(), Path("../tool/bin"))
        self.assertEqual((self.cfg / "scripts/personal-link.sh").readlink(), Path("../privado"))
        self.assertEqual((self.cfg / "scripts/personal.sh").read_text(), "privado")
        self.assertEqual((self.cfg / "scripts/personal.sh").stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.cfg / "memory/MEMORY.md").read_text(), "original MEMORY.md")
        self.assertNotIn("MEMORY.md", self.manifest.read_text())

    def test_old_manifest_never_deletes_live_memory(self):
        result = self.run_cli("uninstall", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.cfg / "memory/MEMORY.md").exists())
        self.assertEqual((self.cfg / "memory/MEMORY.md").read_text(), "original MEMORY.md")
        self.assertFalse((self.cfg / "opencode.jsonc").exists())
        self.assertTrue(list(self.cfg.glob(".pre-uninstall-*/opencode/opencode.jsonc")))

    def test_manifest_paths_fail_before_any_delete(self):
        for bad in ("opencode/../outside", "/tmp/outside", "opencode/memory/topics/note.md",
                    "opencode/scripts/../../outside.sh", "opencode/skills/demo/extra/SKILL.md",
                    "opencode/.env", "opencode/memory/observations.log"):
            with self.subTest(path=bad):
                self.manifest.write_text("opencode/opencode.jsonc\n" + bad + "\n")
                self.assert_failed(self.run_cli("uninstall", "--apply"))
                self.assertTrue((self.cfg / "opencode.jsonc").exists())

    def test_symlink_parent_is_not_followed(self):
        outside = self.home / "outside"
        outside.mkdir()
        (outside / "demo.sh").write_text("privado")
        shutil.rmtree(self.cfg / "scripts")
        (self.cfg / "scripts").symlink_to(outside, target_is_directory=True)
        self.manifest.write_text("opencode/scripts/demo.sh\n")
        for args in (("uninstall", "--apply"), ("sync", "--apply"), ("publish", "--yes")):
            self.assert_failed(self.run_cli(*args))
            self.assertEqual((outside / "demo.sh").read_text(), "privado")

    def test_sync_backup_failure_does_not_overwrite(self):
        self.fail_command("cp", '[[ "$1" == -a ]] && exit 73')
        self.assert_failed(self.run_cli("sync", "--apply"))
        self.assertEqual((self.cfg / "opencode.jsonc").read_text(), "runtime opencode.jsonc")

    def test_directory_config_is_not_a_successful_copy(self):
        for command, destination in (("sync", self.cfg), ("publish", self.eco / "configs")):
            with self.subTest(command=command):
                target = destination / "opencode.jsonc"
                target.unlink()
                target.mkdir()
                self.assert_failed(self.run_cli(command, "--apply" if command == "sync" else "--yes"))
                self.assertEqual(list(target.iterdir()), [])
                target.rmdir()
                target.write_text("restaurado")

    def test_uninstall_backup_failure_does_not_delete(self):
        self.fail_command("cp", 'exit 73')
        self.assert_failed(self.run_cli("uninstall", "--apply"))
        self.assertTrue((self.cfg / "opencode.jsonc").exists())

    def test_sync_copy_failure_is_not_success(self):
        self.fail_command("cp", '[[ "$1" == *configs/opencode.jsonc ]] && exit 73')
        self.assert_failed(self.run_cli("sync", "--apply"))
        self.assertEqual((self.cfg / "opencode.jsonc").read_text(), "runtime opencode.jsonc")

    def test_sync_seed_copy_failure_is_not_success(self):
        (self.cfg / "memory/MEMORY.md").unlink()
        self.fail_command("cp", '[[ "$1" == */memory/MEMORY.md ]] && exit 73')
        self.assert_failed(self.run_cli("sync", "--apply"))

    def test_sync_manifest_failure_is_not_success(self):
        self.manifest.unlink()
        self.manifest.mkdir()
        self.assert_failed(self.run_cli("sync", "--apply"))

    def test_uninstall_remove_failure_is_not_success(self):
        self.fail_command("rm", 'exit 73')
        self.assert_failed(self.run_cli("uninstall", "--apply"))
        self.assertTrue((self.cfg / "opencode.jsonc").exists())

    def test_symlink_manifest_is_not_followed(self):
        outside = self.home / "outside-manifest"
        outside.write_text("opencode/opencode.jsonc\n")
        self.manifest.unlink()
        self.manifest.symlink_to(outside)
        self.assert_failed(self.run_cli("uninstall", "--apply"))
        self.assertTrue((self.cfg / "opencode.jsonc").exists())

    def test_sync_symlink_memory_is_not_followed(self):
        outside = self.home / "outside-memory"
        outside.write_text("privado")
        (self.cfg / "memory/MEMORY.md").unlink()
        (self.cfg / "memory/MEMORY.md").symlink_to(outside)
        self.assert_failed(self.run_cli("sync", "--apply"))
        self.assertEqual(outside.read_text(), "privado")

    def test_publish_preparation_failure_preserves_skills(self):
        original = (self.eco / "skills/demo/SKILL.md").read_text()
        self.fail_command("cp", '[[ "$1" == -r ]] && exit 73')
        self.assert_failed(self.run_cli("publish", "--yes"))
        self.assertEqual((self.eco / "skills/demo/SKILL.md").read_text(), original)
        self.assertFalse(list(self.eco.glob(".publish-*")))

    def test_publish_validates_prepared_copy(self):
        self.fail_command("cp", 'if [[ "$1" == -r ]]; then mkdir -p "$3/demo"; echo invalid > "$3/demo/SKILL.md"; exit 0; fi')
        self.assert_failed(self.run_cli("publish", "--yes"))
        self.assertIn("name: demo", (self.eco / "skills/demo/SKILL.md").read_text())

    def test_publish_config_failure_is_not_success(self):
        self.fail_command("cp", '[[ "$1" == *dcp.jsonc ]] && exit 73')
        self.assert_failed(self.run_cli("publish", "--yes"))
        self.assertIn("name: demo", (self.eco / "skills/demo/SKILL.md").read_text())

    def test_publish_replacement_failure_rolls_back(self):
        self.fail_command("mv", '[[ "$1" == */.publish-*/skills ]] && exit 73')
        self.assert_failed(self.run_cli("publish", "--yes"))
        self.assertIn("name: demo", (self.eco / "skills/demo/SKILL.md").read_text())
        self.assertFalse(list(self.eco.glob(".publish-*")))

    def test_publish_failed_rollback_keeps_original_for_recovery(self):
        self.fail_command("mv", '[[ "$1" == */.publish-*/* ]] && exit 73')
        result = self.run_cli("publish", "--yes")
        self.assert_failed(result)
        backups = list(self.eco.glob(".publish-*/original/demo/SKILL.md"))
        self.assertEqual(len(backups), 1)
        self.assertIn("name: demo", backups[0].read_text())
        self.assertIn("restaurar skills desde", result.stderr)

    def test_publish_success_preserves_memory(self):
        result = self.run_cli("publish", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.eco / "configs/dcp.jsonc").read_text(), "runtime dcp.jsonc")
        self.assertEqual((self.eco / "memory/MEMORY.md").read_text(), "original MEMORY.md")
        self.assertFalse(list(self.eco.glob(".publish-*")))


if __name__ == "__main__":
    unittest.main()
