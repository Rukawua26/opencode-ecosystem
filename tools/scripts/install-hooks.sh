#!/usr/bin/env bash
# Install Git hooks for auto-syncing memory
# Run this script from the root of your project

set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/post-commit-hook.sh"
TARGET_REPO="${1:-.}"

if ! git -C "$TARGET_REPO" rev-parse --git-dir >/dev/null 2>&1; then
    echo "[error] $TARGET_REPO no es un repositorio git"
    exit 1
fi
HOOK_DIR="$(git -C "$TARGET_REPO" rev-parse --path-format=absolute --git-path hooks)"
mkdir -p "$HOOK_DIR"

if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo "[error] post-commit-hook.sh no encontrado en $SCRIPT_PATH"
    exit 1
fi

echo "[opencode] Instalando post-commit hook..."
if [[ -f "$HOOK_DIR/post-commit" ]]; then
    if grep -q "opencode-memory-hook\|MEMORY_CLI=" "$HOOK_DIR/post-commit"; then
        cp "$SCRIPT_PATH" "$HOOK_DIR/post-commit"
        chmod +x "$HOOK_DIR/post-commit"
        echo "[OK] post-commit hook actualizado en $HOOK_DIR/post-commit"
        exit 0
    fi
    cp "$HOOK_DIR/post-commit" "$HOOK_DIR/post-commit.pre-opencode"
    echo "[info] Hook anterior respaldado en $HOOK_DIR/post-commit.pre-opencode"
fi
cp "$SCRIPT_PATH" "$HOOK_DIR/post-commit"
chmod +x "$HOOK_DIR/post-commit"
echo "[OK] post-commit hook instalado en $HOOK_DIR/post-commit"
echo "[info] Cada commit sincronizará la memoria automáticamente"
