#!/usr/bin/env bash
# Wrapper global para el comando opencode-doctor
# Instalado por install.sh en ~/.opencode/bin/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec node "$SCRIPT_DIR/doctor.js" "$@"
