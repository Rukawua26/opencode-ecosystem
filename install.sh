#!/usr/bin/env bash
set -euo pipefail

# ===========================================
# OpenCode Ecosystem Installer
# https://github.com/Rukawua26/opencode-ecosystem
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/Rukawua26/opencode-ecosystem.git"
INSTALL_TAG="${INSTALL_TAG:-v1.10.0}"
OPENCODE_DIR="$HOME/.config/opencode"
OPENCODE_BIN_DIR="$HOME/.opencode/bin"
VERBOSE=false
FORCE=false
SYNC=false
DRY_RUN=false
SKIP_MEMORY=false
MANIFEST_FILE="$OPENCODE_DIR/.ecosystem-managed-files"
CURRENT_MANIFEST=""
CURRENT_MANAGED=()
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
plan() { echo "[dry-run] $*" >&2; }

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose|-v) VERBOSE=true; shift ;;
    --force|-f) FORCE=true; shift ;;
    --sync) SYNC=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --skip-memory) SKIP_MEMORY=true; shift ;;
    --help|-h)
      echo "Usage: install.sh [--verbose] [--force | --sync] [--dry-run] [--skip-memory]"
      echo ""
      echo "Options:"
      echo "  --verbose, -v    Show detailed output"
      echo "  --force, -f      Overwrite existing config"
      echo "  --sync           Update managed files and prune known stale files"
      echo "  --dry-run        Preview operations without changing the system"
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

# Node 22+ may write a compile cache even for version probes. A preview must be
# strictly read-only, including temporary directories.
if [[ "$DRY_RUN" == true ]]; then
  export NODE_DISABLE_COMPILE_CACHE=1
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
  local directories=(
    "$OPENCODE_DIR" "$OPENCODE_DIR/plugins" "$OPENCODE_DIR/plugins.disabled" "$OPENCODE_DIR/lib"
    "$OPENCODE_DIR/commands" "$OPENCODE_DIR/mcp" "$OPENCODE_DIR/agents" "$OPENCODE_DIR/profiles"
    "$OPENCODE_DIR/tools" "$OPENCODE_BIN_DIR"
    "$HOME/.local/share/opencode/plugins-data"
  )
  local directory
  for directory in "${directories[@]}"; do
    case "$directory" in
      "$OPENCODE_DIR"|"$OPENCODE_DIR"/*|"$OPENCODE_BIN_DIR"|"$OPENCODE_BIN_DIR"/*) assert_no_symlink_components "$directory" "$HOME" ;;
    esac
    if [[ "$DRY_RUN" == true ]]; then
      [[ -d "$directory" ]] || plan "create directory: $directory"
    else
      mkdir -p "$directory"
    fi
  done
  info "Directories created at $OPENCODE_DIR"
}

# Clone or update repo
clone_repo() {
  local clone_dir="$SCRIPT_DIR"
  if [[ ! -f "$SCRIPT_DIR/config/opencode.jsonc" || ! -d "$SCRIPT_DIR/skills" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      plan "clone $REPO_URL at tag $INSTALL_TAG"
      printf '%s\n' "__DRY_RUN_REMOTE__"
      return
    fi
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
  if [[ "$DRY_RUN" == true ]]; then
    CURRENT_MANAGED+=("$logical")
  else
    printf '%s\n' "$logical" >> "$CURRENT_MANIFEST"
  fi
}

current_manifest_contains() {
  local logical="$1" current
  if [[ "$DRY_RUN" == false ]]; then
    grep -Fqx "$logical" "$CURRENT_MANIFEST"
    return
  fi
  for current in "${CURRENT_MANAGED[@]}"; do
    [[ "$current" == "$logical" ]] && return 0
  done
  return 1
}

preserve_manifest_prefix() {
  local prefix="$1"
  [[ -f "$MANIFEST_FILE" ]] || return 0
  while IFS= read -r logical; do
    logical="${logical%$'\r'}"
    if [[ "$logical" == "$prefix"* ]]; then
      if [[ "$DRY_RUN" == true ]]; then
        CURRENT_MANAGED+=("$logical")
      else
        printf '%s\n' "$logical" >> "$CURRENT_MANIFEST"
      fi
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
  assert_no_symlink_components "$root" "$HOME"
  local backup path index
  while IFS= read -r backup; do backups+=("$backup"); done < <(
    for path in "$root"/*; do
      if [[ -d "$path" ]]; then basename "$path"; fi
    done | sort -r
  )
  for ((index=MAX_INSTALL_BACKUPS; index<${#backups[@]}; index++)); do
    case "${backups[$index]}" in
      */*|"") error "Unsafe backup entry name: ${backups[$index]}"; exit 1 ;;
    esac
    rm -rf "$root/${backups[$index]:?}"
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
    "$OPENCODE_DIR"/*|"$HOME/opencode-custom/skills"/*|"$OPENCODE_BIN_DIR"/*) assert_no_symlink_components "$path" "$HOME" ;;
    *) error "Managed path is outside allowed roots: $path"; exit 1 ;;
  esac
}

make_executable() {
  local path="$1"
  if [[ "$DRY_RUN" == true ]]; then
    plan "update mode executable: $path"
  else
    assert_managed_path_safe "$path"
    chmod +x "$path"
  fi
}

backup_sync_file() {
  local path="$1" logical backup
  [[ "$SYNC" == true && -f "$path" ]] || return 0
  assert_managed_path_safe "$path"
  logical="$(managed_path_for "$path")" || return 0
  if [[ "$DRY_RUN" == true ]]; then
    plan "backup: $logical"
    return 0
  fi
  if [[ -z "$SYNC_BACKUP_DIR" ]]; then
    assert_no_symlink_components "$HOME/.local/share/opencode/install-backups" "$HOME"
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
    if current_manifest_contains "$logical"; then
      continue
    fi
    destination="$(managed_destination_for "$logical")" || continue
    assert_managed_path_safe "$destination"
    if [[ -f "$destination" ]]; then
      backup_sync_file "$destination"
      if [[ "$DRY_RUN" == true ]]; then
        plan "remove: $logical"
      else
        rm -f "$destination"
        info "Removed stale managed file: $logical"
      fi
    fi
  done < "$MANIFEST_FILE"
}

finalize_manifest() {
  prune_stale_managed
  if [[ "$DRY_RUN" == true ]]; then
    plan "update manifest: $MANIFEST_FILE"
    return 0
  fi
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
  if [[ "$FORCE" == true || "$SYNC" == true || ! -f "$dst" ]]; then
    assert_managed_path_safe "$dst"
  fi
  if [[ -f "$dst" && "$FORCE" == false && "$SYNC" == false ]]; then
    if [[ "$DRY_RUN" == true ]]; then plan "preserve: $dst"; else info "Skipping (exists): $dst"; fi
    return 0
  fi
  if [[ "$SYNC" == true ]]; then
    backup_sync_file "$dst"
  fi
  if [[ "$DRY_RUN" == true ]]; then
    if [[ -e "$dst" || -L "$dst" ]]; then plan "update: $dst"; else plan "create: $dst"; fi
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  info "Installed: $dst"
}

# Copy all matching files into a dir, skipping existing unless FORCE
copy_dir_if_ok() {
  local src_glob="$1" dst_dir="$2" label="$3"
  if [[ "$FORCE" == true && -d "$dst_dir" ]]; then
    assert_managed_path_safe "$dst_dir"
    local existing_files=("$dst_dir"/*)
    if [[ -e "${existing_files[0]}" ]]; then
      local ts_backup
      ts_backup="$(date +%s)"
      if [[ "$DRY_RUN" == true ]]; then
        plan "backup: $label directory $dst_dir"
      else
        mkdir -p "$dst_dir.bak-$ts_backup"
        cp -r "$dst_dir/"* "$dst_dir.bak-$ts_backup/"
        info "$label backed up to $(basename "$dst_dir").bak-$ts_backup"
      fi
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
    if [[ "$DRY_RUN" == true ]]; then plan "preserve: $label tree $dst_dir"; else info "Skipping $label (exists): $dst_dir"; fi
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
    assert_managed_path_safe "$dst_dir"
    local backup
    backup="$dst_dir.bak-$(date +%s)"
    if [[ "$DRY_RUN" == true ]]; then
      plan "backup: $label tree $dst_dir"
    else
      cp -r "$dst_dir" "$backup"
      rm -rf "$dst_dir"
      info "$label backed up to $(basename "$backup")"
    fi
  fi
  if [[ "$DRY_RUN" == true ]]; then
    local source relative
    while IFS= read -r -d '' source; do
      relative="${source#"$src_dir"/}"
      copy_if_ok "$source" "$dst_dir/$relative"
    done < <(find "$src_dir" -type f -print0)
    return 0
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
    if [[ "$DRY_RUN" == true ]]; then plan "preserve: $OPENCODE_DIR/opencode.jsonc"; fi
    warn "opencode.jsonc already exists; preserving it (use --force to replace)"
  else
    if [[ -f "$OPENCODE_DIR/opencode.jsonc" && "$FORCE" == true ]]; then
      assert_managed_path_safe "$OPENCODE_DIR/opencode.jsonc"
      if [[ "$DRY_RUN" == true ]]; then plan "backup: opencode/opencode.jsonc"; else
        cp "$OPENCODE_DIR/opencode.jsonc" "$OPENCODE_DIR/opencode.jsonc.bak"
        info "Backed up opencode.jsonc to opencode.jsonc.bak"
      fi
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
  if [[ -d "$repo_dir/config/plugins.disabled" ]]; then
    copy_dir_if_ok "$repo_dir/config/plugins.disabled/*.js" "$OPENCODE_DIR/plugins.disabled" "Optional plugins (disabled)"
    info "Optional plugins stored disabled"
  fi

  if [[ -d "$repo_dir/config/lib" ]]; then
    copy_dir_if_ok "$repo_dir/config/lib/*.js" "$OPENCODE_DIR/lib" "Plugin libraries"
    info "Plugin libraries copied"
  fi

  # Commands
  if [[ -d "$repo_dir/config/commands" ]]; then
    copy_dir_if_ok "$repo_dir/config/commands/*.md" "$OPENCODE_DIR/commands" "Commands"
    info "Commands copied"
  fi

  # Plugin runtime dependencies (@opencode-ai/plugin resolution from config root)
  if [[ -f "$repo_dir/config/package.json" && -f "$repo_dir/config/package-lock.json" ]]; then
    local user_manifest=false
    if [[ -f "$OPENCODE_DIR/package.json" ]] && ! grep -q '"opencode-config-runtime"' "$OPENCODE_DIR/package.json" 2>/dev/null; then
      user_manifest=true
    fi
    if [[ "$user_manifest" == true ]]; then
      # Never npm ci over a user-owned manifest: it would delete their deps.
      if [[ "$DRY_RUN" == true ]]; then
        plan "install @opencode-ai/plugin with --no-save into user-owned manifest"
      else
        (cd "$OPENCODE_DIR" && npm install --no-save --ignore-scripts @opencode-ai/plugin@1.18.14) || {
          error "Failed to install plugin runtime dependency into user manifest"
          exit 1
        }
        info "Plugin runtime dependency installed alongside user manifest"
      fi
    else
      copy_if_ok "$repo_dir/config/package.json" "$OPENCODE_DIR/package.json"
      copy_if_ok "$repo_dir/config/package-lock.json" "$OPENCODE_DIR/package-lock.json"
      if [[ "$DRY_RUN" == true ]]; then
        plan "install-dependencies: $OPENCODE_DIR (plugin runtime)"
      else
        (cd "$OPENCODE_DIR" && npm ci --omit=dev --ignore-scripts) || {
          error "Failed to install plugin runtime dependencies in $OPENCODE_DIR"
          exit 1
        }
        info "Plugin runtime dependencies installed"
      fi
    fi
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
    if [[ -f "$OPENCODE_DIR/mcp/package.json" || "$DRY_RUN" == true ]]; then
      log "Installing MCP router dependencies..."
      if [[ "$DRY_RUN" == true ]]; then
        plan "install-dependencies: $OPENCODE_DIR/mcp"
      else
        (cd "$OPENCODE_DIR/mcp" && npm ci --omit=dev --ignore-scripts) || {
        error "Failed to install MCP router dependencies in $OPENCODE_DIR/mcp"
        error "Run 'npm ci --omit=dev --ignore-scripts' manually in $OPENCODE_DIR/mcp"
        exit 1
        }
        info "MCP router dependencies installed"
      fi
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
        if [[ -f "$profile" && "$DRY_RUN" == false ]]; then
          node -e 'const fs=require("node:fs"); const file=process.argv[1]; fs.writeFileSync(file, fs.readFileSync(file,"utf8").replaceAll("__OPENCODE_DIR__", process.argv[2]));' "$profile" "$OPENCODE_DIR"
        elif [[ "$DRY_RUN" == true && -f "$profile_dir/opencode.jsonc" ]]; then
          plan "update template: $profile"
        fi
      fi
    done
    info "Profiles copied"
  fi

  # Skills
  log "Installing skills..."
  if [[ -d "$repo_dir/skills" ]]; then
    assert_no_symlink_components "$HOME/opencode-custom/skills" "$HOME"
    if [[ "$DRY_RUN" == true ]]; then
      [[ -d "$HOME/opencode-custom/skills" ]] || plan "create directory: $HOME/opencode-custom/skills"
    else
      mkdir -p "$HOME/opencode-custom/skills"
    fi
    for skill_dir in "$repo_dir/skills"/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill_name="$(basename "$skill_dir")"
      copy_tree_if_ok "$skill_dir" "$HOME/opencode-custom/skills/$skill_name" "Skill $skill_name" || true
    done
    if [[ -f "$repo_dir/skills/sdd-phase-common.md" ]]; then
      copy_if_ok "$repo_dir/skills/sdd-phase-common.md" "$HOME/opencode-custom/skills/sdd-phase-common.md"
    fi
  fi

  # .env.example
  if [[ -f "$repo_dir/.env.example" ]]; then
    copy_if_ok "$repo_dir/.env.example" "$OPENCODE_DIR/.env.example"
    info ".env.example copied (configure your API keys manually)"
  fi

  # Shared config inspector
  if [[ -f "$repo_dir/tools/scripts/config-inspect.js" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/config-inspect.js" "$OPENCODE_DIR/tools/config-inspect.js"
  fi

  # Global doctor command
  if [[ -f "$repo_dir/tools/scripts/doctor.js" && -f "$repo_dir/tools/scripts/opencode-doctor.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/doctor.js" "$OPENCODE_DIR/tools/doctor.js"
    copy_if_ok "$repo_dir/tools/scripts/opencode-doctor.sh" "$OPENCODE_BIN_DIR/opencode-doctor"
    make_executable "$OPENCODE_BIN_DIR/opencode-doctor"
    info "opencode-doctor installed globally at $OPENCODE_BIN_DIR/opencode-doctor"
  fi
  if [[ -f "$repo_dir/tools/scripts/opencode-metrics.js" && -f "$repo_dir/tools/scripts/opencode-metrics.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/opencode-metrics.js" "$OPENCODE_DIR/tools/opencode-metrics.js"
    copy_if_ok "$repo_dir/tools/scripts/opencode-metrics.sh" "$OPENCODE_BIN_DIR/opencode-metrics"
    make_executable "$OPENCODE_BIN_DIR/opencode-metrics"
    info "opencode-metrics installed globally at $OPENCODE_BIN_DIR/opencode-metrics"
  fi
  if [[ -f "$repo_dir/tools/scripts/profile.js" && -f "$repo_dir/tools/scripts/opencode-profile.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/profile.js" "$OPENCODE_DIR/tools/profile.js"
    local profile_command source
    for profile_command in opencode-profile opencode-work opencode-personal opencode-light; do
      source="$repo_dir/tools/scripts/$profile_command.sh"
      [[ -f "$source" ]] || continue
      copy_if_ok "$source" "$OPENCODE_BIN_DIR/$profile_command"
      make_executable "$OPENCODE_BIN_DIR/$profile_command"
    done
    info "OpenCode profile launchers installed globally"
  fi
  if [[ -f "$repo_dir/tools/scripts/skills.js" && -f "$repo_dir/tools/scripts/opencode-skills.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/skills.js" "$OPENCODE_DIR/tools/skills.js"
    copy_if_ok "$repo_dir/tools/scripts/opencode-skills.sh" "$OPENCODE_BIN_DIR/opencode-skills"
    make_executable "$OPENCODE_BIN_DIR/opencode-skills"
    info "opencode-skills installed globally at $OPENCODE_BIN_DIR/opencode-skills"
  fi
  if [[ -f "$repo_dir/tools/scripts/opencode-ecosystem.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/opencode-ecosystem.sh" "$OPENCODE_BIN_DIR/opencode-ecosystem"
    make_executable "$OPENCODE_BIN_DIR/opencode-ecosystem"
    info "opencode-ecosystem installed globally at $OPENCODE_BIN_DIR/opencode-ecosystem"
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
  if [[ ( -f "$mem_dir/src/cli.js" || "$DRY_RUN" == true ) && -f "$repo_dir/tools/scripts/memory-adapter.sh" ]]; then
    copy_if_ok "$repo_dir/tools/scripts/memory-adapter.sh" "$OPENCODE_BIN_DIR/memory-adapter"
    make_executable "$OPENCODE_BIN_DIR/memory-adapter"
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
  check "$OPENCODE_DIR/plugins/organic-rdd.js"
  check "$OPENCODE_DIR/lib/organic-rdd.js"
  check "$OPENCODE_DIR/commands/review-start.md"
  check "$OPENCODE_DIR/commands/review-gate.md"
  check "$OPENCODE_DIR/tools/doctor.js"
  check "$OPENCODE_BIN_DIR/opencode-doctor"
  check "$OPENCODE_DIR/lib/session-metrics.js"
  check "$OPENCODE_BIN_DIR/opencode-metrics"
  check "$OPENCODE_DIR/tools/profile.js"
  check "$OPENCODE_BIN_DIR/opencode-profile"
  check "$OPENCODE_BIN_DIR/opencode-light"
  check "$OPENCODE_DIR/tools/skills.js"
  check "$OPENCODE_BIN_DIR/opencode-skills"
  check "$OPENCODE_BIN_DIR/opencode-ecosystem"
  [[ -d "$OPENCODE_DIR/agents" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing agents dir"
  [[ -d "$OPENCODE_DIR/plugins" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing plugins dir"
  [[ -d "$OPENCODE_DIR/mcp" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing mcp dir"
  [[ -d "$HOME/opencode-custom/skills" ]] && { checks=$((checks+1)); passed=$((passed+1)); } || warn "Missing skills dir"

  if [[ "$SKIP_MEMORY" != true ]]; then
    check "$OPENCODE_DIR/mcp/memory-adapter/package.json"
    check "$OPENCODE_BIN_DIR/memory-adapter"
  fi

  # Verify Organic RDD plugin actually loads with its runtime dependency
  if [[ -d "$OPENCODE_DIR/node_modules/@opencode-ai/plugin" ]]; then
    checks=$((checks+1))
    if node --input-type=module -e "import(process.argv[1]).then(async m => { if (!m.default || typeof m.default !== 'function') process.exit(1); const p = await m.default(); process.exit(p.tool && p.tool.review_gate ? 0 : 1); }).catch(() => process.exit(1))" "$OPENCODE_DIR/plugins/organic-rdd.js" 2>/dev/null; then
      passed=$((passed+1))
      info "Organic RDD plugin import OK"
    else
      warn "Organic RDD plugin import failed"
    fi
  else
    checks=$((checks+1))
    warn "Missing plugin runtime dependency @opencode-ai/plugin"
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
  if [[ "$DRY_RUN" == false ]]; then
    CURRENT_MANIFEST="$(mktemp)"
    trap 'rm -f "$CURRENT_MANIFEST"' EXIT
  fi

  REPO_DIR="$(clone_repo)"
  if [[ "$REPO_DIR" == "__DRY_RUN_REMOTE__" ]]; then
    plan "defer-verification: detailed plan requires distribution contents"
    echo ""
    log "Dry run complete; no changes made."
    return 0
  fi
  info "Using repo dir: $REPO_DIR"

  copy_config "$REPO_DIR"
  install_memory "$REPO_DIR"
  if [[ "$DRY_RUN" == true ]]; then plan "defer-verification: runtime installation checks"; else verify_install; fi
  finalize_manifest

  echo ""
  if [[ "$DRY_RUN" == true ]]; then log "Dry run complete; no changes made."; else log "Done. Happy coding!"; fi
}

main
