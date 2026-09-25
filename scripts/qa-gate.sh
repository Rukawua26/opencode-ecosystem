#!/usr/bin/env bash
# qa-gate.sh — modo warn (no bloqueante en F1): detecta catch vacío, console.log, TODO huérfano en staged.
# También avisa de posibles secretos en líneas añadidas y de ficheros sensibles rastreados (.env/.pem/.key/id_rsa).
# Los secretos nunca se imprimen; solo el tipo de patrón detectado.
# Uso: qa-gate.sh [--strict] ; en warn siempre exit 0 pero avisa.
set -u
STRICT="${1:-warn}"
FAIL=0
DIFF=$(git diff --staged 2>/dev/null || true)
echo "$DIFF" | grep -nE "catch *(\([^)]*\))? *\{\s*\}" && { echo "[qa-gate] catch vacío detectado"; FAIL=1; } || true
echo "$DIFF" | grep -nE "console\.log|dbg!|println!|e\.printStackTrace" | head -5
echo "$DIFF" | grep -nE "TODO|FIXME" | head -5
# Posibles secretos solo en lineas añadidas (no en eliminadas ni contexto del diff)
ADDED=$(echo "$DIFF" | grep -E '^\+[^+]' || true)
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
TRACKED=$(git ls-files 2>/dev/null | grep -E '(^|/)\.env($|\.)|\.pem$|\.key$|(^|/)id_rsa$' || true)
if [ -n "$TRACKED" ]; then
  echo "$TRACKED" | sed 's/^/[qa-gate] fichero sensible rastreado: /'
  FAIL=1
fi
if [ "$STRICT" = "--strict" ] && [ "$FAIL" = "1" ]; then exit 1; fi
exit 0
