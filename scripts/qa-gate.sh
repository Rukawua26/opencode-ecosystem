#!/usr/bin/env bash
set +evx
# Uso: qa-gate.sh [--strict]. Hallazgos: warn=0, strict=1 si bloqueantes.
# Error operativo/argumentos=2 en ambos modos. Nunca imprime codigo ni errores Git.
# Alcance: repo descubierto desde cwd e indice canonico, no GIT_INDEX_FILE alterno.
set -u
if ! command -v python3 >/dev/null 2>&1; then
  echo '[qa-gate] error operativo: Python no disponible'
  exit 2
fi
python3 - "$@" <<'PY'
import ast
import hashlib
import os
import re
import subprocess
import sys
import tempfile


secrets = (
    (re.compile(r"AKIA[0-9A-Z]{16}"), "clave AWS (AKIA...)"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "token de GitHub (ghp_...)"),
    (re.compile(r"sk-[A-Za-z0-9_-]{32,}"), "clave API tipo sk-..."),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "clave privada PEM"),
    (re.compile(r"://[^/:@\s]+:[^/@\s]+@"), "URL con usuario:password embebido"),
)
risks = (
    (re.compile(r"\bsubprocess\.(?:run|Popen|call|check_call|check_output)\s*\([^\n]*\bshell\s*=\s*True\b"), "subprocess shell=True"),
    (re.compile(r"\bos\.system\s*\("), "os.system"),
    (re.compile(r"\beval\s*\("), "eval"),
    (re.compile(r"\byaml\.load\s*\("), "yaml.load"),
    (re.compile(r"(?:_create_unverified_context|CERT_NONE)"), "TLS desactivada"),
    (re.compile(r"\bjwt\.decode\s*\([^\n]*(?:\bverify\s*=\s*False|verify_signature\s*[=:]\s*False)"), "JWT no verificado"),
    (re.compile(r"\bchmod\s*\([^\n]*(?:0o)?777\b"), "chmod 777"),
)

warnings = tuple((re.compile(re.escape(label)), label) for label in
                 ("console.log", "dbg!", "println!", "e.printStackTrace", "TODO", "FIXME"))
catch = re.compile(r"catch *(\([^)]*\))? *\{\s*\}")
sensitive = re.compile(r"(^|/)\.env($|\.)|\.pem$|\.key$|(^|/)id_rsa$")
test_path = re.compile(r"(^|/)(?:tests?|test)[^/]*\/|(^|/)test_[^/]*$|(^|/)[^/]*_test\.[^/]+$")
hunk = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$")
empty_blobs = {40: hashlib.sha1(b"blob 0\0").hexdigest(),
               64: hashlib.sha256(b"blob 0\0").hexdigest()}


class GateError(Exception):
    """Solo causas internas fijas, sin datos de Git ni excepciones externas."""


def git_output(*args):
    # Evita redireccion de repo/indice/config por entorno; conserva PATH y HOME.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    # Transporte temporal, no logs: evita retener stdout sin limite en RAM.
    with tempfile.TemporaryFile() as output:
        done = subprocess.run(
            ["git", "-c", "core.quotePath=true", "-c", "diff.submodule=short", *args],
            stdout=output, stderr=subprocess.DEVNULL, timeout=15, env=env,
        )
        if done.returncode:
            raise GateError("Git no disponible o consulta fallida")
        output.seek(0)
        data = output.read(16 * 1024 * 1024 + 1)
        if len(data) > 16 * 1024 * 1024:
            raise GateError("salida Git excede limite; analisis incompleto")
        return data


def safe_path(path):
    for pattern, _ in secrets:
        path = pattern.sub("[redactado]", path)
    # Escapa controles, backslashes, bidi y bytes invalidos sin terminal injection.
    return path.encode("unicode_escape").decode("ascii")


def diff_path(value):
    if value.startswith('"'):
        value = os.fsdecode(ast.literal_eval(value).encode("latin1"))
    else:
        value = value.rstrip("\t")
    if value == "/dev/null":
        return None
    if not value.startswith("b/"):
        raise GateError("ruta diff invalida")
    return value[2:]


def audit(strict):
    diff = git_output("diff", "--cached", "--patch", "--full-index", "--no-color", "--no-ext-diff",
                      "--no-textconv", "--no-renames", "--no-relative", "--unified=0",
                      "--src-prefix=a/", "--dst-prefix=b/", "--line-prefix=",
                      "--inter-hunk-context=0", "--ignore-submodules=none", "--")
    tracked = git_output("ls-files", "--full-name", "-z", "--", ":/")
    if (diff and not diff.endswith(b"\n")) or (tracked and not tracked.endswith(b"\0")):
        raise GateError("salida Git incompleta")
    findings = []
    total = 0
    blocking = False

    def report(path, number, label, block=False):
        nonlocal total, blocking
        total += 1
        blocking = blocking or block
        if len(findings) < 50:
            location = safe_path(path) + (f":{number}" if number is not None else "")
            findings.append(f"{location}: {label}")

    path = None
    section = False
    metadata = set()
    index_hashes = None
    headers = 0
    had_hunk = False
    old_left = new_left = 0
    number = None
    added = 0

    def complete_section():
        if headers:
            return headers == 2 and had_hunk and metadata in (
                {"index"}, {"index", "new file mode"}, {"index", "deleted file mode"},
                {"index", "old mode", "new mode"},
            )
        # Sin hunk, new/deleted solo son completos si el blob es realmente vacio.
        if metadata == {"old mode", "new mode"}:
            return True
        if index_hashes is None:
            return False
        old, new = index_hashes
        null = "0" * len(old)
        empty = empty_blobs[len(old)]
        return (metadata == {"index", "new file mode"} and old == null and new == empty
                or metadata == {"index", "deleted file mode"} and old == empty and new == null)

    for line in diff.decode("utf-8", "surrogateescape").split("\n")[:-1]:
        if line.startswith("\\ No newline at end of file"):
            continue
        if old_left or new_left:
            # Los contadores del hunk distinguen codigo +++ de cabeceras.
            if line.startswith("+") and new_left:
                code = line[1:]
                added += 1
                if catch.search(code):
                    report(path, number, "catch vacío detectado", True)
                for pattern, label in secrets:
                    if pattern.search(code):
                        report(path, number, "posible secreto en staging: " + label, True)
                for pattern, label in warnings:
                    if pattern.search(code):
                        report(path, number, label)
                if not test_path.search(path) and not re.match(r"\s*(?:#|//|/\*|\*|<!--)", code):
                    for pattern, label in risks:
                        if pattern.search(code):
                            report(path, number, label)
                new_left -= 1
                number += 1
            elif line.startswith("-") and old_left:
                old_left -= 1
            elif line.startswith(" ") and old_left and new_left:
                old_left -= 1
                new_left -= 1
                number += 1
            else:
                raise GateError("diff incompleto o invalido")
            continue
        if line.startswith("diff --git "):
            if section and not complete_section():
                raise GateError("diff incompleto")
            section = True
            metadata = set()
            index_hashes = None
            headers = 0
            had_hunk = False
            path = None
            number = None
        elif not section:
            raise GateError("diff invalido")
        elif line.startswith("+++ "):
            if headers != 1:
                raise GateError("diff incompleto")
            path = diff_path(line[4:])
            headers = 2
        elif line.startswith("--- "):
            if headers:
                raise GateError("diff incompleto")
            headers = 1
        elif line.startswith("@@"):
            match = hunk.fullmatch(line)
            if not match or headers != 2:
                raise GateError("hunk invalido")
            had_hunk = True
            old_left = int(match[2]) if match[2] is not None else 1
            new_left = int(match[4]) if match[4] is not None else 1
            number = int(match[3])
            if new_left and path is None:
                raise GateError("ruta diff ausente")
        elif line.startswith(("Binary files ", "GIT binary patch")):
            raise GateError("diff binario: analisis staged incompleto")
        elif line.startswith("index "):
            match = re.fullmatch(r"index ([0-9a-f]{40}|[0-9a-f]{64})\.\.([0-9a-f]{40}|[0-9a-f]{64})(?: [0-7]{6})?", line)
            if not match or len(match[1]) != len(match[2]):
                raise GateError("diff incompleto")
            index_hashes = match[1], match[2]
            metadata.add("index")
        elif line.startswith(("new file mode ", "deleted file mode ", "old mode ", "new mode ")):
            metadata.add(line.rsplit(" ", 1)[0])
        else:
            raise GateError("diff no soportado o incompleto")
    if old_left or new_left or section and not complete_section():
        raise GateError("diff incompleto")
    for name in tracked.split(b"\0")[:-1]:
        name = os.fsdecode(name)
        if sensitive.search(name):
            report(name, None, "fichero sensible rastreado", True)
    scope = f"staged: aplicado; {added} lineas anadidas" if diff else "staged: no aplicable (sin cambios staged)"
    print(f"[qa-gate] {scope}; rutas rastreadas: comprobadas")
    for finding in findings:
        print(f"[qa-gate] {finding}")
    if total > len(findings):
        print(f"[qa-gate] {total - len(findings)} hallazgos omitidos de la presentacion; todos evaluados")
    return int(strict and blocking)


if sys.argv[1:] not in ([], ["--strict"]):
    print("[qa-gate] argumentos invalidos; uso: qa-gate.sh [--strict]")
    sys.exit(2)
try:
    result = audit(bool(sys.argv[1:]))
except GateError as error:
    print(f"[qa-gate] error operativo: {error}")
    result = 2
except Exception:
    print("[qa-gate] error operativo: analisis no disponible o tiempo agotado")
    result = 2
sys.exit(result)
PY
