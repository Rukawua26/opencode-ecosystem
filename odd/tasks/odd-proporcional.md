# ODD proporcional

## Objetivo
Aplicar paso 4 aprobado: separar documento recuperable, delegacion util y verificacion independiente por riesgo, manteniendo checks obligatorios y autorizacion humana.

## Problema y por que
Skill obliga worker+verifier para todo ODD y cierre lo condiciona al riesgo. Reglas globales usan conteos como gatillos; verifier rechaza implementacion inline. Coste innecesario y contradicciones operativas.

## Alcance
Instrucciones globales ~/AGENTS.md (versionadas en repo HOME), skill fuente, prompt verifier, README y control/README, evolucion. Motivos de delegacion: contexto limpio, paralelismo realmente independiente o aislamiento justificado. Riesgos para revision independiente: datos persistentes, seguridad, contratos, concurrencia, entrega/entorno o falta de prueba eficaz; incertidumbre peligrosa se aclara, nunca se interpreta como bajo riesgo.

## Restricciones
No cambiar runner, CLI, esquema DB, permisos ni contratos control-plane. Flujo gestionado que ya entro sigue worker->verifier obligatorio; no saltar gates ni reevaluar tareas previas automaticamente. No commits, deps, modelos, timers, umbrales, plugins personales, memoria viva, receipts/logs/backups manuales. Sync oficial solo configuracion/skill gestionadas tras auditoria y validacion. No modificar historial ni cambios previos ajenos.
Excepcion posterior autorizada al limite CLI: guarda y escrituras de
`cmd_sync` para limitarse a rutas gestionadas, con tests de regresion.

## No romper
Aprobacion humana de alcance sustancial y registro antes de editar se mantienen; no todos los trabajos requieren documento solo por contar archivos. Checks funcionales siguen obligatorios para inline/delegado. Mantener SUMMARY/RESULT fail-closed y continuaciones registradas. Verifier read-only puede revisar codigo inline pero no emitir continuaciones ni autorizar mutaciones. Guardas especializadas seguridad/arquitectura no se eliminan por ahorro; conteos de capas/lecturas son señales, no obligacion ciega.

## TDD
Modo: off. Fuente: default. Runner: python3 -m unittest discover -s control/tests. Checks funcionales y revision de escenarios obligatorios.

## Tareas
- [x] T1: worker aplica cambios minimos coherentes; verifica baselines Git exactos de HOME/AGENTS y fuente, reutiliza clausulas; conserva flujo gestionado y clarifica seleccion proporcional. Ejemplos verificables: pequeno inline sin documento, recuperable bajo riesgo inline documentado con checks, alto riesgo verifier incluso sin worker, flujo control-plane conserva cadena. No reescribir normas no relacionadas. Documenta evolucion y evidencia, valida skills antes sync, status antes/despues, sync oficial seguro de gestionados, comprobar runtime, tests/verify/qa completos y hashes config semantica sin secretos.
- [x] T2: verificador independiente contrasta reglas/riesgos/contratos y checks, corrige worker si hallazgos reales.

## Criterios de aceptacion
- [x] Documento no obliga delegar; motivos explicitos y checks siempre.
- [x] Verificador por riesgo concreto, no por tamano o existencia worker; incertidumbre peligrosa no se ignora.
- [x] Runner conserva cadena, contratos/permisos/modelos intactos.
- [x] Reglas activas/skill/docs coherentes y runtime sin drift; checks completos verdes.

## Decisiones aceptadas
Ampliacion autorizada: corregir guarda de sync para comprobar solo rutas
gestionadas, sin recorrer ni tocar node_modules/personalizaciones; reutilizar
tests de mutaciones y completar sync oficial, runtime y checks de cierre.
Cambiar politica de seleccion, no maquinaria. Reutilizar agentes/ODD y mantener proceso gestionado mas estricto. Cambio minimo sin framework ni tests fragiles basados en frases exactas. Usuario aprueba como mejor opcion; registro fuente evolucion sin crear skill nueva.

## Reutilizacion investigada
Exploracion dirigida: ~/AGENTS.md versionado repo HOME; skill puntos7/11 contradictorios; config prompt verifier exige worker; README diagrama y control/README; runner encadena y tests ya cubren. No se anade global AGENTS al manifiesto sync.

## Evidencia
T1 completada tras ampliacion autorizada. Evidencia inicial y resolucion
conservadas a continuacion. Trabajo anterior conservado.

- Baselines exactos: HOME `ba62b2f1c3911630f8f7262b5cca07d964ab22f7`
  (AGENTS limpio antes de editar); ECO `8bc6069231768db00841dd679655bd168695b5f7`.
  Evolucion: `docs/evolution/20261014-odd-proporcional.md`.
- Estado: passed. Revision de escenarios por inspeccion de reglas:
  pequeno entendido inline sin documento; recuperable bajo riesgo inline con
  ODD aprobado y checks; alto riesgo exige independiente aunque no haya worker;
  al entrar control-plane exito worker sigue siempre verifier. No se han
  observado aun sesiones reales de esos escenarios: observacion pending.
- Estado: passed. No nuevos helpers ni tests de frases; reutilizados contratos
  y tests existentes `test_success_implementer_chains_verifier`,
  `test_worker_success_always_chains_verifier`,
  `test_verifier_requires_deterministic_check`,
  `test_missing_summary_is_fail_closed`,
  `test_model_next_transition_never_reaches_shell` (suite completa).
- Estado: passed. `python3 -m unittest discover -s control/tests`:
  340 tests, OK (skipped=1, E2E opt-in no ejecutado).
- Estado: passed. `python3 validate-skills.py skills`: 13 skills valid.
- Estado: passed. `git diff --check` y HOME `git diff --check -- AGENTS.md`.
- Estado: passed. Auditoria previa: scripts/commands/dcp/cron y scripts de
  memoria gestionados iguales a runtime; MEMORY.md existente. Solo config
  prompt verifier y skill divergen. Semantica config salvo system verifier
  antes/despues SHA-256 `292cbdaead066546e6b0f3fc1d8ec88c5e6f57f6453bc91886a2d2a0d977469a`;
  permisos/modelos intactos, sin volcar valores sensibles. Runner, ejecutable
  sync y docs/zap-mcp.md mantienen hashes previos (ver evolucion).
- Estado: passed antes de editar. `./opencode-ecosystem status`: `[ok] sin drift`.
- Estado: failed. `./opencode-ecosystem sync --apply`: rc=1 tras validar skills,
  antes de copias. `safe_tree` detecta enlaces de personalizaciones en
  `~/.config/opencode/node_modules/.bin/` (uuid, yaml, node-gyp, etc.).
  No se eliminan, no se sortea guarda, no se cambia script fuera de alcance.
- Estado: failed despues del intento. `./opencode-ecosystem status`:
  rc=1, drift esperado en opencode.jsonc y skills. Runtime no actualizado.
- Estado: failed. `./verify.sh`: rc=1 solo status drift; skills fuente/runtime,
  debug config, plugin/context doctor, discovery/unittest y QA strict rc=0.
- Estado: passed. `scripts/qa-gate.sh --strict`: rc=0, staged no aplicable;
  comprueba rutas rastreadas, no certifica cambios unstaged.

## Progreso
T1 y T2 completadas; cierre registrado. El padre actualizo el documento con la
evidencia del verificador (cambio pequeno inline conforme a la politica
proporcional recien aprobada). No se delego desde worker ni se emitieron
continuaciones. Sin commits ni cambios runner. Persiste solo la observacion
real de escenarios documentada arriba.

## Evidencia de resolucion autorizada
- Estado: passed. Test existente ampliado de mutaciones reproduce RED (rc=1)
  con enlaces personales y stub que rechaza recorrer raiz runtime. GREEN:
  19 tests de mutaciones, contenido/modo/enlaces personales conservados.
  No tests de frases, helpers ni dependencias.
- Guarda sync valida solo rutas copiadas/escritas y sus antecesores; no
  recorre node_modules ni personalizaciones ajenas. Chmod solo scripts fuente;
  config/comandos/scripts de memoria iguales evitan copias y backups innecesarios.
  Topics no se crea; test existente de memoria prepara explicitamente su
  carpeta personal. Suite inicial detecto ese fixture antiguo (1 error),
  corregido sin restaurar la mutacion de memoria personal.
- Estado: passed. `python3 validate-skills.py skills`: 13 skills valid antes
  del sync y despues. `./opencode-ecosystem status` antes del sync: rc=1 solo
  drift esperado opencode.jsonc/skills; tras `sync --apply` rc=0, `[ok] sin drift`.
- Estado: passed. `./opencode-ecosystem sync --apply`: rc=0, unico backup
  anunciado opencode.jsonc; sin tocar node_modules ni personalizaciones.
- Estado: passed. Comparacion exacta de skill y config runtime con fuente;
  misma semantica config salvo system verifier (hash previo conservado),
  runner y docs/zap-mcp.md mantienen hashes anteriores.
- Estado: passed. `python3 -m unittest discover -s control/tests` final:
  340 tests OK, skipped=1 (E2E opt-in). Ejecucion completa repetida por verify.
- Estado: passed. `./verify.sh`: rc=0, `[ok] verify verde`. Hygiene trigger
  informativo rc=1 no bloqueante; todos los checks obligatorios rc=0.
- Estado: passed. `scripts/qa-gate.sh --strict`: rc=0. Sin staged, solo rutas
  rastreadas; no certifica unstaged. `git diff --check`: rc=0.
- Base reversible del sync previo no commiteado en
  `docs/evolution/20261014-odd-proporcional.before.md`; conserva trabajo ajeno.

## Evidencia T2 — verificacion independiente, 2026-10-14
- Estado: passed. odd-verifier read-only en contexto fresco, sin modificar ni
  delegar: `Sin hallazgos` dentro del alcance. Confirmo coherencia de reglas
  globales/skill/prompt/README (inline permitido, delegacion por motivo,
  independiente por riesgo incluso inline, checks siempre, incertidumbre
  peligrosa se aclara) sin contradicciones activas tipo siempre/por tamano.
- Estado: passed. Runner y contratos control-plane intactos: cadena
  worker->verifier fail-closed, sin saltos de gates. Config sin cambios
  semanticos alucinados; permisos/modelos conservados. AGENTS global sigue
  fuera del manifiesto sync.
- Estado: passed. 57 tests focales OK; 13 skills runtime validas; fuente y
  runtime identicos; `./opencode-ecosystem status`: `[ok] sin drift`. No
  ejecuto verify.sh (escribe informe) ni mutaciones sobre HOME real.
- Estado: pending. Observacion real de los escenarios (pequeno inline,
  recuperable bajo riesgo, alto riesgo sin worker, flujo gestionado); no
  bloquea el cierre local ni se presenta como estabilidad medida.
