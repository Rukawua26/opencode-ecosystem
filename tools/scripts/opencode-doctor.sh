#!/usr/bin/env bash
# Wrapper global para el comando opencode-doctor
# Instalado por install.sh en ~/.opencode/bin/

DOCTOR_JS="$HOME/.config/opencode/tools/doctor.js"
if [[ ! -f "$DOCTOR_JS" ]]; then
  echo "[error] doctor.js no esta instalado en $DOCTOR_JS" >&2
  exit 1
fi
exec node "$DOCTOR_JS" "$@"
