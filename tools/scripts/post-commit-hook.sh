#!/usr/bin/env bash
# opencode-memory-hook
# post-commit hook for auto-syncing memory
# Usage: cp tools/scripts/post-commit-hook.sh .git/hooks/post-commit && chmod +x .git/hooks/post-commit

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
MEMORY_CLI="$HOME/.config/opencode/mcp/memory-adapter/src/cli.js"

if [[ -x "$HOOK_DIR/post-commit.pre-opencode" ]] && ! grep -q "opencode-memory-hook\|MEMORY_CLI=\|post-commit.pre-opencode" "$HOOK_DIR/post-commit.pre-opencode"; then
  "$HOOK_DIR/post-commit.pre-opencode" "$@"
fi

# Export only. Never create a commit from post-commit or it would recurse.
if [[ -f "$MEMORY_CLI" ]]; then
  node "$MEMORY_CLI" sync --path "$REPO_ROOT" >/dev/null 2>&1 &
fi
