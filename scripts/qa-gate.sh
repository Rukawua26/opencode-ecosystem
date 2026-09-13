#!/usr/bin/env bash
# qa-gate.sh — modo warn (no bloqueante en F1): detecta catch vacío, console.log, TODO huérfano en staged.
# Uso: qa-gate.sh [--strict] ; en warn siempre exit 0 pero avisa.
set -u
STRICT="${1:-warn}"
FAIL=0
DIFF=$(git diff --staged 2>/dev/null || true)
echo "$DIFF" | grep -nE "catch *(\([^)]*\))? *\{\s*\}" && { echo "[qa-gate] catch vacío detectado"; FAIL=1; } || true
echo "$DIFF" | grep -nE "console\.log|dbg!|println!|e\.printStackTrace" | head -5
echo "$DIFF" | grep -nE "TODO|FIXME" | head -5
if [ "$STRICT" = "--strict" ] && [ "$FAIL" = "1" ]; then exit 1; fi
exit 0
