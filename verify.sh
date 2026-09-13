#!/usr/bin/env bash
# verify.sh — validación única post-cambio. Exit ≠0 si algo falla. No se sincroniza a ~/.config.
set -u
ECO="$HOME/opencode-ecosystem"
FAIL=0
"$ECO/scripts/hygiene.sh" triggers || true # informativo: un gatillo no es fallo
python3 "$ECO/validate-skills.py" "$ECO/skills" || FAIL=1
python3 "$ECO/validate-skills.py" "$HOME/.config/opencode/skills" || FAIL=1
opencode debug config >/dev/null 2>&1 || { echo "[fail] debug config"; FAIL=1; }
"$ECO/opencode-ecosystem" status || FAIL=1
bash "$HOME/tools/plugin_doctor.sh" >/dev/null 2>&1 || { echo "[fail] plugin_doctor"; FAIL=1; }
python3 "$HOME/tools/agent_context/query_context.py" doctor >/dev/null 2>&1 || { echo "[fail] context doctor"; FAIL=1; }
if [ "$FAIL" = "0" ]; then echo "[ok] verify verde"; else echo "[fail] verify rojo"; fi
exit "$FAIL"
