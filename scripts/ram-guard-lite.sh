#!/usr/bin/env bash
# ram-guard-lite.sh — cron 5min: si MEM disponible <15%, mata ollama huérfano. Solo Linux (free -b).
# Log propio (no observations.log) para no enterrar la señal de kairos.
set -u
FREE_PCT=$(free | awk '/Mem:/ {printf "%d", $7/$2*100}')
if [ "${FREE_PCT:-100}" -lt 15 ]; then
  pkill -f "ollama run" 2>/dev/null || true
  echo "$(date -Is) ram-guard: libre ${FREE_PCT}% -> ollama huérfanos terminados" >> "$HOME/.config/opencode/memory/ram-guard.log"
fi
