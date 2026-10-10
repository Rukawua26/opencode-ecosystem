#!/usr/bin/env bash
# kairos.sh (scout) — lite: escanea staged diff por TODO, catch vacíos y resume commit convencional.
# Uso: kairos.sh [REPO_DIR] ; solo anexa a observations.log si hay señal real.
set -u
REPO="${1:-$HOME}"
LOG="$HOME/.config/opencode/memory/observations.log"
cd "$REPO" 2>/dev/null || exit 0
SIGNAL=$(git diff --staged 2>/dev/null | grep -nE "TODO|FIXME|catch *(\([^)]*\))? *\{\s*\}|console\.log|dbg!|println!" | head -20 || true)
[ -n "$SIGNAL" ] || exit 0
{
echo "### kairos $(date -Is) @ $REPO"
git diff --staged --stat 2>/dev/null | head -20
echo "$SIGNAL"
} >> "$LOG" 2>/dev/null || true
