#!/usr/bin/env bash
# Test that install.sh runs successfully in a clean environment
set -euo pipefail

export HOME="/tmp/test-install-home"
rm -rf "$HOME"
mkdir -p "$HOME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

snapshot_home() {
  local root="$1" current="$1"
  local entry path rel stats target
  while IFS= read -r -d '' entry; do
    path="${entry}"
    rel="${path#"$root"/}"
    stats=''
    if [[ -L "$path" ]]; then
      target="$(readlink "$path")"
      printf '%s|link|%s\n' "$rel" "$target"
    elif [[ -d "$path" ]]; then
      printf '%s|dir|%s\n' "$rel" "$(ls -1 "$path" | wc -l | tr -d ' ')"
    else
      printf '%s|file|%s\n' "$rel" "$(wc -c < "$path" | tr -d ' ')"
    fi
  done < <(find "$root" -mindepth 1 -print0 2>/dev/null) | sort
}

# A clean dry-run must describe the plan without creating HOME or running apply-only work.
DRY_RUN_HOME="/tmp/test-install-dry-run-home"
rm -rf "$DRY_RUN_HOME"
DRY_RUN_OUTPUT="$(HOME="$DRY_RUN_HOME" bash "$REPO_DIR/install.sh" --dry-run --verbose 2>&1)"
if [[ -e "$DRY_RUN_HOME" ]]; then
  echo "[FAIL] Clean dry-run modified HOME"
  exit 1
fi
for expected in "create directory:" "install-dependencies:" "defer-verification:" "Dry run complete; no changes made"; do
  if [[ "$DRY_RUN_OUTPUT" != *"$expected"* ]]; then
    echo "[FAIL] Dry-run output missing: $expected"
    exit 1
  fi
done
echo "[OK] Clean dry-run produced a complete read-only plan"

# A detached dry-run reports the remote source without cloning or creating temp files.
DETACHED_DIR="$(mktemp -d)"
DETACHED_TMP="$DETACHED_DIR/tmp"
mkdir -p "$DETACHED_TMP"
cp "$REPO_DIR/install.sh" "$DETACHED_DIR/install.sh"
DETACHED_OUTPUT="$(HOME="$DRY_RUN_HOME" TMPDIR="$DETACHED_TMP" bash "$DETACHED_DIR/install.sh" --dry-run 2>&1)"
if [[ -e "$DRY_RUN_HOME" || -n "$(find "$DETACHED_TMP" -mindepth 1 -print -quit)" ]]; then
  echo "[FAIL] Detached dry-run created HOME or temporary files"
  exit 1
fi
if [[ "$DETACHED_OUTPUT" != *"clone https://github.com/Rukawua26/opencode-ecosystem.git at tag v1.9.0"* || "$DETACHED_OUTPUT" != *"detailed plan requires distribution contents"* ]]; then
  echo "[FAIL] Detached dry-run did not report deferred remote planning"
  exit 1
fi
rm -rf "$DETACHED_DIR"
echo "[OK] Detached dry-run did not clone or create temporary files"

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
assert_exists "$HOME/.config/opencode/tools/profile.js"
assert_exists "$HOME/.opencode/bin/opencode-profile"
assert_exists "$HOME/.opencode/bin/opencode-work"
assert_exists "$HOME/.opencode/bin/opencode-personal"
assert_exists "$HOME/.opencode/bin/opencode-light"
assert_exists "$HOME/.config/opencode/tools/skills.js"
assert_exists "$HOME/.opencode/bin/opencode-skills"

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
POPULATED_BEFORE="$(snapshot_home "$HOME")"
NORMAL_DRY_RUN_OUTPUT="$(bash "$REPO_DIR/install.sh" --skip-memory --dry-run 2>&1)"
FORCE_DRY_RUN_OUTPUT="$(bash "$REPO_DIR/install.sh" --skip-memory --force --dry-run 2>&1)"
POPULATED_AFTER="$(snapshot_home "$HOME")"
if [[ "$POPULATED_BEFORE" != "$POPULATED_AFTER" ]]; then
  echo "[FAIL] Normal or force dry-run changed a populated installation"
  exit 1
fi
if [[ "$NORMAL_DRY_RUN_OUTPUT" != *"preserve:"* || "$FORCE_DRY_RUN_OUTPUT" != *"backup:"* ]]; then
  echo "[FAIL] Normal/force dry-run did not reflect mode decisions"
  exit 1
fi
echo "[OK] Normal and force dry-run preserved populated state"
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

# A first sync updates managed files without pruning unknown files.
rm -f "$HOME/.config/opencode/.ecosystem-managed-files"
printf '%s\n' 'user-config-marker' > "$HOME/.config/opencode/opencode.jsonc"
printf '%s\n' 'user-custom-plugin' > "$HOME/.config/opencode/plugins/user-custom.js"
printf '%s\n' 'unknown-old-plugin' > "$HOME/.config/opencode/plugins/unknown-old.js"
bash "$REPO_DIR/install.sh" --skip-memory --sync >/dev/null

if [[ "$(<"$HOME/.config/opencode/opencode.jsonc")" != "user-config-marker" ]]; then
  echo "[FAIL] Sync overwrote opencode.jsonc"
  exit 1
fi
if [[ "$(<"$HOME/.config/opencode/plugins/user-custom.js")" != "user-custom-plugin" ]]; then
  echo "[FAIL] Sync overwrote an unmanaged custom file"
  exit 1
fi
if [[ ! -f "$HOME/.config/opencode/plugins/unknown-old.js" ]]; then
  echo "[FAIL] First sync pruned a file without manifest evidence"
  exit 1
fi
if [[ "$(<"$HOME/.config/opencode/agents/ai-matcher.md")" == "user-agent-marker" ]]; then
  echo "[FAIL] Sync did not update a managed agent"
  exit 1
fi
assert_exists "$HOME/.config/opencode/.ecosystem-managed-files"
echo "[OK] First sync updated managed files and preserved unknown files"

# A later sync prunes only paths recorded by the previous manifest.
printf '%s\n' 'retired-managed-plugin' > "$HOME/.config/opencode/plugins/retired-managed.js"
printf '%s\n' 'opencode/plugins/retired-managed.js' >> "$HOME/.config/opencode/.ecosystem-managed-files"
printf '%s\n' 'do-not-delete' > "$HOME/escape"
printf '%s\n' 'opencode/../../escape' >> "$HOME/.config/opencode/.ecosystem-managed-files"
printf 'opencode/opencode.jsonc\r\n' >> "$HOME/.config/opencode/.ecosystem-managed-files"
printf 'opencode/.ecosystem-managed-files\r\n' >> "$HOME/.config/opencode/.ecosystem-managed-files"
printf '%s\n' 'sync-profile-marker' > "$HOME/.config/opencode/profiles/work/opencode.jsonc"
for index in $(seq 1 12); do mkdir -p "$HOME/.local/share/opencode/install-backups/10000000$index-1"; done

# Sync dry-run must project backup/pruning while preserving every byte and path.
DRY_RUN_BEFORE="$(snapshot_home "$HOME")"
DRY_RUN_SYNC_OUTPUT="$(bash "$REPO_DIR/install.sh" --skip-memory --sync --dry-run 2>&1)"
DRY_RUN_AFTER="$(snapshot_home "$HOME")"
if [[ "$DRY_RUN_BEFORE" != "$DRY_RUN_AFTER" ]]; then
  echo "[FAIL] Sync dry-run changed the installation"
  exit 1
fi
if [[ "$DRY_RUN_SYNC_OUTPUT" != *"backup: opencode/plugins/retired-managed.js"* || "$DRY_RUN_SYNC_OUTPUT" != *"remove: opencode/plugins/retired-managed.js"* ]]; then
  echo "[FAIL] Sync dry-run did not project stale backup and removal"
  exit 1
fi
echo "[OK] Sync dry-run projected stale pruning without changes"

bash "$REPO_DIR/install.sh" --skip-memory --sync >/dev/null

if [[ -e "$HOME/.config/opencode/plugins/retired-managed.js" ]]; then
  echo "[FAIL] Sync did not prune a stale managed file"
  exit 1
fi
if [[ ! -f "$HOME/.config/opencode/plugins/user-custom.js" || ! -f "$HOME/.config/opencode/plugins/unknown-old.js" ]]; then
  echo "[FAIL] Sync pruned an unmanaged file"
  exit 1
fi
if [[ "$(<"$HOME/escape")" != "do-not-delete" ]]; then
  echo "[FAIL] Sync followed an unsafe manifest path"
  exit 1
fi
if [[ "$(<"$HOME/.config/opencode/opencode.jsonc")" != "user-config-marker" ]]; then
  echo "[FAIL] Sync pruned protected opencode.jsonc from a CRLF manifest entry"
  exit 1
fi
BACKUP_DIR_COUNT=0
for backup_dir in "$HOME/.local/share/opencode/install-backups"/*; do
  [[ -d "$backup_dir" ]] && BACKUP_DIR_COUNT=$((BACKUP_DIR_COUNT + 1))
done
if [[ $BACKUP_DIR_COUNT -gt 10 ]]; then
  echo "[FAIL] Sync retained more than 10 install backup directories"
  exit 1
fi
if ! find "$HOME/.local/share/opencode/install-backups" -path '*/opencode/plugins/retired-managed.js' -type f | grep -q .; then
  echo "[FAIL] Sync did not back up a stale managed file"
  exit 1
fi
if ! find "$HOME/.local/share/opencode/install-backups" -path '*/opencode/profiles/work/opencode.jsonc' -type f | grep -q .; then
  echo "[FAIL] Sync did not back up a replaced managed file"
  exit 1
fi
echo "[OK] Sync backed up changes and pruned only known stale files"

# Sync must refuse managed symlinks instead of following them outside the roots.
printf '%s\n' 'symlink-target' > "$HOME/symlink-target"
rm -f "$HOME/.config/opencode/plugins/guardrails.js"
ln -s "$HOME/symlink-target" "$HOME/.config/opencode/plugins/guardrails.js"
if bash "$REPO_DIR/install.sh" --skip-memory --sync --dry-run >/dev/null 2>&1; then
  echo "[FAIL] Sync dry-run accepted a managed symbolic link"
  exit 1
fi
if bash "$REPO_DIR/install.sh" --skip-memory --sync >/dev/null 2>&1; then
  echo "[FAIL] Sync followed a managed symbolic link"
  exit 1
fi
if [[ "$(<"$HOME/symlink-target")" != "symlink-target" ]]; then
  echo "[FAIL] Sync modified a symbolic-link target"
  exit 1
fi
rm -f "$HOME/.config/opencode/plugins/guardrails.js"
cp "$REPO_DIR/config/plugins/guardrails.js" "$HOME/.config/opencode/plugins/guardrails.js"
echo "[OK] Sync refused managed symbolic links"

rm -f "$HOME/.config/opencode/plugins/guardrails.js"
ln -s "$HOME/symlink-target" "$HOME/.config/opencode/plugins/guardrails.js"
if bash "$REPO_DIR/install.sh" --skip-memory --force --dry-run >/dev/null 2>&1; then
  echo "[FAIL] Force dry-run accepted a managed symbolic link"
  exit 1
fi
if bash "$REPO_DIR/install.sh" --skip-memory --force >/dev/null 2>&1; then
  echo "[FAIL] Force followed a managed symbolic link"
  exit 1
fi
if [[ "$(<"$HOME/symlink-target")" != "symlink-target" ]]; then
  echo "[FAIL] Force modified a symbolic-link target"
  exit 1
fi
rm -f "$HOME/.config/opencode/plugins/guardrails.js"
cp "$REPO_DIR/config/plugins/guardrails.js" "$HOME/.config/opencode/plugins/guardrails.js"
echo "[OK] Force refused managed symbolic links"

printf '%s\n' 'nested-target' > "$HOME/nested-target"
rm -rf "$HOME/opencode-custom/skills/defuddle"
mkdir -p "$HOME/nested-victim"
printf '%s\n' 'nested-target' > "$HOME/nested-victim/SKILL.md"
ln -s "$HOME/nested-victim" "$HOME/opencode-custom/skills/defuddle"
if bash "$REPO_DIR/install.sh" --skip-memory --sync --dry-run >/dev/null 2>&1; then
  echo "[FAIL] Sync dry-run accepted a symbolic-link directory"
  exit 1
fi
if bash "$REPO_DIR/install.sh" --skip-memory --sync >/dev/null 2>&1; then
  echo "[FAIL] Sync followed a symbolic-link directory"
  exit 1
fi
if [[ "$(<"$HOME/nested-victim/SKILL.md")" != "nested-target" ]]; then
  echo "[FAIL] Sync modified a file through a symbolic-link directory"
  exit 1
fi
rm -f "$HOME/opencode-custom/skills/defuddle"
cp -r "$REPO_DIR/skills/defuddle" "$HOME/opencode-custom/skills/defuddle"
echo "[OK] Sync refused symbolic-link directory components"

# A forced reinstall must back up customizations before replacement.
printf '%s\n' 'user-profile-marker' > "$HOME/.config/opencode/profiles/work/opencode.jsonc"
bash "$REPO_DIR/install.sh" --skip-memory --force >/dev/null
profile_backups=("$HOME/.config/opencode/profiles/work.bak-"*)
profile_backup="${profile_backups[${#profile_backups[@]} - 1]}"
if [[ ! -f "$profile_backup/opencode.jsonc" ]]; then
  echo "[FAIL] Forced reinstall did not create a profile backup"
  exit 1
fi
if [[ "$(<"$profile_backup/opencode.jsonc")" != "user-profile-marker" ]]; then
  echo "[FAIL] Forced reinstall backup did not preserve profile customization"
  exit 1
fi
if [[ "$(<"$HOME/.config/opencode/profiles/work/opencode.jsonc")" == "user-profile-marker" ]]; then
  echo "[FAIL] Forced reinstall did not replace the managed profile"
  exit 1
fi
echo "[OK] Forced reinstall backed up customization before replacement"

# Cleanup
rm -rf "$HOME"

echo ""
echo "[PASS] All install tests passed!"
