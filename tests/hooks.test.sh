#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

export HOME="$TEMP/home"
TARGET="$TEMP/target-repo"
mkdir -p "$TARGET"

bash "$ROOT/install.sh" --force >/dev/null
git -C "$TARGET" init -b main >/dev/null
git -C "$TARGET" config user.name "Hook Test"
git -C "$TARGET" config user.email "hook@example.invalid"

bash "$ROOT/tools/scripts/install-hooks.sh" "$TARGET" >/dev/null
bash "$ROOT/tools/scripts/install-hooks.sh" "$TARGET" >/dev/null

HOOKS="$(git -C "$TARGET" rev-parse --path-format=absolute --git-path hooks)"
cp "$HOOKS/post-commit" "$HOOKS/post-commit.pre-opencode"
chmod +x "$HOOKS/post-commit.pre-opencode"

HOME="$HOME" git -C "$TARGET" commit --allow-empty -m "test hook" >/dev/null
sleep 1

test "$(git -C "$TARGET" rev-list --count HEAD)" = "1"
SYNC_FILES=("$HOME"/.local/share/opencode/memory-sync/target-repo-*.json)
test -f "${SYNC_FILES[0]}"
test ! -e "$TARGET/.opencode-memory"

echo "[PASS] Hook is target-safe, idempotent, non-recursive, and exports outside the repo"
