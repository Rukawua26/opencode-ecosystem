#!/usr/bin/env bash
# Install Git hooks for auto-syncing memory
# Run this script from the root of your project

set -euo pipefail

HOOK_DIR=".git/hooks"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/post-commit-hook.sh"

if [[ ! -d "$HOOK_DIR" ]]; then
    echo "[error] No es un repositorio git o .git/hooks no existe"
    exit 1
fi

if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo "[error] post-commit-hook.sh no encontrado en $SCRIPT_PATH"
    exit 1
fi

echo "[opencode] Instalando post-commit hook..."
cp "$SCRIPT_PATH" "$HOOK_DIR/post-commit"
chmod +x "$HOOK_DIR/post-commit"
echo "[OK] post-commit hook instalado en $HOOK_DIR/post-commit"
echo "[info] Cada commit sincronizará la memoria automáticamente"
