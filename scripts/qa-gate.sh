#!/usr/bin/env bash
# qa-gate.sh — modo warn (no bloqueante en F1): detecta catch vacío, console.log, TODO huérfano en staged.
# También avisa de posibles secretos en líneas añadidas y de ficheros sensibles rastreados (.env/.pem/.key/id_rsa).
# Los secretos nunca se imprimen; solo el tipo de patrón detectado.
# Uso: qa-gate.sh [--strict] ; en warn siempre exit 0 pero avisa.
set -u
STRICT="${1:-warn}"
FAIL=0
DIFF=$(git diff --staged 2>/dev/null || true)
# Solo lineas anadidas: un catch vacio eliminado (arreglo) o de contexto no bloquea.
ADDED=$(echo "$DIFF" | grep -E '^\+[^+]' || true)
echo "$ADDED" | grep -E "catch *(\([^)]*\))? *\{\s*\}" >/dev/null && { echo "[qa-gate] catch vacío detectado"; FAIL=1; } || true
echo "$ADDED" | grep -nE "console\.log|dbg!|println!|e\.printStackTrace" | head -5
echo "$ADDED" | grep -nE "TODO|FIXME" | head -5
# Posibles secretos solo en lineas añadidas (no en eliminadas ni contexto del diff)
if [ -n "$ADDED" ]; then
  while IFS='|' read -r pat label; do
    if echo "$ADDED" | grep -qE -- "$pat"; then
      echo "[qa-gate] posible secreto en staging: $label"
      FAIL=1
    fi
  done <<'EOF'
AKIA[0-9A-Z]{16}|clave AWS (AKIA...)
ghp_[A-Za-z0-9]{36}|token de GitHub (ghp_...)
sk-[A-Za-z0-9_-]{32,}|clave API tipo sk-...
-----BEGIN [A-Z ]*PRIVATE KEY-----|clave privada PEM
://[^/:@[:space:]]+:[^/@[:space:]]+@|URL con usuario:password embebido
EOF
fi
# Riesgos informativos: solo codigo anadido de ficheros de produccion.
printf '%s\n' "$DIFF" | python3 /dev/fd/3 3<<'PY'
import re
import sys


patterns = (
    (re.compile(r"\bsubprocess\.(?:run|Popen|call|check_call|check_output)\s*\([^\n]*\bshell\s*=\s*True\b"), "subprocess shell=True"),
    (re.compile(r"\bos\.system\s*\("), "os.system"),
    (re.compile(r"\beval\s*\("), "eval"),
    (re.compile(r"\byaml\.load\s*\("), "yaml.load"),
    (re.compile(r"(?:_create_unverified_context|CERT_NONE)"), "TLS desactivada"),
    (re.compile(r"\bjwt\.decode\s*\([^\n]*(?:\bverify\s*=\s*False|verify_signature\s*[=:]\s*False)"), "JWT no verificado"),
    (re.compile(r"\bchmod\s*\([^\n]*(?:0o)?777\b"), "chmod 777"),
)

diff = sys.stdin.read().splitlines()
path = None
line_number = None
for line in diff:
    if line.startswith("diff --git "):
        match = re.search(r" b/(.*)$", line)
        path = match.group(1) if match else None
        line_number = None
        continue
    if line.startswith("@@"):
        match = re.search(r"\+(\d+)(?:,(\d+))?", line)
        line_number = int(match.group(1)) if match else None
        continue
    if line.startswith("+") and not (line.startswith("+++ ") and line_number is None):
        code = line[1:]
        production = path and not re.search(r"(^|/)(?:tests?|test)[^/]*\/|(^|/)test_[^/]*$|(^|/)[^/]*_test\.[^/]+$", path)
        comment = re.match(r"\s*(?:#|//|/\*|\*|<!--)", code)
        if production and not comment and line_number is not None:
            for pattern, label in patterns:
                if pattern.search(code):
                    print(f"{path}:{line_number}: {label}")
        if line_number is not None:
            line_number += 1
    elif not line.startswith("-") and line_number is not None:
        line_number += 1
PY
TRACKED=$(git ls-files 2>/dev/null | grep -E '(^|/)\.env($|\.)|\.pem$|\.key$|(^|/)id_rsa$' || true)
if [ -n "$TRACKED" ]; then
  echo "$TRACKED" | sed 's/^/[qa-gate] fichero sensible rastreado: /'
  FAIL=1
fi
if [ "$STRICT" = "--strict" ] && [ "$FAIL" = "1" ]; then exit 1; fi
exit 0
