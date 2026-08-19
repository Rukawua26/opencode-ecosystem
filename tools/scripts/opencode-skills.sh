#!/usr/bin/env bash
# Registry index-first de skills OpenCode.
# Instalado por install.sh en ~/.opencode/bin/opencode-skills
set -euo pipefail

SKILLS_JS="$HOME/.config/opencode/tools/skills.js"
if [[ ! -f "$SKILLS_JS" ]]; then
  echo "[error] skills.js no esta instalado en $SKILLS_JS" >&2
  exit 1
fi
export NODE_DISABLE_COMPILE_CACHE=1
exec node "$SKILLS_JS" "$@"
