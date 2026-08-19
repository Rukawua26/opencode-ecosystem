#!/usr/bin/env bash
# Menu y reporte de perfiles OpenCode.
# Instalado por install.sh en ~/.opencode/bin/opencode-profile
set -euo pipefail

PROFILE_JS="$HOME/.config/opencode/tools/profile.js"
if [[ ! -f "$PROFILE_JS" ]]; then
  echo "[error] profile.js no esta instalado en $PROFILE_JS" >&2
  exit 1
fi

if [[ $# -gt 0 && ( "$1" == "--status" || "$1" == "--json" || "$1" == "--help" || "$1" == "-h" ) ]]; then
  exec node "$PROFILE_JS" "$@"
fi

profile=""
if [[ $# -gt 0 ]]; then
  case "$1" in
    work|personal|light|default) profile="$1"; shift ;;
    *) echo "Opcion invalida: $1" >&2; exit 2 ;;
  esac
else
  echo "Perfiles disponibles:"
  echo "  1) work     - Modelo completo + todos los plugins"
  echo "  2) personal - Modelo ligero + plugins esenciales"
  echo "  3) light    - Modelo economico + contexto minimo"
  echo "  4) default  - Config por defecto (sin OPENCODE_CONFIG)"
  echo ""
  read -rp "Selecciona perfil [1-4]: " choice
  case "$choice" in
    1) profile=work ;;
    2) profile=personal ;;
    3) profile=light ;;
    4) profile=default ;;
    *) echo "Opcion invalida" >&2; exit 1 ;;
  esac
fi

node "$PROFILE_JS" --validate "$profile"
case "$profile" in
  work) export OPENCODE_CONFIG="$HOME/.config/opencode/profiles/work/opencode.jsonc" OPENCODE_EFFORT_MODE=max ;;
  personal) export OPENCODE_CONFIG="$HOME/.config/opencode/profiles/personal/opencode.jsonc" OPENCODE_EFFORT_MODE=medium ;;
  light) export OPENCODE_CONFIG="$HOME/.config/opencode/profiles/light/opencode.jsonc" OPENCODE_EFFORT_MODE=low ;;
  default) unset OPENCODE_CONFIG OPENCODE_EFFORT_MODE ;;
esac
command -v opencode >/dev/null 2>&1 || { echo "[error] opencode no esta en PATH" >&2; exit 1; }
exec opencode "$@"
