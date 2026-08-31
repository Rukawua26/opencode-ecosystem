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

# Organic RDD pre-commit hook (opt-in): installs, backs up existing hooks and
# never touches post-commit.
RDD_TARGET="$TEMP/rdd-repo"
mkdir -p "$RDD_TARGET"
git -C "$RDD_TARGET" init -b main >/dev/null
git -C "$RDD_TARGET" config user.name "Hook Test"
git -C "$RDD_TARGET" config user.email "hook@example.invalid"

bash "$ROOT/tools/scripts/install-rdd-hook.sh" "$RDD_TARGET" >/dev/null
RDD_HOOKS="$(git -C "$RDD_TARGET" rev-parse --path-format=absolute --git-path hooks)"
test -x "$RDD_HOOKS/pre-commit"
sh -n "$RDD_HOOKS/pre-commit"
grep -q "organic-rdd" "$RDD_HOOKS/pre-commit"

echo "custom" > "$RDD_HOOKS/post-commit"
echo "existing hook" > "$RDD_HOOKS/pre-commit"
bash "$ROOT/tools/scripts/install-rdd-hook.sh" "$RDD_TARGET" >/dev/null
test "$(cat "$RDD_HOOKS/pre-commit.pre-organic-rdd")" = "existing hook"
test "$(cat "$RDD_HOOKS/post-commit")" = "custom"

bash "$ROOT/tools/scripts/install-rdd-hook.sh" "$RDD_TARGET" >/dev/null
grep -q "organic-rdd" "$RDD_HOOKS/pre-commit"

# A composite hook that merely mentions organic-rdd must be backed up, not
# silently replaced as if it were a managed copy.
printf '#!/bin/sh\necho custom-check\necho uses-organic-rdd-string\n' > "$RDD_HOOKS/pre-commit"
bash "$ROOT/tools/scripts/install-rdd-hook.sh" "$RDD_TARGET" >/dev/null
grep -q "custom-check" "$RDD_HOOKS/pre-commit.pre-organic-rdd"
grep -q "Organic RDD pre-commit gate" "$RDD_HOOKS/pre-commit"

echo "[PASS] RDD hook is opt-in, backs up pre-commit, updates idempotently and preserves post-commit"
