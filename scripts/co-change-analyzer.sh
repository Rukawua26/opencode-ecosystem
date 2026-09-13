#!/usr/bin/env bash
# co-change-analyzer.sh — mínimo: advierte si el fichero a modificar suele cambiar con otros (top co-changes del git log).
# Uso: co-change-analyzer.sh <archivo>
set -u
F="${1:-}"
[ -z "$F" ] && { echo "uso: $0 <archivo>"; exit 0; }
git log --name-only --pretty=format: 2>/dev/null | grep -vE "^\s*$" | sort | uniq -c | sort -rn | head -5 || true
