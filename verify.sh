#!/usr/bin/env bash
set +evx
# Cierre local secuencial. No se sincroniza a ~/.config.
set -u
# Mismo alcance canonico que QA: no aceptar repo/indice/config GIT_* heredados.
for git_name in "${!GIT_@}"; do
  unset "$git_name"
done
unset git_name
if [ "$#" -ne 0 ]; then
  echo '[fail] verify: argumentos invalidos'
  exit 2
fi
if [ -z "${HOME:-}" ]; then
  echo '[unavailable] verify: HOME no disponible; alcance: ECO'
  echo '[fail] verify rojo'
  exit 2
fi
ECO="$HOME/opencode-ecosystem"
FAIL=0
STAGED='desconocido (consulta incompleta)'
if ! cd -- "$ECO" 2>/dev/null; then
  echo '[unavailable] verify: repositorio no disponible; alcance: ECO'
  echo '[fail] verify rojo'
  exit 2
fi
echo '[info] Salidas stdout/stderr descartadas; no se vuelcan ni guardan detalles para evitar secretos.'
echo '[info] Tests: working tree. QA: staged + rutas rastreadas de ECO; no certifica codigo unstaged.'

run_check() {
  local name="$1" scope="$2" seconds="$3" mode="$4" rc result='ok' detail='rc=0'
  shift 4
  if ! command -v timeout >/dev/null 2>&1 || ! command -v "$1" >/dev/null 2>&1; then
    rc=127
  elif { [ "$1" = python3 ] || [ "$1" = bash ]; } && [ "${2:-}" != '-c' ] && [ "${2:-}" != '-m' ] && [ ! -r "${2:-}" ]; then
    rc=127
  else
    # KILL cubre el grupo normal de timeout, no procesos detached deliberados.
    # La redireccion del bloque tambien descarta diagnosticos de la shell.
    { timeout --signal=KILL "${seconds}s" "$@"; rc=$?; } >/dev/null 2>&1
  fi
  case "$mode:$rc" in
    staged:0) STAGED='no aplicable (sin cambios staged)'; detail="$STAGED" ;;
    staged:1) STAGED='aplicable'; detail="$STAGED" ;;
    hygiene:1) result='warn'; detail='trigger informativo; rc=1' ;;
    *:0) ;;
    *:126|*:127) result='unavailable'; detail='comando o recurso no disponible' ;;
    *:124|*:137) result='incomplete'; detail='limite de tiempo o terminacion; sin cierre completo' ;;
    gate:2|discovery:2) result='incomplete'; detail='error operativo o alcance incompleto; rc=2' ;;
    *) result='fail'; detail="error; rc=$rc" ;;
  esac
  printf '[%s] %s: %s; alcance: %s\n' "$result" "$name" "$detail" "$scope"
  case "$result" in ok|warn) ;; *) FAIL=1 ;; esac
}

run_check 'hygiene triggers' 'runtime; solo informativo' 30 hygiene "$ECO/scripts/hygiene.sh" triggers
run_check 'skills fuente' 'working tree ECO/skills' 30 required python3 "$ECO/validate-skills.py" "$ECO/skills"
run_check 'skills runtime' 'HOME/.config/opencode/skills' 30 required python3 "$ECO/validate-skills.py" "$HOME/.config/opencode/skills"
run_check 'debug config' 'config runtime OpenCode' 60 required opencode debug config
run_check 'status drift' 'fuente ECO frente a runtime' 60 required "$ECO/opencode-ecosystem" status
run_check 'plugin doctor' 'herramienta HOME/tools; runtime' 60 required bash "$HOME/tools/plugin_doctor.sh"
run_check 'context doctor' 'contexto HOME/tools/agent_context' 60 required python3 "$HOME/tools/agent_context/query_context.py" doctor
# Exigir una suite no vacia sin depender del exit de unittest ni analizar texto.
run_check 'tests discovery' 'working tree control/tests; exige tests descubiertos' 60 discovery python3 -c 'import sys, unittest; sys.exit(0 if unittest.defaultTestLoader.discover("control/tests").countTestCases() else 2)'
run_check 'unittest' 'working tree control/tests' 180 required python3 -m unittest discover -s control/tests
run_check 'QA consulta staged' 'indice Git raiz ECO; solo aplicabilidad' 15 staged git diff --cached --quiet --no-ext-diff --no-textconv --no-relative --ignore-submodules=none --no-renames -- :/
# Siempre ejecutar: incluso sin staged quedan las rutas sensibles rastreadas.
run_check 'QA strict' "ECO: staged $STAGED + rutas rastreadas; no certifica unstaged" 60 gate "$ECO/scripts/qa-gate.sh" --strict
if [ "$FAIL" = 0 ]; then
  echo '[ok] verify verde'
else
  echo '[fail] verify rojo'
fi
exit "$FAIL"
