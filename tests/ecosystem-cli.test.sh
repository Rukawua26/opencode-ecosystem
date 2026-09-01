#!/usr/bin/env bash
# Test the opencode-ecosystem CLI (source-of-truth control)
set -euo pipefail

TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLI="$REPO_DIR/tools/scripts/opencode-ecosystem.sh"

# A fake ecosystem repo we control (not the real one).
FAKE_REPO="$TEST_ROOT/eco"
FAKE_HOME="$TEST_ROOT/home"
export HOME="$FAKE_HOME"

fail() { echo "[FAIL] $*"; exit 1; }
pass() { echo "[OK] $*"; }

# Build a minimal fake repo + runtime install
mkdir -p "$FAKE_REPO/config/commands" "$FAKE_REPO/config/agents" \
         "$FAKE_REPO/skills/sample" "$FAKE_HOME/.config/opencode/commands" \
         "$FAKE_HOME/.config/opencode/agents" "$FAKE_HOME/opencode-custom/skills/sample"
printf 'cmd-one\n' > "$FAKE_REPO/config/commands/one.md"
printf 'agent-one\n' > "$FAKE_REPO/config/agents/a.md"
printf 'SKILL\n' > "$FAKE_REPO/skills/sample/SKILL.md"
# runtime copies identical
printf 'cmd-one\n' > "$FAKE_HOME/.config/opencode/commands/one.md"
printf 'agent-one\n' > "$FAKE_HOME/.config/opencode/agents/a.md"
printf 'SKILL\n' > "$FAKE_HOME/opencode-custom/skills/sample/SKILL.md"

snapshot_home() {
  local root="$1" entry path rel target
  while IFS= read -r -d '' entry; do
    path="${entry}"; rel="${path#"$root"/}"
    if [[ -L "$path" ]]; then target="$(readlink "$path")"; printf '%s|link|%s\n' "$rel" "$target"
    elif [[ -d "$path" ]]; then printf '%s|dir|%s\n' "$rel" "$(ls -1 "$path" | wc -l | tr -d ' ')"
    else printf '%s|file|%s\n' "$rel" "$(wc -c < "$path" | tr -d ' ')"
    fi
  done < <(find "$root" -mindepth 1 -print0 2>/dev/null) | sort
}

# 1) status --json is read-only and reflects drift
before=$(snapshot_home "$FAKE_HOME")
STATUS_JSON="$(bash "$CLI" status --json --repo "$FAKE_REPO" 2>/dev/null)"
after=$(snapshot_home "$FAKE_HOME")
[[ "$before" == "$after" ]] || fail "status --json modified HOME"
echo "$STATUS_JSON" | grep -q '"commands":' || fail "status json missing commands category"
echo "$STATUS_JSON" | grep -q '"modified":0' || fail "unexpected modified on clean state"
pass "status --json is read-only and reports categories"

# 2) status detects a modified and a missing managed file
printf 'cmd-two\n' > "$FAKE_HOME/.config/opencode/commands/one.md"
printf 'extra\n' > "$FAKE_REPO/config/agents/b.md"
STATUS_JSON="$(bash "$CLI" status --json --repo "$FAKE_REPO" 2>/dev/null)"
echo "$STATUS_JSON" | grep -q '"commands":{"missing":0,"modified":1,"extra":0' || fail "status did not flag modified command"
echo "$STATUS_JSON" | grep -q '"agents":{"missing":1,"modified":0,"extra":0' || fail "status did not flag missing agent"
pass "status flags modified and missing managed files"

# 3) capture --dry-run does not write; --apply writes into the repo
  printf 'new-cmd\n' > "$FAKE_HOME/.config/opencode/commands/two.md"
  CAPTURE_DRY="$(bash "$CLI" capture --repo "$FAKE_REPO" 2>/dev/null)"
  echo "$CAPTURE_DRY" | grep -q "two.md" || fail "capture dry-run did not list two.md"
[[ -f "$FAKE_REPO/config/commands/two.md" ]] && fail "capture --dry-run wrote into repo"
bash "$CLI" capture --apply --repo "$FAKE_REPO" >/dev/null 2>&1
[[ -f "$FAKE_REPO/config/commands/two.md" ]] || fail "capture --apply did not copy two.md"
pass "capture dry-run read-only and apply copies whitelisted runtime file"

# 4) capture never copies .env / node_modules / private paths
mkdir -p "$FAKE_HOME/.config/opencode/node_modules/pkg"
printf 'secret\n' > "$FAKE_HOME/.config/opencode/.env"
printf 'x\n' > "$FAKE_HOME/.config/opencode/node_modules/pkg/index.js"
CAPTURE_DRY="$(bash "$CLI" capture --repo "$FAKE_REPO" 2>/dev/null)"
echo "$CAPTURE_DRY" | grep -q ".env" && fail "capture listed .env"
echo "$CAPTURE_DRY" | grep -q "node_modules" && fail "capture listed node_modules"
pass "capture excludes .env and node_modules"

# 5) config-apply --dry-run read-only; --apply backs up before replacing
printf 'OLD\n' > "$FAKE_HOME/.config/opencode/opencode.jsonc"
printf 'NEW\n' > "$FAKE_REPO/config/opencode.jsonc"
CONFIG_DRY="$(bash "$CLI" config-apply --repo "$FAKE_REPO" 2>/dev/null)"
echo "$CONFIG_DRY" | grep -q "would replace" || fail "config-apply dry-run did not list target"
grep -q "OLD" "$FAKE_HOME/.config/opencode/opencode.jsonc" || fail "config-apply dry-run modified file"
bash "$CLI" config-apply --apply --repo "$FAKE_REPO" >/dev/null 2>&1
grep -q "NEW" "$FAKE_HOME/.config/opencode/opencode.jsonc" || fail "config-apply did not replace"
ls "$FAKE_HOME/.config/opencode/"opencode.jsonc.bak-* >/dev/null 2>&1 || fail "config-apply did not create backup"
pass "config-apply dry-run read-only and apply backs up before replacing"

# 6) publish refuses secrets before running validations
git -C "$FAKE_REPO" init -q
git -C "$FAKE_REPO" config user.email t@t.co
git -C "$FAKE_REPO" config user.name T
git -C "$FAKE_REPO" add -A >/dev/null 2>&1
git -C "$FAKE_REPO" commit -qm init >/dev/null 2>&1
printf 'key = "sk-abcdefghijklmnopqrstuvwxyz1234567890"\n' > "$FAKE_REPO/leak.txt"
PUBLISH_OUT="$(bash "$CLI" publish --yes --repo "$FAKE_REPO" 2>&1 || true)"
echo "$PUBLISH_OUT" | grep -qi "secret" || fail "publish did not refuse secret (out: $PUBLISH_OUT)"
[[ -z "$(git -C "$FAKE_REPO" diff --cached --name-only | grep leak)" ]] || fail "publish staged a leaked file"
[[ "$(git -C "$FAKE_REPO" log --oneline -1 | wc -l | tr -d ' ')" == "1" ]] || fail "publish created a commit"
pass "publish refuses secrets and leaves repo unstaged/uncommitted"

# 7) help works
bash "$CLI" help >/dev/null 2>&1 || fail "help failed"

echo "[PASS] All ecosystem CLI tests passed!"