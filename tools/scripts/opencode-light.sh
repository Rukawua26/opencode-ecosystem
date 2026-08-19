#!/usr/bin/env bash
# Ejecuta OpenCode con el perfil light.
# Instalado por install.sh en ~/.opencode/bin/opencode-light
set -euo pipefail
exec "$HOME/.opencode/bin/opencode-profile" light "$@"
