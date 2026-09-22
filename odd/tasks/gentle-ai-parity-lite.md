# Paridad conceptual gentle-ai v3.4 (paridad ligera)

## Objetivo

Acercar `opencode-ecosystem` al comportamiento conceptual de gentle-ai v3.4.0 manteniendo nuestra filosofia: autorizacion humana, ODD-lite, ahorro de memoria/tokens y ausencia de maquinaria innecesaria.

## Problema y por que

Gentle-AI publico v3.2.1-v3.4.0 tras nuestra ultima alineacion. Lo relevante es la disciplina de parl: delegacion obligatoria para trabajo sustancial, evidencia fall-closed, transiciones exactas y OpenCode V2 consciente de version. Hoy la disciplina esta descrita pero no esta completamente endurecida ni verificada por tests. Quien lo sufre: cualquier feature delegada, bloqueada, reanudada o con salida incompleta.

## Alcance

### Incluye

- Contrato ODD de delegacion y verificacion para trabajo sustancial.
- Fail-closed de resultados y continuaciones.
- Literalidad de `next_transition` con consumo explicito y bloqueo seguro.
- `next_transition` separado por procedencia: el texto del modelo nunca llega a shell; solo el control-plane puede emitir una continuacion ejecutable registrada.
- Diagnostico OpenCode V2 version-aware bajo demanda y `assess` informativo derivado del estado existente.
- Recibos/evidencia ligera reutilizando eventos existentes.
- Revision fallida del verifier: pasa a `waiting` para decision humana, sin consumo de intento ni receipt.
- Rebaseline externa (main `654200afea34`, estable v3.4.0) y E2E OpenCode real offline como patron futuro condicionado.
- Pruebas evolucion y nota de analisis de origen.

### Excluye

- Migracion del esquema SQLite.
- RDD completo, receipts criptograficos, lineage, snapshots, worktrees ni store-reset.
- Engram, telemetria VictoriaMetrics, RTK, TUI, Gentle Shell, binario Go.
- Commits automaticos, ramas, push, PR o release.
- Nuevos procesos, daemons, dependencias externas o memoria adicional.
- E2E permanente o con llamadas cloud: solo opt-in offline con proveedor simulado.

## Restricciones

- Python stdlib solamente.
- i5-1235U/8GB: cero procesos permanentes ni polling agresivo.
- Espanol en docs/skills y sin acentos en contenido de skills.
- No persistir stdout completo ni secretos.
- Cierre Git solo si el humano lo pide explicitamente.

## No romper

- 108/108 tests actuales y style de control.
- `validate-skills.py skills`, `./verify.sh`, `qa-gate.sh --strict`.
- `status` sin drift tras sincronizar skills.
- API/panel sin prompts, workspace ni comandos expuestos.
- Workflows y configuraciones existentes que no se tocan.
- Worker y agentes genericos conservan su politica de reintento (max 2 -> dead); solo `odd-verifier` con `RESULT: failed` pasa a `waiting` para decision humana.

## TDD

- Modo: on
- Fuente: usuario (iterar hasta terminar y corregir errores)
- Runner: `python3 -m unittest discover -s control/tests` + checks funcionales

## Tareas

- [x] T1 - Documentar contrato de paridad en skill y control documental.
- [x] T2 - Endurecer runner fail-closed, next_transition y evidencia minima.
- [x] T3 - Hacer obligatoria la delegacion ODD sustancial con ruta unica worker/verifier.
- [x] T4 - Añadir version-aware ligero de OpenCode en doctor, sin proceso nuevo. Reabierta y cerrada: ahora comprueba version/capacidades.
- [x] T5 - Dogfood: tarea pequena inline, tarea sustancial delegada, bloqueo, reanudacion y continuacion invalida.
- [x] T6 - Documentar evolution + revision del analisis gentle-ai y cerrar con verify/qa-gate.
- [x] T7 - Sustituir la ejecucion de shell desde `NEXT_TRANSITION` por fail-closed sin shell para transiciones del modelo.
- [x] T8 - Añadir `task assess` informativo con `review_state`, `review_due` y continuacion emitida por codigo.
- [x] T9 - Dogfood de transicion desconocida, assess pending/passed/failed y OpenCode V2 compatible/incompatible.
- [x] T10 - Actualizar skill, prompts, README y evolution; sincronizar y ejecutar cierre completo.
- [x] T11 - Alinear la regla global de `next_transition` con la procedencia: solo una operacion registrada del control-plane es ejecutable; el texto del modelo nunca llega a shell.
- [x] T12 - `odd-verifier` con `RESULT: failed` pasa a `waiting` (error_kind=review) sin quemar intento ni receipt; `assess` informa failed y no emite transicion; retry manual reanuda.
- [x] T13 - Rebaseline gentle-ai: main `654200afea34` (+37 commits CI/tests), estable v3.4.0; clasificar delta y marcar E2E aislado como patron a tomar.
- [ ] T14 - Dogfood Fase B: dos features sustanciales reales posteriores a f4cf9c8 con worker/verifier, receipts y assess; registrar intentos, falsos contratos y divergencias (hasta 2026-10-05).
- [ ] T15 - Puerta de decision tras T14: solo si aparece brecha, rama minima (verifier failed, worker done sin verifier, preflight ODD, task trace) con aprobacion.
- [x] T16 - E2E opcional OpenCode real offline: spike efimero fuera del repo; persistir `test_odd_e2e` solo si es barato (OPENCODE_E2E=1, sin tokens ni red externa).
- [ ] T17 - Cierre: docs, gates completos, verifier independiente y periodo prudencial.

## Criterios de aceptacion

- Una tarea sustancial ODD pasa siempre por `odd-worker`; una exitosa encadena `odd-verifier`.
- RESULT ausente o invalido nunca termina en `done`.
- Una transicion devuelta por el modelo nunca se ejecuta como shell; si no existe operacion registrada queda `waiting` sin consumir intento.
- Solo el control-plane puede emitir una continuacion ejecutable exacta; `assess` es informativo y no bloquea por reloj.
- `doctor` observa version OpenCode y falla explicito si no es V2 compatible.
- Errores de proveedor/cuota no consumen intentos funcionales.
- Los recibos/eventos permiten reconstruir estado sin stdout completo.
- Sin migracion SQLite ni dependencias nuevas.
- Verificaciones finales verdes y sin drift.

## Decisiones aceptadas

- 2026-09-21: adoptar paridad conceptual minima, no mecanica.
- 2026-09-21: reutilizar recibos y estados existentes en lugar de migrar SQLite.
- 2026-09-21: no activar RDD, telemetria, Engram ni entrega automatica.
- 2026-09-21: corregir el contrato anterior: ejecutar shell desde stdout del modelo no es equivalente al `next_transition` autoritativo de gentle-ai y queda prohibido.
- 2026-09-21: la revision fallida del verifier no se repite automaticamente: pasa a `waiting` con `error_kind=review` para decision humana (evita gastar tokens en reintentos inutiles).
- 2026-09-21: el E2E solo se persiste si el spike efimero es barato y queda fuera de verify.sh (OPENCODE_E2E=1, opt-in).

## Reutilizacion investigada

- Runner existente: cola atomica, leases, estados, encadenamiento worker->verifier, scrub de salida.
- Recibo existente: `record_receipt` como evento acotado.
- Skill existente: `organic-workflow-lite` como contrato documental.
- T7 reutiliza `waiting`, la devolucion de intento de `RESULT: blocked`, `update_task` y `record_event`; no crea registro ni helper antes de que T8 aporte una operacion del control-plane.
- T4 reutiliza el patron stdlib `subprocess.run` con argv y timeout ya usado por control; no existia un diagnostico de version equivalente que reutilizar.
- T8 reutiliza `tasks.status`, `tasks.finished_at` y `tasks.parent_id`; las lecturas dirigidas devuelven solo columnas publicas y no requieren migracion ni reloj.
- Alternativas descartadas: RDD completo y nueva tabla/columnas SQLite por YAGNI.

## Evidencia

- T0 base - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests`; `python3 validate-skills.py skills`; `./opencode-ecosystem status`
  - Resultado: 108/108 OK; 10 skills valid; sin drift
- T1 - Estado: passed
  - Comando: edicion de `skills/organic-workflow-lite/SKILL.md` (items 7-8), `configs/opencode.jsonc` (prompts worker/verifier) y `control/README.md` (reglas del lanzador)
  - Resultado: contrato escrito: delegacion obligatoria para trabajo sustancial, SUMMARY/QUESTION obligatorios, NEXT_TRANSITION verbatim
- T2 - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests`
  - Resultado: 115/115 OK tras RED de 7 tests nuevos (fail-closed SUMMARY/QUESTION, recibo exacto, verifier encadenado, NEXT_TRANSITION ejecutado verbatim y fallo -> pending)
  - Nota: errata autodetectada y corregida — se propuso columna SQLite para la transicion; se revirtio para respetar "no migrar esquema" y la transicion pasa por el contrato acotado de stdout
- T3 - Estado: passed
  - Comando: revision de `skills/organic-workflow-lite/SKILL.md` item 7 + prompts `odd-worker`/`odd-verifier` en `configs/opencode.jsonc` + `control/README.md`; `./opencode-ecosystem sync --apply && ./opencode-ecosystem status`
  - Resultado: `[ok] 10 skills valid`, `[ok] sync aplicado`, `[ok] sin drift`
- T4 - Estado: passed (reabierta y cerrada)
  - RED: `python3 -m unittest control.tests.test_doctor` -> 9 errores por helper/campo OpenCode ausente.
  - GREEN: `python3 -m unittest control.tests.test_doctor` -> 10/10 OK; `python3 -m unittest discover -s control/tests` -> 123/123 OK.
  - Funcional: `python3 -m control.cli doctor --json` y `python3 -m control.cli doctor` -> OpenCode `2.0.12`, compatible con `2.x`, capacidades `run`, `debug_config` y `service_status` activas; salida sanitizada.
  - Cierre: `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` -> exit 0.
  - Correccion parser RED: `python3 -m unittest control.tests.test_doctor` -> 1 fallo: una salida enganosa con semver interno se marcaba compatible.
  - Correccion parser GREEN: `python3 -m unittest control.tests.test_doctor` -> 11/11 OK; `python3 -m unittest discover -s control/tests` -> 132/132 OK; `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` y `git diff --check` -> exit 0.
  - Hardening ASCII RED: `python3 -m unittest control.tests.test_doctor` -> 1 fallo (digitos Unicode aceptados) y 1 error (`ValueError` con componente de 10 000 digitos).
  - Hardening ASCII GREEN: `python3 -m unittest control.tests.test_doctor` -> 13/13 OK; `python3 -m unittest discover -s control/tests` -> 134/134 OK; `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` y `git diff --check` -> exit 0.
  - Decodificacion RED: `python3 -m unittest control.tests.test_doctor` -> 2 errores: faltaban `encoding/errors` explicitos y `UnicodeDecodeError` escapaba del diagnostico; una salida con caracter de reemplazo ya quedaba incompatible.
  - Decodificacion GREEN: `python3 -m unittest control.tests.test_doctor` -> 15/15 OK; `python3 -m unittest discover -s control/tests` -> 136/136 OK; `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` y `git diff --check` -> exit 0.
  - Resultado: diagnostico bajo demanda con argv sin shell, timeout de 3s, decodificacion UTF-8 con `errors=replace` y captura defensiva de `UnicodeError`; parseo fail-closed anclado al formato completo `opencode vX.Y.Z` (case-insensitive, solo whitespace exterior), con componentes ASCII de 1-3 digitos; binario ausente, salida no oficial, Unicode, bytes reemplazados, componentes desmesurados o major distinto de 2 son incompatibles sin excepcion; sin cache, dependencias, proceso permanente ni migracion SQLite.
- T5 - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests`
  - Resultado: dogfood por escenarios reales del runner: pequena inline (qa-gate sin contrato -> done), sustancial delegada (worker -> verifier encadenado), bloqueo con QUESTION -> waiting sin consumir intento, blocked sin QUESTION -> contrato, NEXT_TRANSITION invalido -> pending (error_kind=transition), recibo exacto por tarea done
- T6 - Estado: passed
  - Comando: `./verify.sh && ./scripts/qa-gate.sh --strict`
  - Resultado: `[ok] verify verde`, qa-gate exit 0; evolution doc `docs/evolution/2026-09-21-paridad-gentle-ai-lite.md` y seccion nueva en `~/docs/sources/gentle-ai-analysis.md`
- T7 - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests`; `./verify.sh`; `./scripts/qa-gate.sh --strict`
  - Resultado: revision RED con 2 fallos (contrato incompleto y agente generico); GREEN 117/117 OK; verify verde y qa-gate exit 0. El contrato ODD se valida antes de la transicion: salida incompleta queda `pending`/`contract`; salida ODD valida queda `waiting` sin shell ni consumo de intento. Agentes genericos ignoran la transicion.
- T8 - Estado: passed
  - RED: `python3 -m unittest control.tests.test_assess` -> 13 errores por `assess_task` ausente.
  - GREEN: `python3 -m unittest control.tests.test_assess` -> 7/7 OK; `python3 -m unittest discover -s control/tests` -> 130/130 OK.
  - Funcional: `python3 -m control.cli task assess 1` sobre DB temporal -> JSON `due`, verifier `2`, `review_due` persistido y transicion exacta; secretos ausentes.
  - Cierre: `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` y `git diff --check` -> exit 0.
  - Correccion FIFO RED: `python3 -m unittest control.tests.test_assess` -> 2 fallos: transicion emitida con otra tarea delante y reason ambiguo para verifier `waiting`.
  - Correccion FIFO GREEN: `python3 -m unittest control.tests.test_assess` -> 8/8 OK; `python3 -m unittest discover -s control/tests` -> 131/131 OK; `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` y `git diff --check` -> exit 0.
  - Resultado: `task assess <worker-id>` informa estados worker/verifier con JSON de seis campos sanitizados; solo el verifier `pending` que es primero en FIFO emite literalmente `python3 -m control.cli task run`; si espera turno sigue `due` sin comando, y `waiting` informa que espera decision; `review_due` reutiliza `finished_at` del worker sin evaluar el reloj; sin migracion SQLite.
- T9 - Estado: passed
  - Transicion ODD dirigida: `python3 -m unittest control.tests.test_runner.TestRunner.test_model_next_transition_never_reaches_shell -v` -> 1/1 OK; una transicion desconocida queda `waiting`, restaura el intento a 0, no invoca `subprocess.run` y no persiste el comando en nota ni eventos.
  - Assess dirigido: `python3 -m unittest control.tests.test_assess -v` -> 8/8 OK; cubre `pending`, `due`, `passed`, `failed` y FIFO sin transicion cuando otra tarea espera antes.
  - Assess funcional: cinco invocaciones reales `python3 -m control.cli task assess <id>` sobre SQLite temporal -> `pending`, `due`, FIFO `due` con `next_transition: ""`, `passed` y `failed`; DB eliminada al salir.
  - Doctor simulado: `python3 -m unittest control.tests.test_doctor -v` -> 11/11 OK; cubre V2 `2.0.12`, incompatible V1, binario ausente, salida malformed y salida enganosa con semver interno.
  - Doctor real: `python3 -m control.cli doctor --json` -> exit 0, OpenCode disponible `2.0.12`, compatible con `2.x`, tres capacidades activas y diagnostico global `ok: true`.
  - Cierre: `python3 -m unittest discover -s control/tests` -> 132/132 OK; `python3 validate-skills.py skills` -> 10 skills valid; `./opencode-ecosystem status` -> sin drift; `./verify.sh` -> verify verde; `./scripts/qa-gate.sh --strict` y `git diff --check` -> exit 0.
  - Resultado: dogfood completado sin proveedor ni gasto de tokens; no fue necesario cambiar codigo.
- T10 - Estado: passed
  - Contrato: skill y prompts worker/verifier prohiben emitir continuaciones; README y evolution distinguen texto del modelo (siempre `waiting`, nunca shell) de transiciones registradas del control-plane. CLI help declara `assess` informativo.
  - Comando: `python3 validate-skills.py skills`; `./opencode-ecosystem status`; `./opencode-ecosystem sync --apply`; `./opencode-ecosystem status`.
  - Resultado: 10 skills valid; drift esperado de config/skill antes del sync; sync aplicado con backup; status posterior `[ok] sin drift`.
  - Comando: `python3 -m unittest discover -s control/tests`; `python3 -m control.cli doctor --json`; `python3 -m control.cli task --help`; `python3 -m control.cli task assess --help`.
  - Resultado: 136/136 OK; doctor real OpenCode `2.0.12`, compatible con `2.x`, tres capacidades activas y `ok: true`; ayuda coherente sin duplicar comandos.
  - Cierre: `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` y `git diff --check` -> exit 0.
  - Periodo prudencial: en observacion hasta 2026-10-05 o 2 features sustanciales delegadas; base reversible Git `2c711e0`, sin commit nuevo.
- T12 - Estado: passed
  - RED: `python3 -m unittest control.tests.test_runner control.tests.test_assess` -> 4 fallos (verifier failed -> pending en vez de waiting, failed+transicion sin prioridad de revision, retry manual rechazado, assess waiting-review da pending).
  - GREEN: `python3 -m unittest control.tests.test_runner control.tests.test_assess` -> 38/38 OK; `python3 -m unittest discover -s control/tests` -> 140/140 OK (incluye test_declared_failure_uses_normal_retry del worker y test_estados_del_verifier con waiting sin error_kind -> pending).
  - Resultado: `odd-verifier` con `RESULT: failed` pasa a `waiting` con `error_kind=review`, intento restaurado (`attempts=max(0, attempts-1)`), nota acotada `[:200]` sin stdout, evento `review/warn` y sin receipt de exito; la rama va antes de la transicion (failed+transicion clasifica como revision fallida); worker y agentes genericos conservan su politica (reintento, max 2 -> dead); `assess` distingue por procedencia: waiting con `error_kind=review` -> `failed` con reason `revision fallida (espera decision)` y sin next_transition; waiting sin error_kind sigue `pending`; `actions.do_retry` reencola ese waiting a pending.
  - Cierre: `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` -> exit 0; `git diff --check` -> ok. Sin migracion SQLite, sin dependencias ni procesos nuevos.
  - Verificacion independiente (odd-verifier, contexto fresco): `Sin hallazgos.` de contrato; 140/140 OK reproducidos; hallazgo cosmico de Progreso corregido en el mismo cierre.
- T11 - Estado: passed (inline docs, effort low segun routing)
  - Comando: edicion de `~/AGENTS.md` (regla de continuaciones); revision dirigida de skill/prompts/README/runner ya coherentes tras T7/T10/T12.
  - Resultado: la regla global distingue procedencia: verbatim solo para operacion registrada del control-plane; texto del modelo nunca llega a shell y deja la tarea en waiting. El sistema recordo el cambio de AGENTS.md sin drift.
- T13 - Estado: passed (inline docs, effort low segun routing)
  - Comando: GitHub API `commits/main` + `releases/latest` + `compare/d45bc428f515...654200afea34` (37 commits).
  - Resultado: baseline actualizada a `654200afea34` (2026-09-21 via GitHub API; estable sigue v3.4.0) en `~/docs/sources/gentle-ai-analysis.md` con delta clasificado: unico patron transferible E2E OpenCode aislado de npm/models.dev/red externa; gate 400-lineas y PR automation sin adoptar.
- T16 - Estado: passed (opt-in OPENCODE_E2E=1; fuera de verify.sh)
  - Spike efimero: `/tmp/opencode/e2e-spike/run_spike.py` -> exit=0, 4.2s, 2 llamadas streamed a /v1/chat/completions, texto determinista en stdout, sin egress externo (proxy muerto para todo menos loopback), sin npm bootstrap.
  - Hallazgo clave: SIN `--standalone` el cliente con env aislado se cuelga (60s, 0 llamadas al mock); CON `--standalone` funciona.
  - Rework (plan mejorado aprobado): hook descartado de `control/runner.py` (logica de test en produccion; revertido junto con `import os`); el E2E crea un wrapper efimero de `opencode` en `PATH` que anade `--standalone` a `run` y ejecuta el binario real; el lanzador de produccion no cambia.
  - Validacion: hook 2/2 OK por el worker antes del rework; tras el rework el recorrido real cubre el wrapper (clase TestStandaloneHook eliminada).
  - Recorrido real: `OPENCODE_E2E=1 python3 -m unittest control.tests.test_odd_e2e -v` -> OK en 2.7s tras el rework (3/3 en 6.6s con el hook previo). Servidor mock ThreadingHTTPServer en loopback (puerto efimero) con patron SSE del spike (streaming si stream:true, JSON si no); env aislado para el hijo via os.environ (HOME/XDG_* /OPENCODE_CONFIG_DIR bajo HOME temporal, MOCK_API_KEY=dummy, OPENCODE_DISABLE_MODELS_FETCH=1, proxy muerto, NO_PROXY loopback); DB temporal con db.init_db; workspace dentro del HOME temporal; worker odd-worker model=mock/test verification_command=true -> done con recibo y verifier unico (parent_id); segundo run_next -> verifier done con check determinista rc=0 y recibo; `cli.assess_task(worker_id, db)` -> review_state passed.
  - Aserciones finales: solo loopback alcanzo el mock (>= 2 llamadas a /chat/completions), sin payload privado ni secretos en DB (list_tasks include_private=False; sin prompt/workspace/comandos ni "dummy"), un solo verifier, resumen acotado persistido como nota y stdout completo ausente.
  - Cierre: `python3 -m unittest discover -s control/tests` -> 141/141 OK con test_odd_e2e saltado; `./verify.sh` -> `[ok] verify verde`; `./scripts/qa-gate.sh --strict` exit 0; `git diff --check` ok. Reutilizado el mock SSE y el env de aislamiento del spike; sin migracion SQLite, sin dependencias, sin procesos permanentes; README documenta el uso opt-in.

## Progreso

- Estado: en_progreso (Fase A T11-T13 y T16 completadas; Fase B dogfood con 2 features reales pendiente hasta 2026-10-05)
- Ultima tarea terminada: T16
- Siguiente paso: T14 (dos features sustanciales reales con worker/verifier)
- Bloqueos: ninguno
