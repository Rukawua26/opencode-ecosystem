"""Pruebas aisladas del lanzador, sin consultar el runtime real."""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
LOADER = importlib.machinery.SourceFileLoader("checked_launcher", str(ROOT / "opencode-checked"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
launcher = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pin = Path(self.temp.name) / "pin"
        self.pin.write_text("opencode v2.0.0\n")

    def check(self, current="opencode v2.0.1", answer="n\n", interactive=True, error=None):
        def probe(*args, **kwargs):
            if error:
                raise error
            parsed = launcher.version(current)
            if not parsed:
                raise ValueError("version invalida")
            return parsed
        output = io.StringIO()
        with patch.object(launcher, "probe_version", side_effect=probe), patch.object(launcher.sys, "stdin", io.StringIO(answer)), contextlib.redirect_stderr(output):
            launcher.check("fake", self.pin, interactive)
        return output.getvalue()

    def test_match_silent(self):
        self.assertEqual(self.check("2.0.0"), "")

    def test_reject(self):
        self.assertIn("sin adaptar", self.check())

    def test_accept_only_review(self):
        output = self.check(answer="s\n")
        self.assertIn("NO recibe", output)
        self.assertIn("no hagas cambios", output)

    def test_unknown_and_eof_reject(self):
        for answer in ("yes\n", "", "quizas\n"):
            self.assertIn("Sin autorizacion", self.check(answer=answer))

    def test_no_tty_never_reads(self):
        with patch.object(launcher.sys, "stdin") as stdin, contextlib.redirect_stderr(io.StringIO()), patch.object(launcher, "probe_version", return_value="2.0.1"):
            launcher.check("fake", self.pin, False)
            stdin.readline.assert_not_called()

    def test_missing_and_invalid_pin(self):
        self.pin.unlink()
        self.assertIn("Pin ausente o invalido", self.check())
        self.pin.write_text("?" * 400)
        self.assertIn("Pin ausente o invalido", self.check())

    def test_failed_probe(self):
        for error in (OSError(), subprocess.TimeoutExpired("fake", 3)):
            self.assertIn("No se pudo comprobar", self.check(error=error))
        self.assertIn("No se pudo comprobar", self.check(current="bad\x1b[0m"))

    def test_nonzero_probe(self):
        fake = self.fake_binary('print("2.0.0")\nsys.exit(1)')
        with self.assertRaises(ValueError):
            launcher.probe_version(str(fake))

    def fake_binary(self, body):
        fake = Path(self.temp.name) / "probe"
        fake.write_text("#!/usr/bin/env python3\nimport os, sys, time\n" + body + "\n")
        fake.chmod(0o755)
        return fake

    def test_probe_output_is_bounded_without_tempfile(self):
        fake = self.fake_binary('while True: os.write(1, b"x" * 1048576)')
        with patch.object(tempfile, "TemporaryFile", side_effect=AssertionError("no disk capture")), patch.object(launcher.os, "read", wraps=os.read) as read:
            with self.assertRaises(ValueError):
                launcher.probe_version(str(fake))
            # Popen tambien lee su pipe de errores de exec (vacio en este caso).
            self.assertEqual(read.call_args_list[-1].args[1], 257)

    def test_probe_success(self):
        fake = self.fake_binary('print("opencode v2.0.0")')
        self.assertEqual(launcher.probe_version(str(fake)), "2.0.0")

    def test_probe_deadline_with_open_stdout(self):
        fake = self.fake_binary('os.write(1, b"2.0.0")\ntime.sleep(20)')
        with self.assertRaises(subprocess.TimeoutExpired):
            launcher.probe_version(str(fake))

    def test_input_errors_still_exec_without_consent(self):
        for error in (OSError("private detail"), UnicodeError("private detail")):
            with self.subTest(error=type(error).__name__), patch.dict(os.environ, {}, clear=True), patch.object(launcher.shutil, "which", return_value="/fake/opencode"), patch.object(launcher.Path, "home", return_value=Path(self.temp.name)), patch.object(launcher, "probe_version", return_value="2.0.1"), patch.object(launcher.sys, "stdin") as stdin, patch.object(launcher.sys, "stderr", new_callable=io.StringIO) as output, patch.object(launcher.os, "execve") as execute:
                pin = Path(self.temp.name) / ".config/opencode/.opencode-version.pin"
                pin.parent.mkdir(parents=True, exist_ok=True)
                pin.write_text("2.0.0")
                stdin.isatty.return_value = True
                stdin.readline.side_effect = error
                with patch.object(output, "isatty", return_value=True):
                    launcher.main([])
                execute.assert_called_once()
                stdin.readline.assert_called_once_with(80)
                self.assertEqual(execute.call_args.args[1], ["/fake/opencode"])
                self.assertIn("Sin autorizacion", output.getvalue())
                self.assertNotIn("Revision aceptada", output.getvalue())
                self.assertNotIn("private detail", output.getvalue())

    def test_args_and_exec(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(launcher.shutil, "which", return_value="/fake/opencode"), patch.object(launcher, "check") as check, patch.object(launcher.os, "execve") as execute:
            for args in (["run", "a b"], ["--help"], ["--version"], ["a b"]):
                launcher.main(args)
                self.assertFalse(check.call_args.args[2])
                self.assertEqual(execute.call_args.args[1], ["/fake/opencode", *args])

    def test_recursion_and_missing_binary(self):
        with contextlib.redirect_stderr(io.StringIO()), patch.object(launcher.shutil, "which", return_value=str(ROOT / "opencode-checked")):
            self.assertEqual(launcher.main([]), 126)
        with contextlib.redirect_stderr(io.StringIO()), patch.object(launcher.shutil, "which", return_value=None):
            self.assertEqual(launcher.main([]), 127)
        with patch.dict(os.environ, {"OPENCODE_CHECKED_ACTIVE": "1"}), contextlib.redirect_stderr(io.StringIO()), patch.object(launcher.shutil, "which", return_value="/fake/opencode"):
            self.assertEqual(launcher.main([]), 126)

    def test_real_exit_and_arguments(self):
        fake = Path(self.temp.name) / "fake"
        fake.write_text('#!/usr/bin/env python3\nimport sys\nif sys.argv[1:] == ["--version"]: print("2.0.0")\nelse: sys.exit(37 if sys.argv[1:] == ["run", "a b"] else 99)\n')
        fake.chmod(0o755)
        env = {**os.environ, "HOME": self.temp.name, "OPENCODE_BIN": str(fake)}
        env.pop("OPENCODE_CHECKED_ACTIVE", None)
        result = subprocess.run([str(ROOT / "opencode-checked"), "run", "a b"], env=env, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 37)
