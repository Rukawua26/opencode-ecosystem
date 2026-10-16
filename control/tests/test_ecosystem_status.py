"""Status aislado: compara archivos, no certifica horarios systemd."""
import shutil
import unittest

from control.tests import test_ecosystem_mutations as fixtures


class StatusTests(unittest.TestCase):
    run_cli = fixtures.MutationTests.run_cli
    fail_command = fixtures.MutationTests.fail_command

    def setUp(self):
        fixtures.MutationTests.setUp(self)
        for name in ("opencode.jsonc", "dcp.jsonc", "cron-jobs.json"):
            shutil.copy2(self.eco / "configs" / name, self.cfg / name)

    def test_equal(self):
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "[ok] sin drift\n")

    def test_cron_changed_or_missing(self):
        for side in (self.eco / "configs", self.cfg):
            target = side / "cron-jobs.json"
            original = target.read_text()
            for mode in ("changed", "missing"):
                with self.subTest(side=side, mode=mode):
                    if mode == "changed":
                        target.write_text("diferente")
                    else:
                        target.unlink()
                    result = self.run_cli("status")
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "[drift] cron-jobs.json\n")
                    target.write_text(original)

    def test_diff_error_is_not_healthy(self):
        self.fail_command("diff", 'exit 2')
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[drift] cron-jobs.json", result.stdout)
        self.assertNotIn("[ok]", result.stdout)

    def test_cron_missing_on_both_sides_is_not_healthy(self):
        (self.eco / "configs/cron-jobs.json").unlink()
        (self.cfg / "cron-jobs.json").unlink()
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "[drift] cron-jobs.json\n")

    def test_cron_directory_is_not_a_matching_file(self):
        target = self.cfg / "cron-jobs.json"
        target.unlink()
        target.mkdir()
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[drift] cron-jobs.json", result.stdout)

    def test_live_memory_and_backups_are_outside_coverage(self):
        (self.cfg / "memory/MEMORY.md").write_text("personal")
        (self.cfg / "commands/demo.md.bak-personal").write_text("backup")
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 0, result.stdout)
