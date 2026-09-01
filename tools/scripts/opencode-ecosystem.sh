#!/usr/bin/env bash
# ===========================================
# OpenCode Ecosystem CLI — source of truth control
# status | sync | config-apply | capture | publish | help
# ===========================================
set -euo pipefail

OPENCODE_DIR="${OPENCODE_DIR:-$HOME/.config/opencode}"
SKILLS_DIR="$HOME/opencode-custom/skills"
BIN_DIR="$HOME/.opencode/bin"
DOCTOR="$BIN_DIR/opencode-doctor"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[opencode-ecosystem]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[warn]${NC} $*" >&2; }
error(){ echo -e "${RED}[error]${NC} $*" >&2; }

usage() {
  cat <<'EOF'
Usage: opencode-ecosystem <command> [options]

Commands:
  status [--json] [--repo DIR]
      Read-only drift report between the ecosystem repo and the live
      OpenCode runtime (categories, extra files, protected config, repo state).

  sync [--apply] [--verbose]
      Update the live runtime from the repo using install.sh --sync.
      Defaults to --dry-run (shows what would change). --apply runs it.

  config-apply [--apply]
      Replace the protected opencode.jsonc and profile configs from the repo,
      backing up each existing target with a timestamp. Defaults to --dry-run.

  capture [--apply] [--repo DIR]
      Copy public managed files from the live runtime back into the repo
      (whitelist: agents, commands, plugins, plugins.disabled, lib, skills).
      Never touches .env, node_modules, backups, receipts, DB or logs.

  publish [--yes] [--message MSG] [--wait-ci] [--repo DIR]
      Validate (secrets, tests, lint, check-docs, shellcheck), then commit and
      push. --yes skips the interactive confirmation.

  help
      Show this help.

Options:
  --repo DIR   Ecosystem repository location (default: $HOME/opencode-ecosystem,
               or $OPENCODE_ECOSYSTEM_REPO).
EOF
}

ALL_ARGS=("$@")
CMD_ARGS=()
REPO_DIR=""
for ((i = 0; i < ${#ALL_ARGS[@]}; i++)); do
  case "${ALL_ARGS[$i]}" in
    --repo)
      REPO_DIR="${ALL_ARGS[$((i + 1))]:-}"
      i=$((i + 1))
      ;;
    *)
      CMD_ARGS+=("${ALL_ARGS[$i]}")
      ;;
  esac
done
CMD="${CMD_ARGS[0]:-help}"
CMD_ARGS=("${CMD_ARGS[@]:1}")

if [[ -z "$REPO_DIR" ]]; then
  REPO_DIR="${OPENCODE_ECOSYSTEM_REPO:-$HOME/opencode-ecosystem}"
fi
case "$CMD" in
  help|-h|--help) ;;
  *)
    if [[ ! -d "$REPO_DIR" ]]; then
      error "Ecosystem repo not found at $REPO_DIR (set OPENCODE_ECOSYSTEM_REPO or use --repo)"
      exit 1
    fi
    ;;
esac

# ---- helpers -------------------------------------------------------------

tree_files() { # dir -> relative file paths (recursive), skip .git, node_modules
  local dir="$1"
  [[ -d "$dir" ]] || return 0
  local tmpf
  tmpf=$(mktemp "${TMPDIR:-/tmp}/opencode.XXXXXX")
  (cd "$dir" && find . -type f ! -path './.git/*' ! -path '*/node_modules/*' ! -name '.DS_Store' 2>/dev/null \
    | sed 's|^\./||' | sort > "$tmpf") || true
  cat "$tmpf"
  rm -f "$tmpf"
}

category_report() { # name srcDir dstDir [onlyDeployed]
  local name="$1" src="$2" dst="$3" only="${4:-}" f rel missing=0 modified=0 extra=0
  local -a extraFiles=()
  local tmpf1 tmpf2
  tmpf1=$(mktemp "${TMPDIR:-/tmp}/opencode.XXXXXX") && tree_files "$src" > "$tmpf1"
  tmpf2=$(mktemp "${TMPDIR:-/tmp}/opencode.XXXXXX") && tree_files "$dst" > "$tmpf2"
  while IFS= read -r f; do
    rel="${f#./}"
    if [[ "$only" == "1" ]]; then
      [[ -f "$dst/$rel" ]] || continue
    fi
    if [[ -f "$dst/$rel" ]]; then
      if ! cmp -s "$src/$rel" "$dst/$rel"; then modified=$((modified+1)); fi
    else
      missing=$((missing+1))
    fi
  done < "$tmpf1"
  while IFS= read -r f; do
    rel="${f#./}"
    if [[ "$only" == "1" ]]; then
      case "$rel" in
        config-inspect.js|doctor.js|opencode-metrics.js|profile.js|skills.js) ;;
        *) continue ;;
      esac
    fi
    if [[ ! -e "$src/$rel" ]]; then
      extra=$((extra+1)); extraFiles+=("$rel")
    fi
  done < "$tmpf2"
  rm -f "$tmpf1" "$tmpf2"
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$missing" "$modified" "$extra" "${extraFiles[*]:-}"
}

# ---- status ---------------------------------------------------------------

cmd_status() {
  local json=false
  for a in "${CMD_ARGS[@]:-}"; do [[ "$a" == "--json" ]] && json=true; done

  local branch ahead behind clean repo_line
  if git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo det)"
    clean="$(git -C "$REPO_DIR" status --porcelain | wc -l | tr -d ' ')"
    ahead=0; behind=0
    if git -C "$REPO_DIR" rev-parse --verify "${branch}@{upstream}" >/dev/null 2>&1; then
      read -r ahead behind <<< "$(git -C "$REPO_DIR" rev-list --left-right --count "@{upstream}...HEAD" 2>/dev/null || echo "0 0")"
    fi
    repo_line="branch=$branch clean_dirty=$clean ahead=$ahead behind=$behind"
  else
    repo_line="not_a_git_repo"
  fi

  local doctor_ok="n/a"
  if [[ -x "$DOCTOR" ]]; then
    if "$DOCTOR" --json >/dev/null 2>&1; then doctor_ok="true"; else doctor_ok="false"; fi
  fi

  local -a cats=(
    "agents|config/agents|$OPENCODE_DIR/agents"
    "commands|config/commands|$OPENCODE_DIR/commands"
    "plugins|config/plugins|$OPENCODE_DIR/plugins"
    "plugins.disabled|config/plugins.disabled|$OPENCODE_DIR/plugins.disabled"
    "lib|config/lib|$OPENCODE_DIR/lib"
    "skills|skills|$SKILLS_DIR"
  )
  local name src dst
  local -a order=(agents commands plugins plugins.disabled lib mcp tools profiles skills)
  local -a results=()
  local i idx
  for ((i = 0; i < ${#order[@]}; i++)); do results[i]=""; done
  for entry in "${cats[@]}"; do
    IFS='|' read -r name src dst <<< "$entry"
    for ((i = 0; i < ${#order[@]}; i++)); do [[ "${order[$i]}" == "$name" ]] && idx=$i; done
    results[$idx]="$(category_report "$name" "$REPO_DIR/$src" "$dst")"
  done

  # mcp (source files only, node_modules/package-lock ignored)
  local mcp_report="mcp	0	0	0	"
  if [[ -d "$REPO_DIR/config/mcp" ]]; then
    local mm=0 mmod=0 mextra=0
    local -a mextraFiles=()
    while IFS= read -r f; do
      rel="${f#./}"
      if [[ "$rel" == "package-lock.json" ]]; then continue; fi
      if [[ -f "$OPENCODE_DIR/mcp/$rel" ]]; then
        if ! cmp -s "$REPO_DIR/config/mcp/$rel" "$OPENCODE_DIR/mcp/$rel"; then mmod=$((mmod+1)); fi
      else mm=$((mm+1)); fi
    done < <(tree_files "$REPO_DIR/config/mcp")
    mcp_report="mcp	$mm	$mmod	$mextra	${mextraFiles[*]:-}"
  fi
  # tools (only the deployed .js subset)
  local tools_report
  tools_report="$(category_report tools "$REPO_DIR/tools/scripts" "$OPENCODE_DIR/tools" 1)"
  # profiles (recursive tree of profile configs)
  local prof_report="profiles	0	0	0	"
  if [[ -d "$REPO_DIR/config/profiles" ]]; then
    local pmiss=0 pmod=0
    while IFS= read -r f; do
      rel="${f#./}"
      local dst_cfg="$OPENCODE_DIR/profiles/$rel"
      if [[ -e "$dst_cfg" ]]; then
        if ! cmp -s <(sed "s|__OPENCODE_DIR__|$OPENCODE_DIR|g" "$REPO_DIR/config/profiles/$rel") "$dst_cfg"; then pmod=$((pmod+1)); fi
      else pmiss=$((pmiss+1)); fi
    done < <(tree_files "$REPO_DIR/config/profiles")
    prof_report="profiles	$pmiss	$pmod	0	"
  fi
  for entry in "mcp|$mcp_report" "tools|$tools_report" "profiles|$prof_report"; do
    name="${entry%%|*}"; val="${entry#*|}"
    for ((i = 0; i < ${#order[@]}; i++)); do [[ "${order[$i]}" == "$name" ]] && idx=$i; done
    results[$idx]="$val"
  done

  # protected opencode.jsonc (informational)
  local cfg_drift="clean"
  if [[ -f "$REPO_DIR/config/opencode.jsonc" && -f "$OPENCODE_DIR/opencode.jsonc" ]] \
     && ! cmp -s "$REPO_DIR/config/opencode.jsonc" "$OPENCODE_DIR/opencode.jsonc"; then
    cfg_drift="DIFFERS (protected/manual)"
  fi

  if [[ "$json" == true ]]; then
    printf '{'
    printf '"repo":"%s","doctor_ok":"%s","opencode_jsonc":"%s","categories":{' "$repo_line" "$doctor_ok" "$cfg_drift"
    local first=1 miss mod extra extraFiles
    for ((i = 0; i < ${#order[@]}; i++)); do
      IFS=$'\t' read -r _ miss mod extra extraFiles <<< "${results[$i]}"
      [[ "$first" -eq 1 ]] || printf ','
      first=0
      printf '"%s":{"missing":%s,"modified":%s,"extra":%s,"extraFiles":[%s]}' \
        "${order[$i]}" "$miss" "$mod" "$extra" \
        "$(for ef in $extraFiles; do printf '"%s",' "$ef"; done | sed 's/,$//')"
    done
    printf '}}\n'
    return
  fi

  log "Status (source of truth: $REPO_DIR)"
  echo "  repo:      $repo_line"
  echo "  doctor:    ok=$doctor_ok"
  for ((i = 0; i < ${#order[@]}; i++)); do
    read -r _ miss mod extra extraFiles <<< "${results[$i]}"
    echo "  ${order[$i]}: missing=$miss modified=$mod extra=$extra ${extraFiles:+[$extraFiles]}"
  done
  echo "  opencode.jsonc: $cfg_drift"
}

# ---- sync ---------------------------------------------------------------

cmd_sync() {
  local apply=false verbose=false
  for a in "${CMD_ARGS[@]:-}"; do
    case "$a" in
      --apply) apply=true ;;
      --verbose|-v) verbose=true ;;
    esac
  done
  local extra=()
  [[ "$apply" == true ]] || extra+=(--dry-run)
  [[ "$verbose" == true ]] && extra+=(--verbose)
  log "Running install.sh --sync --skip-memory ${extra[*]:-}"
  bash "$REPO_DIR/install.sh" --sync --skip-memory "${extra[@]}"
  if [[ "$apply" == true && -x "$DOCTOR" ]]; then
    if "$DOCTOR" --json >/dev/null 2>&1; then
      log "Doctor: OK after sync"
    else
      warn "Doctor reports problems after sync (see: opencode-doctor --json)"
    fi
  fi
}

# ---- config-apply ---------------------------------------------------------

cmd_config_apply() {
  local apply=false
  for a in "${CMD_ARGS[@]:-}"; do [[ "$a" == "--apply" ]] && apply=true; done
  local -a targets=("$OPENCODE_DIR/opencode.jsonc")
  while IFS= read -r pdir; do
    [[ -f "$REPO_DIR/config/profiles/$pdir/opencode.jsonc" ]] || continue
    targets+=("$OPENCODE_DIR/profiles/$pdir/opencode.jsonc")
  done < <(cd "$REPO_DIR/config/profiles" && find . -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sed 's|^\./||' | sort)

  log "config-apply: protected config replacement"
  for t in "${targets[@]}"; do
    local rel="${t#"$OPENCODE_DIR"/}"
    local src
    case "$rel" in
      opencode.jsonc) src="$REPO_DIR/config/opencode.jsonc" ;;
      profiles/*) src="$REPO_DIR/config/profiles/${rel#profiles/}" ;;
      *) continue ;;
    esac
    [[ -f "$src" ]] || continue
    if [[ "$apply" != true ]]; then
      echo "  [dry-run] would replace $rel (backup first)"
      continue
    fi
    mkdir -p "$(dirname "$t")"
    if [[ -f "$t" ]]; then
      local bak
      bak="$t.bak-$(date +%s)"
      cp "$t" "$bak"
      echo "  [ok] backed up $rel -> $(basename "$bak")"
    fi
    cp "$src" "$t"
    echo "  [ok] replaced $rel"
  done
  if [[ "$apply" == true ]]; then
    warn "Restart OpenCode for the new config to take effect."
  fi
}

# ---- capture --------------------------------------------------------------

cmd_capture() {
  local apply=false
  for a in "${CMD_ARGS[@]:-}"; do [[ "$a" == "--apply" ]] && apply=true; done
  local -a pairs=(
    "config/agents|$OPENCODE_DIR/agents"
    "config/commands|$OPENCODE_DIR/commands"
    "config/plugins|$OPENCODE_DIR/plugins"
    "config/plugins.disabled|$OPENCODE_DIR/plugins.disabled"
    "config/lib|$OPENCODE_DIR/lib"
    "skills|$SKILLS_DIR"
  )
  local entry src dst f rel changed=0
  log "capture: public managed files runtime -> repo (whitelist)"
  for entry in "${pairs[@]}"; do
    IFS='|' read -r src dst <<< "$entry"
    local tmpf
    tmpf=$(mktemp "${TMPDIR:-/tmp}/opencode.XXXXXX")
    tree_files "$dst" > "$tmpf"
    while IFS= read -r f; do
      rel="${f#./}"
      if [[ -e "$REPO_DIR/$src/$rel" ]]; then
        cmp -s "$dst/$rel" "$REPO_DIR/$src/$rel" && continue
      fi
      if [[ "$apply" != true ]]; then
        echo "  [dry-run] $src/$rel <- $dst/$rel"
      else
        mkdir -p "$(dirname "$REPO_DIR/$src/$rel")"
        cp "$dst/$rel" "$REPO_DIR/$src/$rel"
        echo "  [ok] captured $src/$rel"
      fi
      changed=$((changed+1))
    done < "$tmpf"
    rm -f "$tmpf"
  done
  if [[ "$apply" != true ]]; then
    log "Use --apply to write. Then review and 'publish'."
  elif [[ "$changed" -eq 0 ]]; then
    log "Nothing to capture."
  fi
}

# ---- publish ---------------------------------------------------------------

secret_scan() { # file -> exit 1 if secret found
  local f="$1"
  if grep -aqE 'sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|npm_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----' "$f" 2>/dev/null; then
    return 1
  fi
  if grep -aqE '^(api[_-]?key|token|secret|password)\s*=\s*["'"'"'][^"'"'"']{16,}["'"'"']' "$f" 2>/dev/null; then
    return 1
  fi
  return 0
}

cmd_publish() {
  local yes=false wait_ci=false message=""
  for a in "${CMD_ARGS[@]:-}"; do
    case "$a" in
      --yes) yes=true ;;
      --wait-ci) wait_ci=true ;;
      --message) ;; # handled in loop below
      --message=*) message="${a#--message=}" ;;
    esac
  done
  # second pass for --message MSG form
  local prev=""
  for a in "${CMD_ARGS[@]:-}"; do
    if [[ "$prev" == "--message" ]]; then message="$a"; fi
    prev="$a"
  done

  if ! git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    error "$REPO_DIR is not a git repository"
    exit 1
  fi

  local -a changed=()
  while IFS= read -r f; do changed+=("$f"); done < <(git -C "$REPO_DIR" status --porcelain | awk '{print $2}')
  if [[ "${#changed[@]}" -eq 0 ]]; then
    log "Nothing to publish."
    exit 0
  fi

  # secret scan over changed/untracked files
  local leaked=()
  local f
  for f in "${changed[@]}"; do
    if [[ -f "$REPO_DIR/$f" ]] && ! secret_scan "$REPO_DIR/$f"; then
      leaked+=("$f")
    fi
  done
  if [[ "${#leaked[@]}" -gt 0 ]]; then
    error "Potential secrets detected, refusing to publish:"
    for f in "${leaked[@]}"; do echo "  $f"; done
    exit 1
  fi

  log "Running validations..."
  (cd "$REPO_DIR" && npm test >/dev/null) || { error "npm test failed"; exit 1; }
  (cd "$REPO_DIR" && npm run lint >/dev/null) || { error "npm run lint failed"; exit 1; }
  (cd "$REPO_DIR" && npm run check-docs >/dev/null) || { error "npm run check-docs failed"; exit 1; }
  bash -n "$REPO_DIR/tools/scripts/opencode-ecosystem.sh" || { error "syntax check failed"; exit 1; }

  git -C "$REPO_DIR" status --short
  git -C "$REPO_DIR" diff --stat

  if [[ "$yes" != true ]]; then
    printf 'Commit and push? [y/N] '
    read -r ans
    [[ "$ans" =~ ^[yY] ]] || { log "Aborted."; exit 1; }
  fi

  if [[ -z "$message" ]]; then
    message="chore(ecosystem): update managed assets"
  fi
  git -C "$REPO_DIR" add -A
  git -C "$REPO_DIR" commit -m "$message"
  git -C "$REPO_DIR" push
  log "Published."
  if [[ "$wait_ci" == true ]]; then
    (cd "$REPO_DIR" && gh run watch --exit-status >/dev/null 2>&1) || { warn "CI not green (see gh run list)."; }
  fi
}

case "$CMD" in
  status) cmd_status ;;
  sync) cmd_sync ;;
  config-apply) cmd_config_apply ;;
  capture) cmd_capture ;;
  publish) cmd_publish ;;
  help|-h|--help) usage ;;
  *) usage; exit 2 ;;
esac