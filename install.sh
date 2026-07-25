#!/usr/bin/env bash
set -euo pipefail

# ===========================================
# OpenCode Ecosystem Installer
# https://github.com/Rukawua26/opencode-ecosystem
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/Rukawua26/opencode-ecosystem.git"
OPENCODE_DIR="$HOME/.config/opencode"
OPENCODE_BIN_DIR="$HOME/.opencode/bin"
VERBOSE=false
FORCE=false
SKIP_MEMORY=false

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
    --skip-memory) SKIP_MEMORY=true; shift ;;
    --help|-h)
      echo "Usage: install.sh [--verbose] [--force] [--skip-memory]"
      echo ""
      echo "Options:"
      echo "  --verbose, -v    Show detailed output"
      echo "  --force, -f      Overwrite existing config"
      echo "  --skip-memory    Skip memory adapter installation"
      echo "  --help, -h       Show this help"
      exit 0
      ;;
    *) error "Unknown option: $1"; exit 1 ;;
  esac
done

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
    log "Cloning repo to $clone_dir..."
    git clone --depth 1 "$REPO_URL" "$clone_dir"
    info "Repo cloned"
  else
    info "Using local distribution files"
  fi
  printf '%s\n' "$clone_dir"
}

# Copy config
copy_config() {
  local repo_dir="$1"
  log "Installing config..."

  # opencode.jsonc
  if [[ -f "$OPENCODE_DIR/opencode.jsonc" && "$FORCE" == false ]]; then
    warn "opencode.jsonc already exists; preserving it (use --force to replace)"
    cp "$OPENCODE_DIR/opencode.jsonc" "$OPENCODE_DIR/opencode.jsonc.bak"
  else
    cp "$repo_dir/config/opencode.jsonc" "$OPENCODE_DIR/opencode.jsonc"
    info "opencode.jsonc installed"
  fi

  # Agents
  log "Installing agents..."
  if [[ -d "$repo_dir/config/agents" ]]; then
    cp -r "$repo_dir/config/agents/"*.md "$OPENCODE_DIR/agents/"
    info "Agents copied"
  fi

  # Plugins
  log "Installing plugins..."
  if [[ -d "$repo_dir/config/plugins" ]]; then
    cp -r "$repo_dir/config/plugins/"*.js "$OPENCODE_DIR/plugins/" 2>/dev/null || true
    info "Plugins copied"
  fi

  if [[ -d "$repo_dir/config/lib" ]]; then
    cp -r "$repo_dir/config/lib/"*.js "$OPENCODE_DIR/lib/" 2>/dev/null || true
    info "Plugin libraries copied"
  fi

  # MCP servers
  log "Installing MCP servers..."
  if [[ -d "$repo_dir/config/mcp" ]]; then
    cp -r "$repo_dir/config/mcp/"*.js "$OPENCODE_DIR/mcp/" 2>/dev/null || true
    info "MCP servers copied"
  fi

  # Profiles
  log "Installing profiles..."
  if [[ -d "$repo_dir/config/profiles" ]]; then
    cp -r "$repo_dir/config/profiles/"* "$OPENCODE_DIR/profiles/" 2>/dev/null || true
    for profile in "$OPENCODE_DIR"/profiles/*/opencode.jsonc; do
      [[ -f "$profile" ]] || continue
      node -e 'const fs=require("node:fs"); const file=process.argv[1]; fs.writeFileSync(file, fs.readFileSync(file,"utf8").replaceAll("__OPENCODE_DIR__", process.argv[2]));' "$profile" "$OPENCODE_DIR"
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
      mkdir -p "$HOME/opencode-custom/skills/$skill_name"
      cp -r "$skill_dir"/* "$HOME/opencode-custom/skills/$skill_name/" 2>/dev/null || true
      info "Skill installed: $skill_name"
    done
  fi

  # .env.example
  if [[ -f "$repo_dir/.env.example" ]]; then
    cp "$repo_dir/.env.example" "$OPENCODE_DIR/.env.example"
    info ".env.example copied (configure your API keys manually)"
  fi

  # Global doctor command
  if [[ -f "$repo_dir/tools/scripts/doctor.js" && -f "$repo_dir/tools/scripts/opencode-doctor.sh" ]]; then
    cp "$repo_dir/tools/scripts/doctor.js" "$OPENCODE_DIR/tools/doctor.js"
    cp "$repo_dir/tools/scripts/opencode-doctor.sh" "$OPENCODE_BIN_DIR/opencode-doctor"
    chmod +x "$OPENCODE_BIN_DIR/opencode-doctor"
    info "opencode-doctor installed globally at $OPENCODE_BIN_DIR/opencode-doctor"
  fi
  if [[ -f "$repo_dir/tools/scripts/opencode-metrics.js" && -f "$repo_dir/tools/scripts/opencode-metrics.sh" ]]; then
    cp "$repo_dir/tools/scripts/opencode-metrics.js" "$OPENCODE_DIR/tools/opencode-metrics.js"
    cp "$repo_dir/tools/scripts/opencode-metrics.sh" "$OPENCODE_BIN_DIR/opencode-metrics"
    chmod +x "$OPENCODE_BIN_DIR/opencode-metrics"
    info "opencode-metrics installed globally at $OPENCODE_BIN_DIR/opencode-metrics"
  fi
}

# Install memory adapter
install_memory() {
  if [[ "$SKIP_MEMORY" == true ]]; then
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
  mkdir -p "$mem_dir"
  cp -r "$repo_dir/packages/memory-adapter/"* "$mem_dir/"

  # Install deps
  if [[ -f "$mem_dir/package.json" ]]; then
    log "Installing memory adapter dependencies..."
    (cd "$mem_dir" && npm install --production 2>/dev/null) || warn "Failed to install memory adapter deps, run 'npm install' manually in $mem_dir"
    info "Memory adapter installed at $mem_dir"
  fi

  # Link global CLI through a wrapper so relative imports stay inside the package.
  if [[ -f "$mem_dir/src/cli.js" && -f "$repo_dir/tools/scripts/memory-adapter.sh" ]]; then
    cp "$repo_dir/tools/scripts/memory-adapter.sh" "$OPENCODE_BIN_DIR/memory-adapter"
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

  local agent_count plugin_count skill_count
  agent_count=$(find "$OPENCODE_DIR/agents" -name "*.md" 2>/dev/null | wc -l || echo 0)
  plugin_count=$(find "$OPENCODE_DIR/plugins" -name "*.js" 2>/dev/null | wc -l || echo 0)
  skill_count=$(find "$HOME/opencode-custom/skills" -maxdepth 1 -type d 2>/dev/null | wc -l || echo 0)
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

  REPO_DIR="$(clone_repo)"
  info "Using repo dir: $REPO_DIR"

  copy_config "$REPO_DIR"
  install_memory "$REPO_DIR"
  verify_install

  echo ""
  log "Done. Happy coding!"
}

main
