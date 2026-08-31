#!/usr/bin/env bash
# Install the Organic RDD pre-commit gate into a target git repository (opt-in).
# Backs up an existing pre-commit hook; never touches post-commit or other hooks.
#
# Usage: install-rdd-hook.sh [TARGET_REPO]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK_SOURCE="$REPO_ROOT/hooks/pre-commit"
TARGET_REPO="${1:-.}"

if ! git -C "$TARGET_REPO" rev-parse --git-dir >/dev/null 2>&1; then
    echo "[error] $TARGET_REPO no es un repositorio git"
    exit 1
fi
if [[ ! -f "$HOOK_SOURCE" ]]; then
    echo "[error] hook Organic RDD no encontrado en $HOOK_SOURCE"
    exit 1
fi

HOOK_DIR="$(git -C "$TARGET_REPO" rev-parse --path-format=absolute --git-path hooks)"
mkdir -p "$HOOK_DIR"

if [[ -f "$HOOK_DIR/pre-commit" ]]; then
    if cmp -s "$HOOK_SOURCE" "$HOOK_DIR/pre-commit" || grep -q "^# .*Organic RDD pre-commit gate" "$HOOK_DIR/pre-commit"; then
        cp "$HOOK_SOURCE" "$HOOK_DIR/pre-commit"
        chmod +x "$HOOK_DIR/pre-commit"
        echo "[OK] hook organic-rdd actualizado en $HOOK_DIR/pre-commit"
        exit 0
    fi
    cp "$HOOK_DIR/pre-commit" "$HOOK_DIR/pre-commit.pre-organic-rdd"
    echo "[info] Hook anterior respaldado en $HOOK_DIR/pre-commit.pre-organic-rdd"
fi

cp "$HOOK_SOURCE" "$HOOK_DIR/pre-commit"
chmod +x "$HOOK_DIR/pre-commit"
echo "[OK] pre-commit Organic RDD instalado en $HOOK_DIR/pre-commit"
echo "[info] El gate bloquea commits con candidatos stale o manifest incompleto."
echo "[info] Nota: un hook local puede omitirse con --no-verify; no es autoridad remota."
