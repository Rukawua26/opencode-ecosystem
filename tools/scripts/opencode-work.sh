#!/usr/bin/env bash
# Ejecuta OpenCode con el perfil work.
# Instalado por install.sh en ~/.opencode/bin/opencode-work
set -euo pipefail
exec "$HOME/.opencode/bin/opencode-profile" work "$@"
