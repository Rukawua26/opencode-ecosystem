import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "verify.sh"
MARKER = "untrusted-output-must-not-appear"
CHECKS = ("hygiene", "source", "runtime", "config", "status", "plugin",
          "context", "discovery", "tests", "git", "gate")

# Todos los comandos son locales al fixture. El timeout simulado no duerme.
DRIVER = '''name="${0##*/}"
if [ "$name" = timeout ]; then
    options=()
    while [[ "$1" == --* ]]; do options+=("$1"); shift; done
    shift
    if [ -n "${REAL_TIMEOUT:-}" ] && [[ "$1" == *hygiene.sh ]]; then
        exec "$REAL_TIMEOUT" "${options[@]}" 5s "$@"
    fi
    if [ -n "$TIMEOUT_MATCH" ] && [[ "$*" == *"$TIMEOUT_MATCH"* ]]; then
        echo "$RAW_MARKER"
        echo "$RAW_MARKER" >&2
        exit 124
    fi
    exec "$@"
fi
if [ -n "${REQUIRE_SAFE_OPTIONS:-}" ]; then
    case ":$SHELLOPTS:" in *:errexit:*|*:xtrace:*|*:verbose:*) exit 76 ;; esac
fi
case "$name" in
    python3)
        case "${1:-}" in
            -c) label=discovery ;;
            -m) label=tests ;;
            *validate-skills.py)
                if [[ "$2" == *'.config'* ]]; then label=runtime; else label=source; fi ;;
            *query_context.py) label=context ;;
            *) label=python ;;
        esac ;;
    hygiene.sh) label=hygiene ;;
    opencode) label=config ;;
    opencode-ecosystem) label=status ;;
    plugin-check) label=plugin ;;
    qa-gate.sh) label=gate ;;
    *) label="$name" ;;
esac
{ printf '%s\\t%s' "$label" "$PWD"; printf '\\t%s' "$@"; printf '\\n'; } >> "$EVENTS"
if [ "$label" = git ] && [ -n "${REAL_GIT:-}" ]; then exec "$REAL_GIT" "$@"; fi
echo "$RAW_MARKER"
echo "$RAW_MARKER" >&2
fault="F_$label"
if [ -n "${!fault}" ]; then exit "${!fault}"; fi
case "$label" in
    git) exit "$STAGED_CODE" ;;
    discovery|tests|python) exec "$REAL_PYTHON" "$@" ;;
esac
exit 0
'''


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.eco = self.home / "opencode-ecosystem"
        self.bin = self.home / "bin"
        self.bin.mkdir()
        self.eco.mkdir()
        self.events = self.home / "events"
        self.env = {**os.environ, "HOME": str(self.home), "PATH": str(self.bin),
                    "EVENTS": str(self.events), "REAL_PYTHON": sys.executable,
                    "RAW_MARKER": MARKER}
        for name in ("python3", "timeout", "git", "opencode", "plugin-check"):
            self.write(self.bin / name, f"#!{shutil.which('bash')}\n" + DRIVER, executable=True)
        (self.bin / "bash").symlink_to(shutil.which("bash"))
        for name in ("scripts/hygiene.sh", "scripts/qa-gate.sh", "opencode-ecosystem"):
            self.write(self.eco / name, f"#!{shutil.which('bash')}\n" + DRIVER, executable=True)
        for path in (self.eco / "validate-skills.py",
                     self.home / "tools/agent_context/query_context.py"):
            self.write(path, "# fixture\n")
        self.write(self.home / "tools/plugin_doctor.sh", 'exec plugin-check "$@"\n')
        (self.eco / "skills").mkdir()
        (self.home / ".config/opencode/skills").mkdir(parents=True)
        self.test_file = self.eco / "control/tests/test_local.py"
        self.write(self.test_file, "import unittest\nclass Local(unittest.TestCase):\n"
                                  "    def test_local(self): self.assertTrue(True)\n")

    def write(self, path, content, executable=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        if executable:
            path.chmod(0o755)

    def run_verify(self, faults=None, staged=0, args=(), timeouts=None, cwd=None):
        self.events.write_text("")
        env = {**self.env, "STAGED_CODE": str(staged),
               "TIMEOUT_MATCH": next(iter(timeouts or {}), ""),
               **{"F_" + label: str((faults or {})[label]) if label in (faults or {}) else ""
                  for label in (*CHECKS, "python")}}
        done = subprocess.run([shutil.which("bash"), str(VERIFY), *args],
                              cwd=cwd or self.home, env=env, text=True,
                              capture_output=True, timeout=60)
        rows = [line.split("\t") for line in self.events.read_text().splitlines()]
        events = [(row[0], row[2:], row[1]) for row in rows]
        output = done.stdout + done.stderr
        self.assertNotIn(MARKER, output)
        # Bash puede trazar/mostrar solo el comando fijo que desactiva opciones.
        self.assertTrue(all(line in ("#!/usr/bin/env bash", "set +evx", "+ set +evx")
                            for line in done.stderr.splitlines()), done.stderr)
        return done.returncode, output, events

    def assert_red(self, code, output):
        self.assertNotEqual(code, 0)
        self.assertNotIn("[ok] verify verde", output)
        self.assertIn("[fail] verify rojo", output)

    def checks_of(self, events):
        """Solo los checks del cierre, sin las llamadas al escritor de informe."""
        return [e for e in events if e[0] in CHECKS]

    def helpers_of(self, events):
        """Llamadas auxiliares (marcador 'en curso' + informe final)."""
        return [e for e in events if e[0] not in CHECKS]

    def test_full_success_runs_exact_tests_strict_and_all_existing_checks(self):
        code, output, events = self.run_verify()
        self.assertEqual(code, 0)
        self.assertIn("[ok] verify verde", output)
        self.assertEqual([event[0] for event in self.checks_of(events)], list(CHECKS))
        # verify.sh solo puede usar python3 para el informe privado: dos veces,
        # una al empezar (marcador "en curso") y otra al terminar. Fijar el
        # numero impide que aparezcan procesos auxiliares ocultos.
        self.assertEqual(len(self.helpers_of(events)), 2,
                         "solo se permiten 2 llamadas auxiliares al informe")
        self.assertEqual(next(e[1] for e in events if e[0] == "tests"),
                         ["-m", "unittest", "discover", "-s", "control/tests"])
        self.assertEqual(next(e[1] for e in events if e[0] == "gate"), ["--strict"])
        for event in events:
            self.assertEqual(event[2], str(self.eco))
        for line in output.splitlines()[2:-1]:
            self.assertIn("alcance:", line)
        self.assertIn("no certifica", output)
        self.assertIn("descartadas", output)

    def test_every_mandatory_failure_keeps_running_and_never_green(self):
        for label in CHECKS:
            with self.subTest(label=label):
                code, output, events = self.run_verify(faults={label: 2})
                self.assert_red(code, output)
                self.assertEqual([e[0] for e in self.checks_of(events)], list(CHECKS))
                if label == "gate":
                    self.assertIn("[incomplete] QA strict", output)

    def test_gate_blocker_is_failure(self):
        code, output, _ = self.run_verify(faults={"gate": 1})
        self.assert_red(code, output)
        self.assertIn("[fail] QA strict", output)

    def test_staged_scope_empty_vs_applicable_uses_git_not_gate_text(self):
        for staged, expected in ((0, "no aplicable (sin cambios staged)"), (1, "aplicable")):
            with self.subTest(staged=staged):
                code, output, events = self.run_verify(staged=staged)
                self.assertEqual(code, 0)
                self.assertIn("ECO: staged " + expected + " + rutas rastreadas", output)
                argv = next(e[1] for e in events if e[0] == "git")
                for flag in ("--cached", "--quiet", "--no-ext-diff", "--no-textconv", ":/"):
                    self.assertIn(flag, argv)
                self.assertIn("gate", [e[0] for e in events])

    def test_staged_query_error_is_not_no_applicable_and_gate_still_runs(self):
        code, output, events = self.run_verify(faults={"git": 128})
        self.assert_red(code, output)
        self.assertIn("staged desconocido (consulta incompleta)", output)
        self.assertNotIn("sin cambios staged", output)
        self.assertEqual(self.checks_of(events)[-1][0], "gate")

    def test_hygiene_trigger_warns_but_operational_error_does_not(self):
        code, output, _ = self.run_verify(faults={"hygiene": 1})
        self.assertEqual(code, 0)
        self.assertIn("[warn] hygiene triggers", output)
        code, output, _ = self.run_verify(faults={"hygiene": 127})
        self.assert_red(code, output)
        self.assertIn("[unavailable] hygiene triggers", output)

    def test_discovery_empty_missing_and_bad_import_cannot_approve(self):
        self.write(self.test_file, "# Ningun test\n")
        # Incluso si un runner/Python devuelve 0 sin tests, discovery no aprueba.
        code, output, _ = self.run_verify(faults={"tests": 0})
        self.assert_red(code, output)
        self.assertIn("[ok] unittest", output)
        self.assertIn("[incomplete] tests discovery", output)
        self.test_file.unlink()
        code, output, events = self.run_verify()
        self.assert_red(code, output)
        self.assertIn("[incomplete] tests discovery", output)
        self.assertIn("tests", [e[0] for e in events])
        shutil.rmtree(self.test_file.parent)
        code, output, _ = self.run_verify()
        self.assert_red(code, output)
        self.write(self.test_file, "raise RuntimeError('" + MARKER + "')\n")
        code, output, _ = self.run_verify()
        self.assert_red(code, output)

    def test_missing_commands_resources_and_timeout_are_not_green(self):
        for relative in ("bin/opencode", "bin/git", "bin/python3", "bin/timeout",
                         "opencode-ecosystem/scripts/qa-gate.sh",
                         "opencode-ecosystem/scripts/hygiene.sh", "tools/plugin_doctor.sh",
                         "tools/agent_context/query_context.py"):
            with self.subTest(missing=relative):
                path = self.home / relative
                original = path.read_bytes()
                permissions = path.stat().st_mode
                path.unlink()
                try:
                    code, output, _ = self.run_verify()
                    self.assert_red(code, output)
                    self.assertIn("[unavailable]", output)
                finally:
                    path.write_bytes(original)
                    path.chmod(permissions)
        for command in ("-m unittest", "qa-gate.sh", "git diff", "hygiene.sh"):
            with self.subTest(timeout=command):
                code, output, events = self.run_verify(timeouts={command: True})
                self.assert_red(code, output)
                self.assertIn("[incomplete]", output)
                if command != "qa-gate.sh":
                    self.assertEqual(self.checks_of(events)[-1][0], "gate")

    def test_invalid_arguments_fail_closed_without_execution_or_raw_output(self):
        code, output, events = self.run_verify(args=[MARKER])
        self.assertEqual(code, 2)
        self.assertIn("argumentos invalidos", output)
        self.assertEqual(events, [])

    def test_missing_repository_is_unavailable(self):
        self.env["HOME"] = str(self.home / "missing")
        code, output, events = self.run_verify()
        self.assert_red(code, output)
        self.assertIn("[unavailable]", output)
        self.assertEqual(events, [])
        self.env.pop("HOME")
        code, output, events = self.run_verify()
        self.assert_red(code, output)
        self.assertIn("HOME no disponible", output)
        self.assertEqual(events, [])

    def test_inherited_shell_options_do_not_leak_or_stop_remaining_checks(self):
        self.env["REQUIRE_SAFE_OPTIONS"] = "1"
        for options in ("xtrace", "verbose:xtrace", "errexit", "errexit:verbose:xtrace"):
            with self.subTest(options=options):
                self.env["SHELLOPTS"] = options
                self.env["HOME"] = str(self.home / MARKER)
                # HOME adversario no debe imprimirse ni producir excepciones raw.
                code, output, _ = self.run_verify()
                self.assert_red(code, output)
                self.env["HOME"] = str(self.home)
                code, output, events = self.run_verify(faults={"source": 2})
                self.assert_red(code, output)
                self.assertEqual([e[0] for e in self.checks_of(events)], list(CHECKS))

    def test_git_environment_cannot_redirect_canonical_staged_query(self):
        git = shutil.which("git")
        self.env["REAL_GIT"] = git
        alternate = self.home / "alternate"
        alternate.mkdir()
        for repo in (self.eco, alternate):
            subprocess.run([git, "init", "-q"], cwd=repo, check=True)
        self.write(self.eco / ".env", "safe\n")
        subprocess.run([git, "add", ".env"], cwd=self.eco, check=True)
        shutil.copyfile(ROOT / "scripts/qa-gate.sh", self.eco / "scripts/qa-gate.sh")
        overrides = ({"GIT_DIR": str(alternate / ".git"), "GIT_WORK_TREE": str(alternate)},
                     {"GIT_INDEX_FILE": str(alternate / ".git/index")},
                     {"GIT_CONFIG_COUNT": "invalid-" + MARKER})
        for override in overrides:
            with self.subTest(names=tuple(override)):
                self.env.update(override)
                try:
                    code, output, _ = self.run_verify()
                    self.assert_red(code, output)
                    self.assertIn("[ok] QA consulta staged: aplicable;", output)
                    self.assertIn("[fail] QA strict", output)
                finally:
                    for name in override:
                        self.env.pop(name)

    def test_real_timeout_kills_term_ignoring_descendant(self):
        self.env["REAL_TIMEOUT"] = shutil.which("timeout")
        address = str(self.home / "ready.sock")
        self.env["READY_SOCKET"] = address
        # El padre sale con TERM; el hijo lo ignora y conserva el socket abierto.
        self.write(self.eco / "scripts/hygiene.sh", f"#!{sys.executable}\n" + '''
import os, signal, socket, sys
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
child = os.fork()
if child == 0:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    with socket.socket(socket.AF_UNIX) as ready:
        ready.connect(os.environ["READY_SOCKET"])
        ready.sendall((str(os.getpgrp()) + "\\n").encode())
        while True:
            signal.pause()
else:
    os.waitpid(child, 0)
''', executable=True)
        group = None
        ready = None
        with socket.socket(socket.AF_UNIX) as server:
            server.bind(address)
            server.listen(1)
            server.settimeout(10)
            try:
                try:
                    code, output, _ = self.run_verify()
                finally:
                    # Recoger el grupo tambien si una asercion del runner falla.
                    ready = server.accept()[0]
                    ready.settimeout(5)
                    data = b""
                    while not data.endswith(b"\n"):
                        part = ready.recv(1)
                        self.assertTrue(part, "handshake incompleto")
                        data += part
                    group = int(data)
                self.assert_red(code, output)
                self.assertIn("[incomplete] hygiene triggers", output)
                self.assertIn("[ok] QA strict", output)
                self.assertEqual(ready.recv(1), b"", "descendiente sigue vivo")
            finally:
                if ready is not None:
                    ready.close()
                if group is not None:
                    try:
                        os.killpg(group, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_real_gate_tracked_sensitive_without_stage_and_binary_incomplete(self):
        self.env["REAL_GIT"] = shutil.which("git")
        git = self.env["REAL_GIT"]
        subprocess.run([git, "init", "-q"], cwd=self.eco, check=True)
        subprocess.run([git, "config", "user.email", "test@example.invalid"], cwd=self.eco, check=True)
        subprocess.run([git, "config", "user.name", "Test"], cwd=self.eco, check=True)
        self.write(self.eco / ".env", "safe\n")
        subprocess.run([git, "add", ".env"], cwd=self.eco, check=True)
        subprocess.run([git, "commit", "-qm", "fixture"], cwd=self.eco, check=True)
        shutil.copyfile(ROOT / "scripts/qa-gate.sh", self.eco / "scripts/qa-gate.sh")
        code, output, _ = self.run_verify()
        self.assert_red(code, output)
        self.assertIn("[fail] QA strict", output)
        self.assertIn("sin cambios staged", output)
        (self.eco / "binary.bin").write_bytes(b"\x00binary\xff\n")
        subprocess.run([git, "add", "binary.bin"], cwd=self.eco, check=True)
        code, output, _ = self.run_verify()
        self.assert_red(code, output)
        self.assertIn("[incomplete] QA strict", output)
        self.assertIn("staged aplicable", output)
