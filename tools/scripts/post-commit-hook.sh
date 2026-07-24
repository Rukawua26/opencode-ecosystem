#!/usr/bin/env bash
# post-commit hook for auto-syncing memory
# Usage: cp tools/scripts/post-commit-hook.sh .git/hooks/post-commit && chmod +x .git/hooks/post-commit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR")"
MEMORY_ADAPTER_CMD="node ~/.config/opencode/mcp/memory-adapter/src/cli.js sync"

# Only run if we're in a git repo and memory-adapter is configured
if command -v git >/dev/null 2>&1; then
    if [[ -f "$REPO_ROOT/.config/opencode/mcp/memory-adapter/src/cli.js" ]]; then
        PROJECT_NAME=$(basename "$REPO_ROOT")
        $MEMORY_ADAPTER_CMD --project "$PROJECT_NAME" --path "$REPO_ROOT" --out "$REPO_ROOT/memory-sync.json" 2>/dev/null &
    fi
fi
