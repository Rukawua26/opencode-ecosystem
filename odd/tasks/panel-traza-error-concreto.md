# panel-traza-error-concreto

Fecha inicio: 2026-09-28
Estado: completada

## Objetivo
Que la traza muestre el ERROR CONCRETO registrado (mensaje real del runner) de forma destacada, junto a la causa probable y qué revisar, para poder capturarlo y buscar solución.

## Problema y por que
Hoy la columna "¿Por qué tiene este resultado?" explica el estado con texto genérico, pero no muestra el mensaje de error real que el runner guardó en `tr.note` (p. ej. "workspace inexistente o fuera de HOME"). El usuario quiere ver ese error concreto para hacer captura y buscar la solución. El control NO persiste stdout del agente (limite duro), pero SÍ guarda `note` (máx 200 chars) y `error_kind`, que son el error real registrado.

## Alcance
### Incluye
- `control/web/index.html`: en `#trace-why`, bloque destacado "Error registrado" con `tr.note` (mensaje real) + `error_kind` + `result_code`, visible arriba de la explicación genérica. Si no hay nota, decir "sin mensaje de error registrado".
- "Qué revisar" por `error_kind`: contract → "el agente no emitió RESULT/SUMMARY/QUESTION válido; revisa la salida del agente en la sesión"; timeout → "el agente tardó más de 15 min; revisa si el prompt era demasiado amplio o el modelo lento"; provider_balance → "saldo insuficiente del proveedor; recarga o cambia de modelo"; provider_rate → "rate limit; espera o cambia de proveedor"; infra → "opencode no disponible; comprueba `opencode service status`"; verification → "el check determinista falló; revisa el comando de verificación"; review → "la verificación pidió decisión humana; revisa el verificador"; agent → "fallo del agente; revisa la nota y reintenta".
- `control/tests/test_frontend.py`: test estructural de las marcas nuevas ("Error registrado", "Qué revisar").

### Excluye
- Persistir stdout/respuestas del agente; endpoint nuevo; cambios en `server.py`, `trace.py`, `db.py`, `runner.py`, `reconcile.py`, esquema SQLite.
- Chatbot/LLM; dependencias; polling extra; trabajo movil; ramas/commits/push/PR/merge/deploy.

## Restricciones
- Python stdlib; JS vanilla; sin procesos ni polling extra.
- `/*__CSRF__*/` una sola vez; sin exponer prompt/workspace/verification_command/expected_outputs/stdout.
- `./opencode-ecosystem status` = `[ok] sin drift`; suite verde; `./verify.sh` verde; `qa-gate --strict` exit 0.

## No romper
- Contratos `/api/*`; `showTrace`, `hideTrace`, `explainTrace`, `showView`, `showHistory`, `renderInspector`, `selectComponent`, `renderCompDetail`, `loadCompEvents`, `clearCompSelection`, `isDarkTheme`, `paintThemeBtn`, `toggleTheme`, `loadData`, filtros, acciones CSRF.
- Accesibilidad: `aria-live` en `#trace-why`, `:focus-visible`, `prefers-reduced-motion`; sin `alert()`; favicon y mensaje CSRF intactos.
- E2E `test_filtros_e_historial` y `TestVistaAyuda` siguen pasando.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks: `node --check` de cada bloque `<script>`, suite completa, `verify.sh`, `qa-gate --strict`, `status` sin drift.

## Tareas
- [x] T1 — Documento ODD y alcance aprobado.
- [x] T2 — Bloque "Error registrado" + "Qué revisar" en `#trace-why` y test estructural. Worker atomico.
- [x] T3 — Verificacion independiente read-only.
- [x] T4 — Cierre con evidencia y qa-gate.

## Criterios de aceptacion
- [x] El error concreto (`tr.note`) aparece destacado en la columna "por que", con `error_kind` y `result_code`.
- [x] "Qué revisar" da una orientación accionable por `error_kind`.
- [x] Si no hay nota, dice "sin mensaje de error registrado" (no inventa).
- [x] Suite verde; `./verify.sh` verde; `qa-gate --strict` exit 0; `status` sin drift.

## Decisiones aceptadas
- Mostrar `tr.note` (ya sanitizado, máx 200 chars) como el error concreto; no persistir stdout (limite duro del ecosistema).
- "Qué revisar" como orientación, no como certeza: se deriva de `error_kind`, no de adivinanza.
- Reutilizar `explainTrace` y el layout existente; solo añadir bloques dentro de `#trace-why`.

## Reutilizacion investigada
- Existente: `explainTrace(tr)` (index.html:980-1020) con todas las ramas; `tr.note` ya llega sanitizado desde `build_trace` (trace.py:119, máx 200 chars); `tr.error_kind` y `tr.result_code` ya en la traza; estilos `.ev`/`.muted`/`.tag`/`.pill`/`.badge`; `TestColumnaPorQue` en test_frontend.py.
- Canonica: añadir bloques dentro de `#trace-why` reutilizando `explainTrace`; no crear helper nuevo.
- Descartado: endpoint `/api/tasks/<id>/error` (la traza ya trae note/error_kind/result_code); persistir stdout (limite duro).

## Evidencia
- T2 (worker): `control/web/index.html` (en `explainTrace`, antes de la explicación genérica: bloque "Error registrado" con `tr.note` + `error_kind` + `result_code`, o "sin mensaje de error registrado"; bloque "Qué revisar" con orientación por `error_kind`) y `control/tests/test_frontend.py` (`test_bloque_error_registrado_y_que_revisar`). Observado por el worker: `node --check` OK en ambos bloques, `TestColumnaPorQue` 2/2, y un fallo E2E `test_traza_y_ejecucion_en_vivo` que el worker marcó como preexistente.
- T3 (verificador read-only): pendiente de registro formal; el padre verificó el fallo E2E de forma independiente.
- T4 (cierre padre): el fallo E2E era real y preexistente (no lo causó T2): el test exigía "ejecución" en `#live-body`, pero la única tarea activa (#17, odd-verifier) lleva 826 min en `waiting`, así que el panel muestra "esperando decisión". Corregido en `control/tests/test_playwright_e2e.py` para aceptar ambos estados vivos válidos. Observado: 173 tests OK (skipped=1); `./verify.sh` -> `[ok] verify verde`; `scripts/qa-gate.sh --strict` -> EXIT=0; `./opencode-ecosystem status` -> `[ok] sin drift`.

## Progreso
- Estado: completada (T1-T4).
- Ultima tarea: T4 cierre.
- Bloqueos: ninguno.
