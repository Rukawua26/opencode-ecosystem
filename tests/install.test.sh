#!/usr/bin/env bash
# Test that install.sh runs successfully in a clean environment
set -euo pipefail

export HOME="/tmp/test-install-home"
rm -rf "$HOME"
mkdir -p "$HOME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Run install without the optional memory adapter.
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

# Verify MCP router SDK
assert_exists "$HOME/.config/opencode/mcp/package.json"
assert_exists "$HOME/.config/opencode/mcp/local-model-router.js"
assert_exists "$HOME/.config/opencode/mcp/node_modules/@modelcontextprotocol/sdk/package.json"
echo "[OK] MCP router SDK installed"

# Count agents
AGENT_COUNT=$(find "$HOME/.config/opencode/agents" -name "*.md" | wc -l)
if [[ $AGENT_COUNT -lt 10 ]]; then
  echo "[FAIL] Expected at least 10 agents, got $AGENT_COUNT"
  exit 1
fi
echo "[OK] $AGENT_COUNT agents installed"

# Count plugins
PLUGIN_COUNT=$(find "$HOME/.config/opencode/plugins" -name "*.js" ! -name "*-helpers.js" | wc -l)
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

# A normal reinstall must preserve user customizations.
printf '%s\n' 'user-agent-marker' > "$HOME/.config/opencode/agents/ai-matcher.md"
printf '%s\n' 'user-skill-marker' > "$HOME/opencode-custom/skills/defuddle/SKILL.md"
printf '%s\n' 'user-profile-marker' > "$HOME/.config/opencode/profiles/work/opencode.jsonc"
printf '%s\n' 'user-tool-marker' > "$HOME/.config/opencode/tools/doctor.js"
bash "$REPO_DIR/install.sh" --skip-memory >/dev/null

for marker_file in \
  "$HOME/.config/opencode/agents/ai-matcher.md:user-agent-marker" \
  "$HOME/opencode-custom/skills/defuddle/SKILL.md:user-skill-marker" \
  "$HOME/.config/opencode/profiles/work/opencode.jsonc:user-profile-marker" \
  "$HOME/.config/opencode/tools/doctor.js:user-tool-marker"; do
  file="${marker_file%%:*}"
  marker="${marker_file##*:}"
  if [[ "$(<"$file")" != "$marker" ]]; then
    echo "[FAIL] Reinstall overwrote: $file"
    exit 1
  fi
done
echo "[OK] Reinstall preserved agents, skills, profiles, and tools"

# Cleanup
rm -rf "$HOME"

echo ""
echo "[PASS] All install tests passed!"
