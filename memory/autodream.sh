#!/usr/bin/env bash
# autodream.sh (consolidador) — lite: destila observations.log a 3 ficheros fijos con dedup.
# Uso: solo en idle. No usa red ni modelos. Si no hay señal, no escribe.
set -u
MEM="$HOME/.config/opencode/memory"
LOG="$MEM/observations.log"
TOP="$MEM/topics"
mkdir -p "$TOP"
[ -f "$LOG" ] || exit 0
DEC="$TOP/decisiones.md"
LEC="$TOP/lecciones.md"
PRE="$TOP/preferencias.md"
for F in "$DEC" "$LEC" "$PRE"; do [ -f "$F" ] || echo "# $(basename "$F" .md)" > "$F"; done
while IFS= read -r LINE; do
  case "$LINE" in
    ""|"### kairos"*) continue ;;
  esac
  DEST=""
  case "$LINE" in
    *[Dd]ecisi*|*[Aa]cuerdo*|*[Ss]e\ decide*) DEST="$DEC" ;;
    *[Ll]ecci*|*[Aa]prendid*|*[Ee]rror*|*ERROR*|*[Ff]ix*|*FIX*|*[Ff]allo*) DEST="$LEC" ;;
    *[Pp]refer*|*[Pp]refiero*|*siempre*|*nunca*) DEST="$PRE" ;;
    *) continue ;;
  esac
  grep -Fqx -- "$LINE" "$DEST" 2>/dev/null || echo "$LINE" >> "$DEST"
done < "$LOG"
# Trunca log para no crecer sin fin (conserva últimas 50 líneas como ventana)
tail -50 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG" || true
echo "destilado en decisiones/lecciones/preferencias"
