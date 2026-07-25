#!/usr/bin/env bash

METRICS_JS="$HOME/.config/opencode/tools/opencode-metrics.js"
if [[ ! -f "$METRICS_JS" ]]; then
  echo "[error] opencode-metrics.js no esta instalado en $METRICS_JS" >&2
  exit 1
fi
exec node "$METRICS_JS" "$@"
