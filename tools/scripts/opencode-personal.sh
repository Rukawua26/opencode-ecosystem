#!/usr/bin/env bash
# Ejecuta OpenCode con el perfil personal.
# Instalado por install.sh en ~/.opencode/bin/opencode-personal
set -euo pipefail
exec "$HOME/.opencode/bin/opencode-profile" personal "$@"
