import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "scripts" / "qa-gate.sh"


class QaGateTests(unittest.TestCase):
    def run_gate(self, files, initial=None, strict=False):
        """Ejecuta el gate en un repo temporal. Devuelve (returncode, stdout)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            for name, content in (initial or {}).items():
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            if initial:
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            for name, content in files.items():
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            args = [str(GATE)] + (["--strict"] if strict else [])
            done = subprocess.run(args, cwd=repo, text=True, capture_output=True)
            return done.returncode, done.stdout

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
