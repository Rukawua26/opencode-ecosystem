# Panel: verdad declarado y alcance de salud

## Objetivo
Que el plano de control deje de afirmar mas de lo que observa: corregir el flujo
declarado que inventa un hook `pre-commit` inexistente, hacer visible el cierre
`verify.sh`, y acotar la etiqueta de salud a lo que realmente comprueba.

## Problema y por que
- `control/collect.py:329-335` declara el flujo `qa-gate` con la description
  `restore -> qa-gate -> pre-commit; hooks ram-guard y kairos activos`. No existe
  hook pre-commit (`git config core.hooksPath` vacio, `.git/hooks/pre-commit`
  ausente) y `verify.sh` no aparece en ningun flujo pese a ser el cierre real.
- El panel presenta `health.ok` con la etiqueta `sano`. `Health.ok` solo comprueba
  servicio OpenCode activo, timers activos y `errors == []` (`collect.py:377-384`).
  No ejecuta ni observa `verify.sh`, tests ni qa-gate: hoy puede mostrar `sano`
  con `verify.sh` rojo. Afirmacion que excede la evidencia observada.
- `verify.sh` es el unico componente del ciclo de cierre que el panel no observa.
- `control/README.md:9` replica la lista de flujos y no aclara el alcance de salud.

## Alcance
Incluye: flujo `qa-gate` declarado, nuevo flujo `cierre` declarado, componente
observado `verify.sh`, acotado de la etiqueta de salud del panel, README del
control y sus tests.
Excluye: ejecutar la suite desde el panel, migrar SQLite, dependencias nuevas,
daemons, observar sesion interactiva/tokens/skills usadas, podar backups,
reescribir documentos historicos de `odd/tasks/` o `docs/evolution/`, y
automatizar la aceptacion de versions de OpenCode.

## Restricciones
Python stdlib y HTML/JS sin CDN. Sin cambios en esquema, memoria viva, receipts,
backups ni logs. Sin commit, branch, push ni PR sin peticion explicita. No tocar
los tests del E2E Playwright ni el servidor mas de lo necesario. La fuente es
este repo; `verify.sh` es local y no se sincroniza al runtime.

## No romper
- `health.ok` sigue significando exactamente lo de hoy: servicio + timers + errors.
  No se redefine su semantica ni se le anade el estado de `verify.sh`.
- El nombre del flujo `qa-gate` se conserva: cambiar el id rompe consumidores.
- `counts` y la forma del `Snapshot` no cambian.
- El cierre `verify.sh` no se ejecuta desde el panel ni se guarda su exit code.
- Todos los tests existentes siguen pasando, incluido `test_frontend.py` con
  `node --check` sobre el script inline.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks funcionales obligatorios. Se escribe primero la regresion que falla
  (flujo que promete `pre-commit`, etiqueta de salud sin acotar, `verify.sh` no
  observado) antes de corregir, sin afirmar que hay Strict TDD configurado.

## Tareas
- [x] T1: corregir flujo `qa-gate` y anadir flujo declarado `cierre`; observar
  `verify.sh` como componente; actualizar `control/README.md`; tests que fijen
  que el flujo no promete `pre-commit`, que `cierre` nombra `./verify.sh` y que
  `verify.sh` aparece como componente observado.

## Criterios de aceptacion
- [x] Ningun flujo declarado afirma un hook `pre-commit`.
- [x] Existe un flujo declarado de cierre que nombra `./verify.sh` y sus checks.
- [x] `verify.sh` es componente observado con `kind=script`.
- [x] La etiqueta de salud del panel dice que mide servicio y timers, no el cierre.
- [x] `health.ok` mantiene su semantica; no se guarda exit code de `verify.sh`.
- [x] `control/README.md` coincide con los flujos reales y aclara el alcance de salud.
- [x] Regresiones que fallan antes del fix y pasan despues.
- [x] Suite completa verde, validate-skills verde, status sin drift, verify verde
      y `qa-gate.sh --strict` exit 0.

## Decisiones aceptadas
- Se conserva el id `qa-gate` y se anade `cierre`; no se renombra nada.
- La salud se acota en la etiqueta visible, no en la semantica de `Health`.
- No se anade categoria de pin desfasado a `verify.sh`: los dos jueces
  independientes lo marcaron como YAGNI y riesgo de falso verde cuando exista el
  primer plugin. Se resuelve re-pineando tras revision explicita.
- `docs/` y `odd/tasks/` no se convierten en componentes: 19 documentos ODD y las
  notas de evolucion inflarian los conteos y generarian ruido en cada ODD nuevo.

## Reutilizacion investigada
- Canonicos: `control/collect.py` (`_build_flows`, `_collect_scripts`),
  `control/web/index.html` (`health-pill`), `control/README.md`, y el fixture
  `control/tests/test_control.py` que ya construye un snapshot en temporal.
- `_collect_scripts` ya resuelve scripts por glob; `verify.sh` esta en la raiz,
  no en `scripts/`, asi que se anade una funcion pequena que reutiliza `Component`
  y `ComponentKind.SCRIPT` en vez de un kind nuevo.
- No existe sanitizador de salidas que reutilizar: aqui no hay salida que volcar.
- No se crea categoria nueva en `verify.sh`; se reutiliza `run_check` tal cual.

## Evidencia
- Baseline: `./verify.sh` ROJO solo por `plugin doctor` rc=1: OpenCode auto
  actualizado a `v2.0.27` frente al pin `v2.0.26`. CORRECCION de un error
  propio: al redactar este ODD se afirmo "sin directorio plugins"; es falso.
  SI existe `~/.config/opencode/plugins/uso/tui.tsx` (455 lineas, plugin TUI de
  consumo por modelo). Tests, skills, config, drift, doctores, discovery,
  unittest, consulta staged y qa-gate strict estaban en verde.
- Hallazgo lateral: `~/tools/plugin_doctor.sh` solo inspecciona
  `$PLUGINS_DIR/*.js`, asi que no puede ver ese plugin `.tsx` y reporta
  "hooks en uso:" vacio de forma vacuamente cierta. Fuera de alcance: `~/tools`
  no es de este repo y el plugin es personalizacion del runtime.
- Snapshot observado: `health.ok=true`, `counts={skills:13, scripts:4, agentes:2,
  timers:3, flujos:3, componentes:24}`, generado 2026-10-11.
- `control/README.md:9` declara `(ODD, ODD delegado, QA-gate)`.
- T1: tests primero en `control/tests/test_panel_verdad.py` (nuevo, 11 tests).
  Rojo antes del fix: `Ran 11 tests ... FAILED (failures=7, errors=3)` con
  `AssertionError: 'pre-commit' unexpectedly found in 'qa-gate ...'`,
  `falta el flujo declarado 'cierre'`, `verify.sh no aparece como componente
  observado` y `el README debe aclarar el alcance de la salud`.
  Verde despues: `Ran 11 tests ... OK` (0.002s).
- T1 (estado final, comandos observados en la raiz del repo):
  - `python3 -m unittest discover -s control/tests -p "test_panel_verdad.py"` -> `Ran 11 tests in 0.002s OK`
  - `python3 -m unittest discover -s control/tests -p "test_control.py"` -> `Ran 11 tests in 0.052s OK`
  - `python3 -m unittest discover -s control/tests -p "test_frontend.py"` -> `Ran 25 tests in 0.052s OK` (incluye `node --check`)
  - `python3 -m unittest discover -s control/tests -p "test_graph.py"` -> `Ran 10 tests in 0.001s OK`
  - `python3 -m py_compile control/collect.py control/tests/test_panel_verdad.py` -> OK
  - Cambios: `collect.py` nuevo `_collect_root_entrypoints()` (kind script,
    fuente OBSERVADO, `is_file()` y lista vacia si no existe) invoked en
    `collect_snapshot`; `flows[3]` pasa a 4 (3 -> 4) y `componentes` 24 -> 25 en
    el repo real por `verify.sh`; `qa-gate` conserva id y steps sin hook;
    panel: `runtime sano` / `runtime: revisar` + `title`/`aria-label` con el
    alcance; README lista el flujo `cierre` y anade una linea de alcance.
- Verificacion independiente de T1 (odd-verifier read-only, contexto fresco):
  passed. Los 6 puntos del contrato se cumplen; los tests se confirmaron NO
  tautologicos por contrafactual (collect.py viejo: 3 failures + 3 errors;
  HTML viejo: fallan los 2 tests de etiqueta). Dos hallazgos `low` de
  mantenibilidad los corrigio el padre: `sources` sin `verify.sh` y la
  asercion `title|aria-label` anclada a una ventana de 200 chars que includia
  markup vecino (ahora anclada a los atributos propios del elemento).
- T2 (pin OpenCode): passed.
  - Antes de re-pinear se reviso la superficie del plugin `uso/tui.tsx` contra
    el binario `v2.0.27` con `grep -a`: PRESENTES `session.execution.succeeded`,
    `session.execution.failed`, `session.stats`, `prompt.footer.status` y
    `@opencode/plugin/tui`. Por eso el bump se acepto.
    `permission.ask` presente en el binario (hook conocido muerto, no lo usa el
    plugin). `tool.execute.before` AUSENTE en el binario.
    Advertencia: presencia de cadenas no prueba el renderizado del TUI.
  - `bash ~/tools/plugin_doctor.sh pin` -> pin `v2.0.27`.
  - `bash ~/tools/plugin_doctor.sh` -> `RESULTADO: plugins sanos`, exit 0.
- Cierre del padre (comandos observados, todos passed):
  - `python3 -m unittest discover -s control/tests` -> `Ran 245 tests in 26.642s`,
    `OK (skipped=1)`, exit 0.
  - `./verify.sh` -> `[ok] verify verde`, exit 0. Hygiene solo aviso informativo
    rc=1 (23 backups, 15 podables; prune es decision humana, fuera de alcance).
  - `./scripts/qa-gate.sh --strict` -> exit 0; staged no aplicable.
  - `python3 validate-skills.py skills` -> `[ok] 13 skills valid`.
  - `./opencode-ecosystem status` -> `[ok] sin drift`.
  - Snapshot observado tras el cambio: `counts={skills:13, comandos:0, scripts:5,
    agentes:2, timers:3, flujos:4, componentes:25}`;
    `verify` presente como `(script, observado)`; `sources` incluye `verify.sh`;
    flujos `['odd-delegado','odd','qa-gate','cierre']`; `pre-commit` en flujos:
    False.
- Nota de evolucion: `docs/evolution/2026-10-12-panel-verdad-declarado.md`.

## Progreso
- Estado: done (en observacion 7 dias desde 2026-10-12).
- T1: passed, con verificacion independiente en contexto fresco.
- T2: passed, con revision previa de hooks antes de aceptar la version.
- Cierre: suite 245 tests, verify verde, skills 13 validas, sin drift, QA exit 0.
- Ultima tarea: cierre completo y documentacion.
- Siguiente: observacion; si se decide, corregir el glob de `plugin_doctor.sh`
  (vive en `~/tools`, requiere autorizacion aparte).
- Bloqueos: ninguno. Sin stage, commit, push ni PR.