#!/usr/bin/env bash
# co-change-analyzer.sh — mínimo: advierte si el fichero a modificar suele cambiar
# con otros (top co-cambios del git log).
# Uso: co-change-analyzer.sh <archivo>
set -u
F="${1:-}"
[ -z "$F" ] && { echo "uso: $0 <archivo>"; exit 0; }
# Co-cambios reales: ficheros presentes en los mismos commits que $F (no los más
# versionados en global). Acotado a los últimos 100 commits que tocaron $F para
# mantener el coste bajo en la máquina modesta (3 procesos git, no uno por commit).
N=100
git rev-list -n "$N" HEAD -- "$F" 2>/dev/null \
  | xargs -r git show --format= --name-only 2>/dev/null \
  | grep -vE '^[[:space:]]*$' \
  | grep -vxF "$F" \
  | sort | uniq -c | sort -rn | head -5 || true
