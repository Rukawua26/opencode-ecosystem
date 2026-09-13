#!/usr/bin/env bash
# hygiene.sh {triggers|prune [--apply]|reset [--confirm]} — higiene manual, preview por defecto.
# Nada se borra sin --apply/--confirm. Gatillos: .bak>5, observations.log>200 líneas, topics>10.
set -u
CFG="$HOME/.config/opencode"
MEM="$CFG/memory"
KEEP_BAK=5
MAX_LOG_LINES=200
MAX_TOPICS=10
KEEP_LOG_LINES=50

cmd_triggers() {
  local baks log_lines topics fire=0 prunables
  baks=$(ls "$CFG"/*.bak-* 2>/dev/null | wc -l)
  prunables=$(prune_candidates | wc -l)
  log_lines=$(wc -l < "$MEM/observations.log" 2>/dev/null || echo 0)
  topics=$(ls "$MEM/topics" 2>/dev/null | wc -l)
  echo "baks: $baks (podables $prunables, keep $KEEP_BAK/basename)"
  echo "observations.log líneas: $log_lines (umbral $MAX_LOG_LINES)"
  echo "topics ficheros: $topics (umbral $MAX_TOPICS)"
  [ "$prunables" -gt "0" ] && { echo "-> dispara: prune ($prunables)"; fire=1; }
  { [ "$log_lines" -gt "$MAX_LOG_LINES" ] || [ "$topics" -gt "$MAX_TOPICS" ]; } && { echo "-> dispara: reset"; fire=1; }
  [ "$fire" = "0" ] && echo "-> no dispara"
}

prune_candidates() { # imprime rutas podables (dedup sha256 + keep-5 por basename, nuevos primero)
  local base f
  for base in $(ls "$CFG"/*.bak-* 2>/dev/null | sed 's/\.bak-[0-9-]*$//' | sort -u); do
    local kept=0
    declare -A seen=()
    while IFS= read -r f; do
      [ -z "$f" ] && continue
      local h
      h=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)
      if [ "$kept" -lt "$KEEP_BAK" ] && [ -z "${seen[$h]:-}" ]; then
        seen[$h]=1; kept=$((kept + 1))
      else
        echo "$f"
      fi
    done < <(ls -t "$base".bak-* 2>/dev/null)
  done
}

cmd_prune() { # prune [--apply]
  local apply="${1:-preview}" deleted=0 f
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if [ "$apply" = "--apply" ]; then rm -f "$f"; echo "[rm] $f"; else echo "[pdte] $f"; fi
    deleted=$((deleted + 1))
  done < <(prune_candidates)
  echo "candidatos: $deleted (modo: $apply)"
}

cmd_reset() { # reset [--confirm]: preview o trunca log a 50 + vacía topics/ (preserva MEMORY.md y *.sh)
  local apply="${1:-preview}"
  echo "--- topics/ ---"
  ls "$MEM/topics" 2>/dev/null || echo "(vacío)"
  echo "--- observations.log: $(wc -l < "$MEM/observations.log" 2>/dev/null || echo 0) líneas ---"
  if [ "$apply" = "--confirm" ]; then
    tail -n "$KEEP_LOG_LINES" "$MEM/observations.log" > "$MEM/observations.log.tmp" 2>/dev/null \
      && mv "$MEM/observations.log.tmp" "$MEM/observations.log" || true
    rm -f "$MEM"/topics/* 2>/dev/null || true
    echo "[ok] reset aplicado (MEMORY.md y *.sh intactos)"
  else
    echo "(preview: sin cambios)"
  fi
}

case "${1:-triggers}" in
  triggers) cmd_triggers ;;
  prune) cmd_prune "${2:-preview}" ;;
  reset) cmd_reset "${2:-preview}" ;;
  *) echo "uso: $0 {triggers|prune [--apply]|reset [--confirm]}"; exit 2 ;;
esac
