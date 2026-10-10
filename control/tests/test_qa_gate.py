import contextlib
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "scripts" / "qa-gate.sh"


class QaGateTests(unittest.TestCase):
    def run_gate(self, files, initial=None, strict=False, staged=True, args=None,
                 git_fault=None, subdir=None, object_format=None, git_env=None):
        """Ejecuta el gate en un repo temporal; devuelve codigo y salida combinada."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_args = ["git", "init", "-q"]
            if object_format:
                init_args.append("--object-format=" + object_format)
            subprocess.run(init_args, cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            for contents, commit in ((initial or {}, True), (files, False)):
                for name, content in contents.items():
                    path = repo / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if content is None:
                        path.unlink()
                    elif isinstance(content, bytes):
                        path.write_bytes(content)
                    else:
                        path.write_text(content)
                if (commit and contents) or (not commit and staged):
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                if commit and contents:
                    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            env = os.environ.copy()
            env.update(git_env or {})
            if git_fault:
                command, code, output, error = git_fault
                bin_dir = repo / "fake-bin"
                bin_dir.mkdir()
                fake_git = bin_dir / "git"
                fake_git.write_text(
                    f"#!{sys.executable}\nimport os, sys\n"
                    f"if {command!r} in sys.argv:\n"
                    f"    sys.stdout.buffer.write({output!r})\n"
                    f"    sys.stderr.buffer.write({error!r})\n"
                    f"    sys.exit({code})\n"
                    f"os.execv({shutil.which('git')!r}, ['git'] + sys.argv[1:])\n"
                )
                fake_git.chmod(0o755)
                env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
            argv = [str(GATE)] + (args if args is not None else (["--strict"] if strict else []))
            cwd = repo / subdir if subdir else repo
            cwd.mkdir(parents=True, exist_ok=True)
            done = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, env=env)
            return done.returncode, done.stdout + done.stderr

    def synthetic_secrets(self):
        return ("AKIA" + "A" * 16, "ghp_" + "b" * 36, "sk-" + "c" * 32,
                 "-----BEGIN " + "PRIVATE KEY-----", "https://" + "user:password@example.invalid")

    def test_inherited_shell_options_do_not_leak_or_change_exit_codes(self):
        secret = self.synthetic_secrets()[0]
        for options in ("xtrace", "verbose", "errexit", "errexit:verbose:xtrace"):
            for mode in ("invalid", "invalid-strict", "warn", "strict"):
                with self.subTest(options=options, mode=mode):
                    args = {"invalid": [secret], "invalid-strict": ["--strict", secret],
                            "warn": [], "strict": ["--strict"]}[mode]
                    code, output = self.run_gate({}, initial={".env": "safe\n"}, staged=False,
                                                 args=args, git_env={"SHELLOPTS": options})
                    expected = 2 if mode.startswith("invalid") else int(mode == "strict")
                    # No assertNotIn/assertIn con stdout: un fallo no debe volcarlo.
                    self.assertFalse(secret in output, "valor sintetico filtrado por startup")
                    self.assertFalse("import ast" in output, "verbose imprime el fuente embebido")
                    self.assertFalse("python3 - " in output, "startup imprime la invocacion Python")
                    self.assertEqual(code, expected)
                    label = "argumentos invalidos" if expected == 2 else ".env: fichero sensible rastreado"
                    self.assertTrue(label in output, "falta etiqueta segura del resultado")

    def test_git_environment_cannot_redirect_repo_or_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            alternate = Path(tmp)
            subprocess.run(["git", "init", "-q", "--object-format=sha1"], cwd=alternate, check=True)
            (alternate / "clean.txt").write_text("safe\n")
            subprocess.run(["git", "add", "-A"], cwd=alternate, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "clean"], cwd=alternate, check=True)
            variants = (
                {"GIT_DIR": str(alternate / ".git"), "GIT_WORK_TREE": str(alternate)},
                {"GIT_INDEX_FILE": str(alternate / ".git" / "index")},
                {"GIT_DIR": str(alternate / ".git"), "GIT_COMMON_DIR": str(alternate / ".git"),
                 "GIT_WORK_TREE": str(alternate), "GIT_INDEX_FILE": str(alternate / ".git" / "index")},
            )
            for env in variants:
                for subdir in (None, "nested/deep"):
                    for strict in (False, True):
                        with self.subTest(variables=tuple(env), subdir=subdir, strict=strict):
                            code, output = self.run_gate({}, initial={".env": "safe\n"}, staged=False,
                                                         strict=strict, subdir=subdir, object_format="sha1", git_env=env)
                            self.assertEqual(code, int(strict))
                            self.assertIn(".env: fichero sensible rastreado", output)
                            self.assertIn("staged: no aplicable", output)
                            self.assertNotIn(str(alternate), output)
                            self.assertNotIn("clean.txt", output)

    def test_git_environment_configuration_cannot_change_queries(self):
        secret = self.synthetic_secrets()[0]
        variants = (
            {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "diff.orderFile", "GIT_CONFIG_VALUE_0": secret},
            {"GIT_CONFIG_PARAMETERS": f"'diff.orderFile={secret}'"},
            {"GIT_CONFIG_COUNT": "invalid-count"},
        )
        for env in variants:
            for strict in (False, True):
                with self.subTest(variables=tuple(env), strict=strict):
                    code, output = self.run_gate({"app.py": "value = eval(input())\n"}, strict=strict, git_env=env)
                    self.assertEqual(code, 0)
                    self.assertIn("app.py:1: eval", output)
                    self.assertNotIn(secret, output)

    def test_git_environment_cannot_invent_repository_for_nonrepo_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            alternate = Path(tmp) / "alternate"
            outside = Path(tmp) / "outside"
            alternate.mkdir()
            outside.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=alternate, check=True)
            env = {**os.environ, "GIT_DIR": str(alternate / ".git"), "GIT_WORK_TREE": str(alternate)}
            for strict in (False, True):
                done = subprocess.run([str(GATE)] + (["--strict"] if strict else []),
                                      cwd=outside, env=env, text=True, capture_output=True)
                self.assertEqual(done.returncode, 2)
                self.assertIn("error operativo", done.stdout)
                self.assertNotIn(str(alternate), done.stdout + done.stderr)

    def test_logs_todos_and_secrets_never_print_source(self):
        for strict in (False, True):
            for secret in self.synthetic_secrets():
                with self.subTest(strict=strict, family=secret[:4]):
                    code, output = self.run_gate({"app.js": f"console.log('{secret}'); // TODO marker-source\n"}, strict=strict)
                    self.assertEqual(code, int(strict))
                    self.assertIn("app.js:1:", output)
                    self.assertIn("posible secreto", output)
                    self.assertIn("console.log", output)
                    self.assertIn("TODO", output)
                    self.assertNotIn(secret, output)
                    self.assertNotIn("marker-source", output)

    def test_double_plus_lines_are_checked_by_all_rules(self):
        secret = self.synthetic_secrets()[0]
        catch = "catch (e) " + "{}"
        code, output = self.run_gate({"app.js": f"+console.log('{secret}'); // FIXME\n+{catch}\n"}, strict=True)
        self.assertEqual(code, 1)
        for label in ("posible secreto", "catch vacío", "console.log", "FIXME"):
            self.assertIn(label, output)
        self.assertNotIn(secret, output)

    def test_git_errors_are_operational_in_both_modes(self):
        secret = self.synthetic_secrets()[1]
        for command in ("diff", "ls-files"):
            for strict in (False, True):
                with self.subTest(command=command, strict=strict):
                    code, output = self.run_gate({}, strict=strict, git_fault=(command, 128, secret.encode(), secret.encode()))
                    self.assertEqual(code, 2)
                    self.assertIn("error operativo", output)
                    self.assertNotIn(secret, output)

    def test_outside_git_repository_is_not_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args in ([], ["--strict"]):
                done = subprocess.run([str(GATE)] + args, cwd=tmp, text=True, capture_output=True)
                self.assertEqual(done.returncode, 2)
                self.assertNotIn("fatal:", done.stdout + done.stderr)

    def test_invalid_arguments_fail_without_echoing_them(self):
        secret = self.synthetic_secrets()[2]
        for args in ([secret], ["--strict", secret], ["--warn"]):
            code, output = self.run_gate({}, args=args)
            self.assertEqual(code, 2)
            self.assertNotIn(secret, output)

    def test_no_staged_is_explicit_and_does_not_scan_working_tree(self):
        code, output = self.run_gate({"app.js": "console.log('unstaged-marker');\n"}, staged=False, strict=True)
        self.assertEqual(code, 0)
        self.assertIn("staged: no aplicable", output)
        self.assertNotIn("console.log", output)
        self.assertNotIn("unstaged-marker", output)

    def test_sensitive_tracked_paths_checked_without_staged(self):
        for name in (".env", "nested/.env.local", "cert.pem", "cert.key", "nested/id_rsa"):
            for strict in (False, True):
                with self.subTest(name=name, strict=strict):
                    code, output = self.run_gate({}, initial={name: "safe\n"}, staged=False, strict=strict)
                    self.assertEqual(code, int(strict))
                    self.assertIn("staged: no aplicable", output)
                    self.assertIn("fichero sensible rastreado", output)
                    self.assertIn(name, output)

    def test_quoted_and_control_paths_are_safe_and_keep_locations(self):
        for name in ('dir b/space name.py', 'café.py', 'quote".py', 'tab\tname.py', 'new\nname.py', 'escape\x1b.py', 'back\\slash.py'):
            with self.subTest(name=name):
                code, output = self.run_gate({name: "value = eval(input())\n"}, strict=True)
                self.assertEqual(code, 0)
                self.assertIn(name.encode("unicode_escape").decode("ascii") + ":1: eval", output)
                self.assertNotIn("\x1b", output)

    def test_secret_like_paths_are_redacted_in_every_report(self):
        secret = self.synthetic_secrets()[0]
        code, output = self.run_gate({secret + ".pem": "value = eval(input())\nconsole.log('safe'); // TODO\n"}, strict=True)
        self.assertEqual(code, 1)
        self.assertNotIn(secret, output)
        self.assertIn("[redactado].pem:1: eval", output)
        self.assertIn("fichero sensible rastreado", output)

    def test_binary_staged_is_incomplete_not_green(self):
        for strict in (False, True):
            code, output = self.run_gate({"blob.bin": b"\x00binary\xff\n"}, strict=strict)
            self.assertEqual(code, 2)
            self.assertIn("binario", output)

    def test_incomplete_or_invalid_diff_never_approves(self):
        diffs = (b"diff --git a/app.py b/app.py\n--- /dev/null\n+++ b/app.py\n@@ -0,0 +1,2 @@\n+safe\n",
                 b"diff --git a/app.py b/app.py\n+++ b/app.py\n+orphan\n",
                 b"arbitrary raw code\n", b"diff --git a/app.py b/app.py\n",
                 b"diff --git a/app.py b/app.py\nindex 123..456 100644\n",
                 b"diff --git a/app.py b/app.py\nold mode 100644\n",
                 b"diff --git a/app.py b/app.py\nindex 123..456 100644\n--- a/app.py\n+++ b/app.py\n",
                 b"diff --git a/app.py b/app.py\nindex 123..456 100644\n--- /dev/null\n+++ \"invalid-path-source\n")
        for diff in diffs:
            for strict in (False, True):
                with self.subTest(diff_kind=diff[:12], strict=strict):
                    code, output = self.run_gate({}, strict=strict, git_fault=("diff", 0, diff, b""))
                    self.assertEqual(code, 2)
                    self.assertNotIn("arbitrary raw code", output)
                    self.assertNotIn("invalid-path-source", output)

    def test_incomplete_tracked_paths_never_approves(self):
        code, output = self.run_gate({}, git_fault=("ls-files", 0, b"unterminated.pem", b""))
        self.assertEqual(code, 2)

    def test_presentation_cap_does_not_skip_late_blocker(self):
        secret = self.synthetic_secrets()[0]
        source = "console.log('presentation-marker');\n" * 80 + f"value = '{secret}'\n"
        code, output = self.run_gate({"app.js": source}, strict=True)
        self.assertEqual(code, 1)
        self.assertLess(len(output.splitlines()), 65)
        self.assertIn("omitidos", output)
        self.assertNotIn(secret, output)

    def test_warning_catalog_remains_nonblocking(self):
        source = "console.log(value); dbg!(value); println!(value); e.printStackTrace(); // TODO FIXME\n"
        code, output = self.run_gate({"app.js": source}, strict=True)
        self.assertEqual(code, 0)
        for label in ("console.log", "dbg!", "println!", "e.printStackTrace", "TODO", "FIXME"):
            self.assertIn(label, output)

    def test_external_exceptions_and_timeouts_are_safe(self):
        # Sin sleeps: ejercita el transporte real con fallo controlado de subprocess.
        source = GATE.read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        secret = self.synthetic_secrets()[0]
        errors = (subprocess.TimeoutExpired(secret, 15, output=secret, stderr=secret),
                  FileNotFoundError(secret), ValueError(secret), OSError(secret))
        for error in errors:
            for strict in (False, True):
                output = io.StringIO()
                with self.subTest(error_type=type(error).__name__, strict=strict):
                    with mock.patch.object(sys, "argv", [str(GATE)] + (["--strict"] if strict else [])), \
                         mock.patch.object(subprocess, "run", side_effect=error), \
                         contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                        with self.assertRaises(SystemExit) as done:
                            exec(compile(source, str(GATE), "exec"), {})
                    self.assertEqual(done.exception.code, 2)
                    self.assertIn("error operativo", output.getvalue())
                    self.assertNotIn(secret, output.getvalue())

    def test_missing_python_is_operational(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args in ([], ["--strict"]):
                done = subprocess.run([shutil.which("bash"), str(GATE)] + args,
                                      env={**os.environ, "PATH": tmp}, text=True, capture_output=True)
                self.assertEqual(done.returncode, 2)
                self.assertIn("Python no disponible", done.stdout)
                self.assertEqual(done.stderr, "")

    def test_oversized_git_output_does_not_get_a_partial_approval(self):
        code, output = self.run_gate({}, git_fault=("diff", 0, b"x" * (16 * 1024 * 1024 + 1), b""))
        self.assertEqual(code, 2)
        self.assertIn("excede limite", output)
        self.assertLess(len(output), 200)

    def test_deleted_or_context_secrets_do_not_block(self):
        secret = self.synthetic_secrets()[0]
        base = {"app.py": f"secret = '{secret}'\nold = eval(value)\n"}
        code, output = self.run_gate({"app.py": f"secret = '{secret}'\nnew = safe(value)\n"}, initial=base, strict=True)
        self.assertEqual(code, 0)
        self.assertNotIn("posible secreto", output)
        self.assertNotIn(secret, output)
        code, output = self.run_gate({"app.py": "new = safe(value)\n"}, initial=base, strict=True)
        self.assertEqual(code, 0)
        self.assertNotIn("posible secreto", output)

    def test_empty_file_staged_is_applicable_with_zero_added_lines(self):
        code, output = self.run_gate({"empty.py": ""}, strict=True)
        self.assertEqual(code, 0)
        self.assertIn("staged: aplicado; 0 lineas anadidas", output)

    def test_truncated_new_or_deleted_metadata_is_not_an_empty_blob(self):
        for algorithm in (hashlib.sha1, hashlib.sha256):
            digest = algorithm(b"blob 6\0value\n").hexdigest()
            null = "0" * len(digest)
            for mode, old, new in (("new", null, digest), ("deleted", digest, null)):
                diff = ("diff --git a/app.py b/app.py\n"
                        f"{mode} file mode 100644\nindex {old}..{new}\n").encode()
                for suffix in (b"", b"diff --git a/empty.py b/empty.py\nold mode 100644\nnew mode 100755\n"):
                    for strict in (False, True):
                        with self.subTest(algorithm=algorithm().name, mode=mode, strict=strict, next_file=bool(suffix)):
                            code, output = self.run_gate({}, strict=strict, git_fault=("diff", 0, diff + suffix, b""))
                            self.assertEqual(code, 2)
                            self.assertIn("error operativo", output)
                            self.assertNotIn("staged: aplicado", output)

    def test_real_empty_blobs_and_nonempty_hunks_in_both_object_formats(self):
        for object_format in ("sha1", "sha256"):
            for strict in (False, True):
                with self.subTest(object_format=object_format, strict=strict):
                    code, output = self.run_gate({"empty.py": ""}, strict=strict, object_format=object_format)
                    self.assertEqual(code, 0)
                    self.assertIn("0 lineas anadidas", output)
                    code, output = self.run_gate({"empty.py": None}, initial={"empty.py": ""},
                                                 strict=strict, object_format=object_format)
                    self.assertEqual(code, 0)
                    self.assertIn("0 lineas anadidas", output)
                    code, output = self.run_gate({"app.py": "value = eval(input())\n"},
                                                 strict=strict, object_format=object_format)
                    self.assertEqual(code, 0)
                    self.assertIn("app.py:1: eval", output)

    def test_subdirectory_invocation_checks_root_sensitive_tracked_paths(self):
        secret = self.synthetic_secrets()[0]
        initial = {".env": "safe\n", secret + "\n.key": "safe\n", "nested/local.pem": "safe\n"}
        for staged in (False, True):
            for strict in (False, True):
                with self.subTest(staged=staged, strict=strict):
                    code, output = self.run_gate({"app.py": "value = eval(input())\n"}, initial=initial,
                                                 staged=staged, strict=strict, subdir="nested/deep")
                    self.assertEqual(code, int(strict))
                    for path in (".env", "[redactado]\\n.key", "nested/local.pem"):
                        self.assertIn(path + ": fichero sensible rastreado", output)
                    self.assertNotIn(secret, output)
                    self.assertNotIn("../", output)
                    if staged:
                        self.assertIn("app.py:1: eval", output)
                    else:
                        self.assertIn("staged: no aplicable", output)
                        self.assertNotIn("eval", output)

    def test_mode_only_and_deleted_empty_file_are_complete(self):
        diff = b"diff --git a/app.py b/app.py\nold mode 100644\nnew mode 100755\n"
        code, output = self.run_gate({}, git_fault=("diff", 0, diff, b""), strict=True)
        self.assertEqual(code, 0)
        self.assertIn("staged: aplicado; 0 lineas anadidas", output)
        code, output = self.run_gate({"empty.py": None}, initial={"empty.py": ""}, strict=True)
        self.assertEqual(code, 0)
        self.assertIn("staged: aplicado; 0 lineas anadidas", output)

    def test_deleted_file_is_not_an_added_code_audit(self):
        secret = self.synthetic_secrets()[0]
        code, output = self.run_gate({"app.py": None}, initial={"app.py": f"value = '{secret}'\n"}, strict=True)
        self.assertEqual(code, 0)
        self.assertIn("0 lineas anadidas", output)
        self.assertNotIn(secret, output)

    def test_safe_quoted_sensitive_paths(self):
        secret = self.synthetic_secrets()[1]
        name = "dir\n" + secret + ".key"
        code, output = self.run_gate({}, initial={name: "safe\n"}, staged=False, strict=True)
        self.assertEqual(code, 1)
        self.assertIn("dir\\n[redactado].key", output)
        self.assertNotIn(secret, output)

    def test_multiple_hunks_and_no_final_newline_keep_line_numbers(self):
        base = "\n".join(f"safe_{i} = value" for i in range(20)) + "\n"
        changed = base.replace("safe_2 = value", "new = eval(value)")
        changed = changed.replace("safe_18 = value", "newer = os.system(command)").rstrip("\n")
        code, output = self.run_gate({"app.py": changed}, initial={"app.py": base}, strict=True)
        self.assertEqual(code, 0)
        self.assertIn("app.py:3: eval", output)
        self.assertIn("app.py:19: os.system", output)

    def test_only_added_non_comment_production_lines_are_reported(self):
        _, output = self.run_gate({
            "app.py": "old = safe(value)\n# os.system('ignored')\n# eval(ignored)\nnew = eval(value)\nnewer = os.system(command)\n",
            "tests/test_app.py": "value = eval(input())\n",
        }, initial={"app.py": "old = eval(value)\n# os.system('ignored')\nnew = safe(value)\n"})
        self.assertIn("app.py:4: eval", output)
        self.assertIn("app.py:5: os.system", output)
        self.assertNotIn("tests/test_app.py", output)
        self.assertNotIn("app.py:1: eval", output)
        self.assertNotIn("app.py:2", output)
        self.assertNotIn("app.py:3", output)

    def test_catalog_and_no_secret_values(self):
        # El valor falso no imita la forma de una clave real: el escaner de
        # secretos es otro gate y debe poder escanear tambien los tests.
        _, output = self.run_gate({
            "app.py": "subprocess.run(cmd)\nsubprocess.run(['sh', '-c', command], shell=True)\nyaml.load(data)\nssl._create_unverified_context()\njwt.decode(token, verify=False)\nos.chmod(path, 0o777)\nsecret = 'AKIA_FAKE_KEY_000000'\n",
        })
        self.assertNotIn("app.py:1: subprocess", output)
        self.assertIn("app.py:2: subprocess shell=True", output)
        for label in ("yaml.load", "TLS desactivada", "JWT no verificado", "chmod 777"):
            self.assertIn(label, output)
        self.assertNotIn("AKIA_FAKE_KEY_000000", output)

    def test_added_line_starting_with_double_plus_is_not_a_header(self):
        _, output = self.run_gate({
            "app.py": "counter += 1\n++.load\nnew = os.system(command)\n",
        })
        self.assertIn("app.py:3: os.system", output)

    def test_added_line_starting_with_triple_plus_is_not_a_header(self):
        _, output = self.run_gate({
            "app.py": "+++ os.system(command)\n",
        })
        self.assertIn("app.py:1: os.system", output)

    def test_empty_catch_only_blocks_when_it_is_added(self):
        # El fixture se ensambla en runtime: escribir el patron literal en el
        # fuente haria que el gate bloquease su propio test.
        empty_catch = "try { run() } catch (e) " + "{}"
        base = {"app.js": empty_catch + "\nother();\n"}
        added, _ = self.run_gate(
            {"app.js": empty_catch + "\nother();\n" + empty_catch + "\n"},
            initial=base, strict=True,
        )
        self.assertEqual(added, 1, "un catch vacio anadido debe bloquear")
        removed, _ = self.run_gate({"app.js": "other();\n"}, initial=base, strict=True)
        self.assertEqual(removed, 0, "borrar un catch vacio es el arreglo, no una infraccion")


if __name__ == "__main__":
    unittest.main()
