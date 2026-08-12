#!/usr/bin/env bash
set -euo pipefail

# ===========================================
# OpenCode Ecosystem Installer
# https://github.com/Rukawua26/opencode-ecosystem
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/Rukawua26/opencode-ecosystem.git"
INSTALL_TAG="${INSTALL_TAG:-v1.9.0}"
OPENCODE_DIR="$HOME/.config/opencode"
OPENCODE_BIN_DIR="$HOME/.opencode/bin"
VERBOSE=false
FORCE=false
SYNC=false
SKIP_MEMORY=false
MANIFEST_FILE="$OPENCODE_DIR/.ecosystem-managed-files"
CURRENT_MANIFEST=""
SYNC_BACKUP_DIR=""
MAX_INSTALL_BACKUPS=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() { echo -e "${GREEN}[opencode-ecosystem]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[warn]${NC} $*" >&2; }
error() { echo -e "${RED}[error]${NC} $*" >&2; }
info() { { [[ "$VERBOSE" == true ]] && echo -e "${BLUE}[debug]${NC} $*" >&2; } || true; }

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose|-v) VERBOSE=true; shift ;;
    --force|-f) FORCE=true; shift ;;
    --sync) SYNC=true; shift ;;
    --skip-memory) SKIP_MEMORY=true; shift ;;
    --help|-h)
      echo "Usage: install.sh [--verbose] [--force | --sync] [--skip-memory]"
      echo ""
      echo "Options:"
      echo "  --verbose, -v    Show detailed output"
      echo "  --force, -f      Overwrite existing config"
      echo "  --sync           Update managed files and prune known stale files"
      echo "  --skip-memory    Skip memory adapter installation"
      echo "  --help, -h       Show this help"
      exit 0
      ;;
    *) error "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ "$FORCE" == true && "$SYNC" == true ]]; then
  error "--force and --sync cannot be used together"
  exit 1
fi

# Detect OS
detect_os() {
  local os_type
  os_type="$(uname -s)"
  case "$os_type" in
    Linux*)  echo "linux" ;;
    Darwin*) echo "macos" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *) error "Unsupported OS: $os_type"; exit 1 ;;
  esac
}

OS="$(detect_os)"
info "Detected OS: $OS"

# Check dependencies
check_deps() {
  local missing=()
  command -v node >/dev/null 2>&1 || missing+=("node")
  command -v npm >/dev/null 2>&1 || missing+=("npm")
  command -v git >/dev/null 2>&1 || missing+=("git")

  if [[ ${#missing[@]} -gt 0 ]]; then
    error "Missing dependencies: ${missing[*]}"
    error "Please install them before running this script."
    case "$OS" in
      linux)  error "  sudo apt install -y nodejs npm git" ;;
      macos)  error "  brew install node npm git" ;;
      windows) error "  winget install OpenJS.NodeJS Git.Git" ;;
    esac
    exit 1
  fi
  if [[ "$(node -p 'Number(process.versions.node.split(".")[0])')" -lt 22 ]]; then
    error "Node.js 22 or newer is required for the native node:sqlite module"
    exit 1
  fi
  info "Dependencies OK: node=$(node -v), npm=$(npm -v), git=$(git --version)"
}

# Create directories
create_dirs() {
  log "Creating directories..."
  mkdir -p "$OPENCODE_DIR"
  mkdir -p "$OPENCODE_DIR/plugins"
  mkdir -p "$OPENCODE_DIR/lib"
  mkdir -p "$OPENCODE_DIR/mcp"
  mkdir -p "$OPENCODE_DIR/agents"
  mkdir -p "$OPENCODE_DIR/profiles"
  mkdir -p "$OPENCODE_DIR/tools"
  mkdir -p "$OPENCODE_BIN_DIR"
  mkdir -p "$HOME/.local/share/opencode/plugins-data"
  info "Directories created at $OPENCODE_DIR"
}

# Clone or update repo
clone_repo() {
  local clone_dir="$SCRIPT_DIR"
  if [[ ! -f "$SCRIPT_DIR/config/opencode.jsonc" || ! -d "$SCRIPT_DIR/skills" ]]; then
    clone_dir="$(mktemp -d)"
    log "Cloning repo (tag $INSTALL_TAG) to $clone_dir..."
    git clone --depth 1 --branch "$INSTALL_TAG" "$REPO_URL" "$clone_dir"
    info "Repo cloned at tag $INSTALL_TAG"
  else
    info "Using local distribution files"
  fi
  printf '%s\n' "$clone_dir"
}

managed_path_for() {
  local path="$1"
  case "$path" in
    "$OPENCODE_DIR"/*) printf 'opencode/%s\n' "${path#"$OPENCODE_DIR"/}" ;;
    "$HOME/opencode-custom/skills"/*) printf 'skills/%s\n' "${path#"$HOME/opencode-custom/skills"/}" ;;
    "$OPENCODE_BIN_DIR"/*) printf 'bin/%s\n' "${path#"$OPENCODE_BIN_DIR"/}" ;;
    *) return 1 ;;
  esac
}

managed_destination_for() {
  local logical="$1"
  case "$logical" in
    opencode/*) printf '%s/%s\n' "$OPENCODE_DIR" "${logical#opencode/}" ;;
    skills/*) printf '%s/%s\n' "$HOME/opencode-custom/skills" "${logical#skills/}" ;;
    bin/*) printf '%s/%s\n' "$OPENCODE_BIN_DIR" "${logical#bin/}" ;;
    *) return 1 ;;
  esac
}

is_safe_managed_path() {
  local logical="$1"
  [[ "$logical" == opencode/* || "$logical" == skills/* || "$logical" == bin/* ]] || return 1
  [[ "$logical" != *"../"* && "$logical" != *"/.."* && "$logical" != *"//"* ]] || return 1
  [[ "$logical" != *\\* && "$logical" != *:* && "$logical" != /* ]] || return 1
  return 0
}

register_managed() {
  local logical
  logical="$(managed_path_for "$1")" || return 0
  printf '%s\n' "$logical" >> "$CURRENT_MANIFEST"
}

preserve_manifest_prefix() {
  local prefix="$1"
  [[ -f "$MANIFEST_FILE" ]] || return 0
  while IFS= read -r logical; do
    logical="${logical%$'\r'}"
    if [[ "$logical" == "$prefix"* ]]; then
      printf '%s\n' "$logical" >> "$CURRENT_MANIFEST"
    fi
  done < "$MANIFEST_FILE"
  return 0
}

is_protected_managed_path() {
  case "$1" in
    opencode/opencode.jsonc|opencode/.ecosystem-managed-files) return 0 ;;
    *) return 1 ;;
  esac
}

retain_install_backups() {
  local root="$HOME/.local/share/opencode/install-backups" backups=()
  [[ -d "$root" ]] || return 0
  local backup path index
  while IFS= read -r backup; do backups+=("$backup"); done < <(
    for path in "$root"/*; do
      if [[ -d "$path" ]]; then basename "$path"; fi
    done | sort -r
  )
  for ((index=MAX_INSTALL_BACKUPS; index<${#backups[@]}; index++)); do
    rm -rf "$root/${backups[$index]}"
  done
}

assert_no_symlink_components() {
  local path="$1" root="$2" relative current segment
  relative="${path#"$root"/}"
  [[ "$relative" != "$path" ]] || { error "Managed path is outside its root: $path"; exit 1; }
  current="$root"
  IFS='/' read -r -a segments <<< "$relative"
  for segment in "${segments[@]}"; do
    current="$current/$segment"
    if [[ -L "$current" ]]; then
      error "Refusing managed path with symbolic-link component: $current"
      exit 1
    fi
  done
}

assert_managed_path_safe() {
  local path="$1"
  case "$path" in
    "$OPENCODE_DIR"/*) assert_no_symlink_components "$path" "$OPENCODE_DIR" ;;
    "$HOME/opencode-custom/skills"/*) assert_no_symlink_components "$path" "$HOME/opencode-custom/skills" ;;
    "$OPENCODE_BIN_DIR"/*) assert_no_symlink_components "$path" "$OPENCODE_BIN_DIR" ;;
    *) error "Managed path is outside allowed roots: $path"; exit 1 ;;
  esac
}

backup_sync_file() {
  local path="$1" logical backup
  [[ "$SYNC" == true && -f "$path" ]] || return 0
  assert_managed_path_safe "$path"
  logical="$(managed_path_for "$path")" || return 0
  if [[ -z "$SYNC_BACKUP_DIR" ]]; then
    SYNC_BACKUP_DIR="$HOME/.local/share/opencode/install-backups/$(date +%s)-$$"
    mkdir -p "$SYNC_BACKUP_DIR"
    retain_install_backups
  fi
  backup="$SYNC_BACKUP_DIR/$logical"
  mkdir -p "$(dirname "$backup")"
  cp -p "$path" "$backup"
}

prune_stale_managed() {
  [[ "$SYNC" == true && -f "$MANIFEST_FILE" ]] || return 0
  local logical destination
  while IFS= read -r logical; do
    logical="${logical%$'\r'}"
    [[ -n "$logical" ]] || continue
    if ! is_safe_managed_path "$logical"; then
      warn "Ignoring unsafe managed path in manifest: $logical"
      continue
    fi
    if is_protected_managed_path "$logical"; then
      warn "Ignoring protected path in manifest: $logical"
      continue
    fi
    if grep -Fqx "$logical" "$CURRENT_MANIFEST"; then
      continue
    fi
    destination="$(managed_destination_for "$logical")" || continue
    assert_managed_path_safe "$destination"
    if [[ -f "$destination" ]]; then
      backup_sync_file "$destination"
      rm -f "$destination"
      info "Removed stale managed file: $logical"
    fi
  done < "$MANIFEST_FILE"
}

finalize_manifest() {
  prune_stale_managed
  if [[ "$SYNC" == false && "$FORCE" == false && -f "$MANIFEST_FILE" ]]; then
    local previous
    while IFS= read -r previous; do
      previous="${previous%$'\r'}"
      if is_safe_managed_path "$previous" && ! is_protected_managed_path "$previous"; then
        printf '%s\n' "$previous" >> "$CURRENT_MANIFEST"
      fi
    done < "$MANIFEST_FILE"
  fi
  local next_manifest="$MANIFEST_FILE.next"
  sort -u "$CURRENT_MANIFEST" > "$next_manifest"
  mv "$next_manifest" "$MANIFEST_FILE"
  info "Managed manifest updated: $MANIFEST_FILE"
}

# Copy a file only if it does not exist or FORCE is true
copy_if_ok() {
  local src="$1" dst="$2" managed="${3:-true}"
  if [[ "$managed" == true ]]; then
    register_managed "$dst"
  fi
  if [[ "$SYNC" == true ]]; then
    assert_managed_path_safe "$dst"
  fi
  if [[ -f "$dst" && "$FORCE" == false && "$SYNC" == false ]]; then
    info "Skipping (exists): $dst"
    return 0
  fi
  if [[ "$SYNC" == true ]]; then
    backup_sync_file "$dst"
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  info "Installed: $dst"
}

# Copy all matching files into a dir, skipping existing unless FORCE
copy_dir_if_ok() {
  local src_glob="$1" dst_dir="$2" label="$3"
  if [[ "$FORCE" == true && -d "$dst_dir" ]]; then
    local existing_files=("$dst_dir"/*)
    if [[ -e "${existing_files[0]}" ]]; then
      local ts_backup
      ts_backup="$(date +%s)"
      mkdir -p "$dst_dir.bak-$ts_backup"
      cp -r "$dst_dir/"* "$dst_dir.bak-$ts_backup/"
      info "$label backed up to $(basename "$dst_dir").bak-$ts_backup"
    fi
  fi
  for src in $src_glob; do
    [[ -f "$src" ]] || continue
    local name
    name="$(basename "$src")"
    copy_if_ok "$src" "$dst_dir/$name"
  done
}

# Copy a directory as one managed unit, preserving an existing installation.
copy_tree_if_ok() {
  local src_dir="$1" dst_dir="$2" label="$3"
  src_dir="${src_dir%/}"
  if [[ -d "$dst_dir" && "$FORCE" == false && "$SYNC" == false ]]; then
    info "Skipping $label (exists): $dst_dir"
    return 1
  fi
  if [[ "$SYNC" == true ]]; then
    local src rel
    while IFS= read -r -d '' src; do
      rel="${src#"$src_dir"/}"
      copy_if_ok "$src" "$dst_dir/$rel"
    done < <(find "$src_dir" -type f -print0)
    info "$label synchronized: $dst_dir"
    return 0
  fi
  if [[ -d "$dst_dir" && "$FORCE" == true ]]; then
    local backup="$dst_dir.bak-$(date +%s)"
    cp -r "$dst_dir" "$backup"
    rm -rf "$dst_dir"
    info "$label backed up to $(basename "$backup")"
  fi
  mkdir -p "$dst_dir"
  cp -r "$src_dir/." "$dst_dir/"
  local installed
  while IFS= read -r -d '' installed; do
    register_managed "$installed"
  done < <(find "$dst_dir" -type f -print0)
  info "$label installed: $dst_dir"
}

# Copy config
copy_config() {
  local repo_dir="$1"
  log "Installing config..."

  # opencode.jsonc
  if [[ -f "$OPENCODE_DIR/opencode.jsonc" && "$FORCE" == false ]]; then
    warn "opencode.jsonc already exists; preserving it (use --force to replace)"
  else
    if [[ -f "$OPENCODE_DIR/opencode.jsonc" && "$FORCE" == true ]]; then
      cp "$OPENCODE_DIR/opencode.jsonc" "$OPENCODE_DIR/opencode.jsonc.bak"
      info "Backed up opencode.jsonc to opencode.jsonc.bak"
    fi
    copy_if_ok "$repo_dir/config/opencode.jsonc" "$OPENCODE_DIR/opencode.jsonc" false
    info "opencode.jsonc installed"
  fi

  # Agents
  log "Installing agents..."
  if [[ -d "$repo_dir/config/agents" ]]; then
    copy_dir_if_ok "$repo_dir/config/agents/*.md" "$OPENCODE_DIR/agents" "Agents"
    info "Agents copied"
  fi

  # Plugins
  log "Installing plugins..."
  if [[ -d "$repo_dir/config/plugins" ]]; then
    copy_dir_if_ok "$repo_dir/config/plugins/*.js" "$OPENCODE_DIR/plugins" "Plugins"
    info "Plugins copied"
  fi

  if [[ -d "$repo_dir/config/lib" ]]; then
    copy_dir_if_ok "$repo_dir/config/lib/*.js" "$OPENCODE_DIR/lib" "Plugin libraries"
    info "Plugin libraries copied"
  fi

  # MCP servers
  log "Installing MCP servers..."
  if [[ -d "$repo_dir/config/mcp" ]]; then
    for f in "$repo_dir/config/mcp/"*.js; do
      [[ -f "$f" ]] || continue
      copy_if_ok "$f" "$OPENCODE_DIR/mcp/$(basename "$f")"
    done
    copy_if_ok "$repo_dir/config/mcp/package.json" "$OPENCODE_DIR/mcp/package.json"
    copy_if_ok "$repo_dir/config/mcp/package-lock.json" "$OPENCODE_DIR/mcp/package-lock.json"
    info "MCP servers copied"
    if [[ -f "$OPENCODE_DIR/mcp/package.json" ]]; then
      log "Installing MCP router dependencies..."
      (cd "$OPENCODE_DIR/mcp" && npm ci --omit=dev --ignore-scripts) || {
        error "Failed to install MCP router dependencies in $OPENCODE_DIR/mcp"
        error "Run 'npm ci --omit=dev --ignore-scripts' manually in $OPENCODE_DIR/mcp"
        exit 1
      }
      info "MCP router dependencies installed"
    fi
  fi

  # Profiles
  log "Installing profiles..."
  if [[ -d "$repo_dir/config/profiles" ]]; then
    for profile_dir in "$repo_dir/config/profiles"/*/; do
      [[ -d "$profile_dir" ]] || continue
      local profile_name
      profile_name="$(basename "$profile_dir")"
      if copy_tree_if_ok "$profile_dir" "$OPENCODE_DIR/profiles/$profile_name" "Profile $profile_name"; then
        local profile="$OPENCODE_DIR/profiles/$profile_name/opencode.jsonc"
        if [[ -f "$profile" ]]; then
          node -e 'const fs=require("node:fs"); const file=process.argv[1]; fs.writeFileSync(file, fs.readFileSync(file,"utf8").replaceAll("__OPENCODE_DIR__", process.argv[2]));' "$profile" "$OPENCODE_DIR"
        fi
      fi
    done
    info "Profiles copied"
  fi

  # Skills
  log "Installing skills..."
  if [[ -d "$repo_dir/skills" ]]; then
    mkdir -p "$HOME/opencode-custom/skills"
    for skill_dir in "$repo_dir/skills"/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill_name="$(basename "$skill_dir")"
      copy_tree_if_ok "$skill_dir" "$HOME/opencode-custom/skills/$skill_name" "Skill $skill_name" || true
    done
  fi

  # .env.example
  if [[ -f "$repo_dir/.env.example" ]]; then
    copy_if_ok "$repo_dir/.env.example" "$OPENCODE_DIR/.env.example"
    info ".env.example copied (configure your API keys manually)"
  fi

  # Global doctor command
  if [[ -f "$repo_dir/tools/scripts/doctor.js" && -f "$repo_dir/tools/scripts/opencode-doctor.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/doctor.js" "$OPENCODE_DIR/tools/doctor.js"
    copy_if_ok "$repo_dir/tools/scripts/opencode-doctor.sh" "$OPENCODE_BIN_DIR/opencode-doctor"
    chmod +x "$OPENCODE_BIN_DIR/opencode-doctor"
    info "opencode-doctor installed globally at $OPENCODE_BIN_DIR/opencode-doctor"
  fi
  if [[ -f "$repo_dir/tools/scripts/opencode-metrics.js" && -f "$repo_dir/tools/scripts/opencode-metrics.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/opencode-metrics.js" "$OPENCODE_DIR/tools/opencode-metrics.js"
    copy_if_ok "$repo_dir/tools/scripts/opencode-metrics.sh" "$OPENCODE_BIN_DIR/opencode-metrics"
    chmod +x "$OPENCODE_BIN_DIR/opencode-metrics"
    info "opencode-metrics installed globally at $OPENCODE_BIN_DIR/opencode-metrics"
  fi
}

# Install memory adapter
install_memory() {
  if [[ "$SKIP_MEMORY" == true ]]; then
    preserve_manifest_prefix "opencode/mcp/memory-adapter/"
    preserve_manifest_prefix "bin/memory-adapter"
    warn "Skipping memory adapter (--skip-memory)"
    return
  fi

  local repo_dir="$1"
  log "Installing memory adapter..."

  if [[ ! -d "$repo_dir/packages/memory-adapter" ]]; then
    warn "Memory adapter package not found, skipping"
    return
  fi

  local mem_dir="$OPENCODE_DIR/mcp/memory-adapter"
  if copy_tree_if_ok "$repo_dir/packages/memory-adapter" "$mem_dir" "Memory adapter"; then
    # The adapter uses only Node.js built-ins and has no runtime dependencies.
    info "Memory adapter installed at $mem_dir"
  else
    info "Memory adapter preserved at $mem_dir"
  fi

  # Link global CLI through a wrapper so relative imports stay inside the package.
  if [[ -f "$mem_dir/src/cli.js" && -f "$repo_dir/tools/scripts/memory-adapter.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/memory-adapter.sh" "$OPENCODE_BIN_DIR/memory-adapter"
    chmod +x "$OPENCODE_BIN_DIR/memory-adapter"
    info "memory-adapter CLI installed globally at $OPENCODE_BIN_DIR/memory-adapter"
  fi

  # Link MCP server in config
  info "Memory adapter MCP server linked"
}

# Verify installation
verify_install() {
  log "Verifying installation..."

  local checks=0
  local passed=0

  check() { checks=$((checks+1)); [[ -f "$1" ]] && passed=$((passed+1)) || warn "Missing: $1"; }

  check "$OPENCODE_DIR/opencode.jsonc"
  check "$OPENCODE_DIR/.env.example"
  check "$OPENCODE_DIR/tools/doctor.js"
  check "$OPENCODE_BIN_DIR/opencode-doctor"
  check "$OPENCODE_DIR/lib/session-metrics.js"
  check "$OPENCODE_BIN_DIR/opencode-metrics"
  [[ -d "$OPENCODE_DIR/agents" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing agents dir"
  [[ -d "$OPENCODE_DIR/plugins" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing plugins dir"
  [[ -d "$OPENCODE_DIR/mcp" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing mcp dir"
  [[ -d "$HOME/opencode-custom/skills" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing skills dir"

  if [[ "$SKIP_MEMORY" != true ]]; then
    check "$OPENCODE_DIR/mcp/memory-adapter/package.json"
    check "$OPENCODE_BIN_DIR/memory-adapter"
  fi

  # Verify MCP router SDK can import
  check "$OPENCODE_DIR/mcp/package.json"
  check "$OPENCODE_DIR/mcp/local-model-router.js"
  if [[ -f "$OPENCODE_DIR/mcp/node_modules/@modelcontextprotocol/sdk/package.json" ]]; then
    checks=$((checks+1))
    if node -e "import('$OPENCODE_DIR/mcp/local-model-router.js').then(m => { if (m.TOOL_DEFINITIONS.length === 5) process.exit(0); else process.exit(1); }).catch(() => process.exit(1))" 2>/dev/null; then
      passed=$((passed+1))
      info "MCP router SDK import OK"
    else
      warn "MCP router SDK import failed"
    fi
  else
    checks=$((checks+1))
    warn "Missing MCP router SDK"
  fi

  local agent_count plugin_count skill_count
  agent_count=$(find "$OPENCODE_DIR/agents" -name "*.md" 2>/dev/null | wc -l) || agent_count=0
  plugin_count=$(find "$OPENCODE_DIR/plugins" -name "*.js" ! -name "*-helpers.js" 2>/dev/null | wc -l) || plugin_count=0
  skill_count=$(find "$HOME/opencode-custom/skills" -maxdepth 1 -type d 2>/dev/null | wc -l) || skill_count=0
  skill_count=$((skill_count > 0 ? skill_count - 1 : 0))

  echo ""
  log "Installation summary:"
  echo "  Agents:  $agent_count"
  echo "  Plugins: $plugin_count"
  echo "  Skills:  $skill_count"
  echo "  Checks:  $passed/$checks"

  if [[ $passed -eq $checks ]]; then
    echo ""
    log "Installation successful!"
    log "Next steps:"
    echo "  1. cp $OPENCODE_DIR/.env.example $OPENCODE_DIR/.env"
    echo "  2. Edit ~/.config/opencode/.env with your API keys"
    echo "  3. Run: opencode"
  else
    warn "Some checks failed. Review the warnings above."
    exit 1
  fi
}

# Main
main() {
  echo ""
  echo "  ╔══════════════════════════════════════╗"
  echo "  ║    OpenCode Ecosystem Installer      ║"
  echo "  ║    Rukawua26/opencode-ecosystem      ║"
  echo "  ╚══════════════════════════════════════╝"
  echo ""

  check_deps
  create_dirs
  CURRENT_MANIFEST="$(mktemp)"
  trap 'rm -f "$CURRENT_MANIFEST"' EXIT

  REPO_DIR="$(clone_repo)"
  info "Using repo dir: $REPO_DIR"

  copy_config "$REPO_DIR"
  install_memory "$REPO_DIR"
  verify_install
  finalize_manifest

  echo ""
  log "Done. Happy coding!"
}

main
