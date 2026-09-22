---
nombre: 2026-09-21-paridad-gentle-ai-lite
fecha: 2026-09-21
estado: en_observacion
afecta: [skills, configs, scripts, docs]
fuente: gentle-ai
---

# Paridad conceptual gentle-ai v3.4 (lite)

## Por que
gentle-ai avanzo de `eae8fadd5ece` (v3.1.0, baseline nuestro) a `d45bc428f515`
(main 2026-09-21) y publico `v3.2.1`-`v3.4.0`: delegacion ODD obligatoria,
review assess con `next_transition`, fail-closed en errores de review y RDD
activado por defecto. Nuestro contrato ODD tenia la forma pero no el endurecimiento:
SUMMARY/QUESTION podian faltar, la continuacion no era verificable y no habia
recibo por tarea. La primera implementacion confundio una continuacion autoritativa
del control-plane con texto del modelo y llego a ejecutar ese texto por shell; T7
corrige explicitamente ese comportamiento inseguro.

## Antes
- `RESULT: success` sin `SUMMARY` cerraba en `done`.
- `RESULT: blocked` sin `QUESTION` quedaba `waiting` indistinguible.
- No existia una transicion registrada del control-plane. La primera iteracion
  aceptaba `NEXT_TRANSITION` desde stdout del modelo y lo ejecutaba por bash.
- Sin recibo `receipt` por tarea completada.
- Skill no obligaba a delegar: el padre podia implementar trabajo sustancial inline.
- `doctor` no validaba version/capacidades de OpenCode V2 y no existia
  `task assess <worker-id>`.

## Despues
- Runner fail-closed: `success` sin `SUMMARY` o `blocked` sin `QUESTION` =
  error de contrato (reintento, nunca `done`).
- `NEXT_TRANSITION` o cualquier continuacion procedente del modelo nunca llega a
  shell: una salida ODD valida queda `waiting`, restaura el intento y no persiste
  el comando. Los prompts worker/verifier prohiben emitir continuaciones.
- Solo el control-plane registrado puede publicar una transicion ejecutable exacta.
  `task assess <worker-id>` informa la revision y solo publica `task run` cuando
  el verifier pendiente es primero en FIFO; no ejecuta el comando.
- `review_due` reutiliza `finished_at` del worker como dato informativo; no evalua
  reloj, deadline ni SLA.
- `RESULT: failed` del verifier pasa a `waiting` con `error_kind=review` para
  decision humana: sin consumo de intento, sin receipt y sin transicion; `retry`
  manual reanuda. El verifier ya no repite una revision fallida hasta `dead`.
- Regla global (`~/AGENTS.md`) alineada: `next_transition` verbatim solo para una
  operacion registrada del control-plane; una continuacion escrita por un modelo
  nunca llega a shell.
- `doctor` ejecuta `opencode --version` con argv/timeout, exige salida oficial y
  major 2, y declara capacidades V2 sin cache ni proceso permanente.
- Recibo `receipt` con estado `success` y nota `task #N <summary> [verifier pending]`
  por cada tarea `done`.
- Skill item 7: delegacion obligatoria para trabajo ODD sustancial; el inline
  queda para cambios pequenos sin documento.
- Prompts de `odd-worker`/`odd-verifier` declaran el contrato completo.
- OpenCode ausente, salida no oficial o major distinto de 2 hacen fallar `doctor`
  de forma explicita y sanitizada.

## Beneficio
- Paridad conceptual con v3.4 sin adoptar su maquinaria (RDD nativo, Engram,
  telemetria, TUI, Go, worktrees candidatos).
- Cero dependencias, cero procesos nuevos, cero migracion SQLite, cero tokens
  extra al arranque (solo texto de prompts existentes).

## No regresion
- Se conservan los 108 tests base; T4/T7/T8/T9/T12 amplian cobertura sin cambiar
  el esquema SQLite, dependencias ni procesos; T16 anade E2E opt-in (saltado en
  la suite normal y fuera de verify.sh).
- `sync --apply` sin drift; runtime actualizado.
- `verify.sh` verde; `qa-gate.sh --strict` exit 0.
- Estados/errores previos intactos: provider no consume intento, verification_command
  determinista, scrub de sensibles, purga de payloads.

## Verificacion
- T4: `python3 -m unittest control.tests.test_doctor -v` → 15/15 OK;
  cubre V2 compatible, V1 incompatible, binario ausente, salidas no oficiales,
  digitos Unicode, componentes desmesurados, errores de decodificacion y bytes
  reemplazados sin excepcion.
- T7: `test_model_next_transition_never_reaches_shell` → 1/1 OK; la salida del
  modelo queda `waiting`, sin shell, sin persistir comando y sin consumir intento.
- T8/T9: `python3 -m unittest control.tests.test_assess -v` → 8/8 OK; cubre
  `pending`, `due`, `passed`, `failed`, espera FIFO y transicion registrada exacta.
- T9: `python3 -m control.cli doctor --json` → OpenCode `2.0.12`, compatible con
  `2.x`, tres capacidades activas y `ok: true`.
- T10: `python3 -m unittest discover -s control/tests` → 136/136 OK;
  `python3 validate-skills.py skills` → 10 skills valid; status previo detecto el
  drift esperado de config/skill, `sync --apply` actualizo el runtime y el status
  posterior termino `[ok] sin drift`.
- T10 funcional: `doctor --json` → OpenCode `2.0.12`, compatible, tres capacidades
  activas y `ok: true`; las ayudas de `task`/`task assess` describen la consulta
  informativa sin ejecucion.
- Cierre T10: `./verify.sh` → `[ok] verify verde`; `qa-gate.sh --strict` y
  `git diff --check` → exit 0.
- Documento ODD: `odd/tasks/gentle-ai-parity-lite.md` con RED/verde y evidencia.
- T11/T13: regla global (`~/AGENTS.md`) alineada por procedencia y baseline
  actualizada a `654200afea34` (main +37 commits CI/tests via Compare API,
  estable sigue v3.4.0; delta clasificado, unico patron transferible E2E
  OpenCode aislado de npm/models.dev/red externa).
- T12: `python3 -m unittest discover -s control/tests` → 140/140 OK; RED de 4
  fallos (waiting/review, prioridad sobre transicion, retry manual, assess
  failed); `odd-verifier` independiente en contexto fresco: `Sin hallazgos.`
  de contrato.
- Cierre Fase A: `./verify.sh` → `[ok] verify verde`; `qa-gate.sh --strict` y
  `git diff --check` → exit 0.
- T16: spike efimero fuera del repo (OpenCode real + proveedor OpenAI-compatible
  simulado en loopback: exit=0, 4.2s, SSE streamed, sin egress externo, sin npm
  bootstrap); hallazgo: sin `--standalone` el cliente con env aislado se cuelga.
  E2E opt-in `control/tests/test_odd_e2e.py` persistido: recorrido real
  worker → verifier unico → `assess passed`, receipts, DB efimera y sin
  secretos en DB; wrapper efimero de `opencode` en `PATH` anade `--standalone`
  solo en el test (el lanzador de produccion no cambia; hook de test en
  produccion descartado). README documenta el uso opt-in.
  Cierre: suite 141/141 con E2E saltado; E2E real OK 2.7s; `./verify.sh` verde;
  `qa-gate.sh --strict` exit 0; `git diff --check` ok.

## Periodo prudencial
- Duracion: hasta 2026-10-05 o 2 features sustanciales delegadas con dogfood real.
- Estable si: ninguna tarea sustancial queda `done` sin SUMMARY; bloqueos llevan
  QUESTION; una revision fallida del verifier queda `waiting` sin repetirse;
  ningun texto del modelo llega a shell; `assess` describe fielmente la
  cola y solo el control-plane publica transiciones registradas.
- Revertir si: hay falsos `contract`, una continuacion del modelo alcanza shell,
  `assess` altera estado o `doctor` acepta una salida/version incompatible.
  Rollback: restaurar desde la base Git los cambios de runner/CLI/config/skill,
  resincronizar y mantener deshabilitada cualquier continuacion ejecutable.
- Base reversible: estado previo en Git (`f4cf9c8` para T11-T13; `2c711e0` para
  T4/T7-T10); specs anteriores se conservan como historial.

## Fuente
- `~/docs/sources/gentle-ai-analysis.md` (seccion Revision 2026-09-21, baseline
  `eae8fadd5ece..654200afea34`, estable `v3.4.0`).
