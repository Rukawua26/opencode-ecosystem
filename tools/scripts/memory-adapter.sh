#!/usr/bin/env bash

CLI="$HOME/.config/opencode/mcp/memory-adapter/src/cli.js"
if [[ ! -f "$CLI" ]]; then
  echo "[error] memory-adapter no esta instalado en $CLI" >&2
  exit 1
fi
exec node "$CLI" "$@"
