#!/usr/bin/env bash
# autodream.sh (consolidador) — lite: mueve líneas de observations.log a topics/ si el archivo citado existe.
# Uso: solo en idle. No usa red ni modelos.
set -u
MEM="$HOME/.config/opencode/memory"
LOG="$MEM/observations.log"
TOP="$MEM/topics"
mkdir -p "$TOP"
[ -f "$LOG" ] || exit 0
# Consolidación mínima: agrupa por fecha en topics/inbox-YYYY-MM-DD.md (evita miles de ficheros)
DAY=$(date +%F)
DEST="$TOP/inbox-$DAY.md"
grep -vE "^\s*$" "$LOG" | head -200 >> "$DEST" 2>/dev/null || true
# Trunca log para no crecer sin fin (conserva últimas 50 líneas como ventana)
tail -50 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG" || true
echo "consolidado en $DEST"
