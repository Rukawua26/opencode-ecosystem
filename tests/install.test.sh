#!/usr/bin/env bash
# Test that install.sh runs successfully in a clean environment
set -euo pipefail

export HOME="/tmp/test-install-home"
rm -rf "$HOME"
mkdir -p "$HOME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Run install with skip-memory (avoids npm install in test)
bash "$REPO_DIR/install.sh" --verbose --skip-memory --force

# Assertions
echo "[test] Verifying installation..."

assert_exists() {
  if [[ ! -e "$1" ]]; then
    echo "[FAIL] Expected: $1"
    exit 1
  fi
  echo "[OK] $1"
}

assert_exists "$HOME/.config/opencode/opencode.jsonc"
assert_exists "$HOME/.config/opencode/agents"
assert_exists "$HOME/.config/opencode/plugins"
assert_exists "$HOME/.config/opencode/mcp"
assert_exists "$HOME/.config/opencode/profiles"
assert_exists "$HOME/opencode-custom/skills"
assert_exists "$HOME/.config/opencode/.env.example"
assert_exists "$HOME/.config/opencode/tools/doctor.js"
assert_exists "$HOME/.opencode/bin/opencode-doctor"
assert_exists "$HOME/.config/opencode/lib/session-metrics.js"
assert_exists "$HOME/.opencode/bin/opencode-metrics"

# Count agents
AGENT_COUNT=$(find "$HOME/.config/opencode/agents" -name "*.md" | wc -l)
if [[ $AGENT_COUNT -lt 10 ]]; then
  echo "[FAIL] Expected at least 10 agents, got $AGENT_COUNT"
  exit 1
fi
echo "[OK] $AGENT_COUNT agents installed"

# Count plugins
PLUGIN_COUNT=$(find "$HOME/.config/opencode/plugins" -name "*.js" | wc -l)
if [[ $PLUGIN_COUNT -lt 5 ]]; then
  echo "[FAIL] Expected at least 5 plugins, got $PLUGIN_COUNT"
  exit 1
fi
echo "[OK] $PLUGIN_COUNT plugins installed"

# Count skills
SKILL_COUNT=$(find "$HOME/opencode-custom/skills" -maxdepth 1 -type d | wc -l)
SKILL_COUNT=$((SKILL_COUNT > 0 ? SKILL_COUNT - 1 : 0))
if [[ $SKILL_COUNT -lt 10 ]]; then
  echo "[FAIL] Expected at least 10 skills, got $SKILL_COUNT"
  exit 1
fi
echo "[OK] $SKILL_COUNT skills installed"

# Cleanup
rm -rf "$HOME"

echo ""
echo "[PASS] All install tests passed!"
