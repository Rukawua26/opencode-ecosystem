# panel-traza-porque

Fecha inicio: 2026-09-27
Estado: completada

## Objetivo
Que la traza de tarea explique el POR QUE de su resultado (`done`/`waiting`/`dead`/...) y que la Ayuda documente cada opcion de cada desplegable con ejemplos de uso.

## Problema y por que
(1) Al clicar una fila se despliega la traza (fase, estado, timeline), pero no explica por que la tarea acabó así: hay que inferirlo del `error_kind` crudo ("contract") y del timeline. (2) Los desplegables (agente, modelo, sensibilidad, filtros de cola y de mapa) tienen tooltip pero sus OPCIONES no estan documentadas ni con ejemplo de cuándo usarlas. El usuario pide ambas cosas. La salida completa del agente NO se persiste (limite duro), asi que la explicacion se deduce de datos ya registrados (estado, fase, error_kind, rc, nota, timeline, verifier), nunca del razonamiento interno del agente ni de un chatbot.

## Alcance
### Incluye
- `control/web/index.html`: panel de traza en dos columnas cuando hay espacio (traza a la izquierda, "¿Por qué tiene este resultado?" a la derecha); la tabla de tareas NO se estrecha (el panel sigue debajo, patron `.map-layout` ya existente); en pantallas estrechas se apila.
- Explicacion del resultado en JS frontend con los campos que YA devuelve `/api/tasks/<id>/trace` (status, phase, error_kind, result_code, note, attempts, timeline, verifier, stop_reason): textos humanos por combinacion (contract→"sin RESULT/SUMMARY coherente, el runner la rechazo y tras 2 intentos quedo dead"; review→"la verificacion pide decision humana, no se reintenta automaticamente"; provider→"fallo del proveedor, vuelve a pending sin quemar intento"; timeout; blocked/transicion→"necesita tu decision o una operacion del control-plane"; done→"termino rc=0 con contrato valido" + verificador encadenado si existe + intentos usados; pending/running→"en cola / en ejecucion"). Sin datos suficientes → "no hay informacion suficiente en el registro" (nunca inventar).
- Ayuda: seccion nueva "Desplegables y sus opciones" con 3 sub-bloques (Encolar tarea: agente/modelo/sensibilidad; Filtros de cola: estado/agente/modelo/sensibilidad; Mapa: capa/estado/fuente), tabla `Opcion | Que significa | Ejemplo de uso` por cada opcion; los 7 estados de tarea ya explicados se ENLAZAN, no se duplican; `todos los agentes/modelos` documentados como "se rellena con los valores de la cola".
- Enlace contextual ❓ junto a "filtros:" y al formulario de encolado que abre `showView('ayuda')`.
- `control/tests/test_frontend.py`: test anti-drift (cada valor de la lista JS de agentes y cada `<option>` estatica debe aparecer en la seccion de ayuda) + test estructural de la columna "por que".
- Ajuste minimo de `test_playwright_e2e.py` solo si el cambio lo exige.

### Excluye
- Chatbot, LLM, endpoint nuevo, cambios en `server.py`, `trace.py`, `graph.py`, `collect.py`, `db.py`, `runner.py`, `reconcile.py`, esquema SQLite.
- Persistir stdout/respuestas del agente; migracion; polling extra; dependencias; React/SSE; trabajo movil.
- Reordenar secciones/vistas; ramas, commits, push, PR, merge, deploy.

## Restricciones
- Python stdlib; JS vanilla sin dependencias; sin procesos ni polling extra (i5-1235U/8GB).
- `/*__CSRF__*/` una sola vez en el script del body; sin exponer prompt/workspace/verification_command/expected_outputs/stdout.
- `./opencode-ecosystem status` = `[ok] sin drift`; `python3 -m unittest discover -s control/tests` verde; `./verify.sh` verde; `scripts/qa-gate.sh --strict` exit 0.

## No romper
- Contratos `/api/*`; `showView`, `showHistory`, `renderInspector`, `selectComponent`, `renderCompDetail`, `loadCompEvents`, `clearCompSelection`, `showTrace`, `hideTrace`, `isDarkTheme`, `paintThemeBtn`, `toggleTheme`, `loadData`, filtros, acciones CSRF.
- Accesibilidad: `role=button`/tab, teclado, `aria-live`, `:focus-visible`, `prefers-reduced-motion`; la columna nueva con encabezado accesible.
- Sin `alert()`; favicon y mensaje CSRF intactos; E2E `test_filtros_e_historial` y `TestVistaAyuda` siguen pasando.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks obligatorios: `node --check` de cada bloque `<script>`, suite completa, `verify.sh`, `qa-gate --strict`, `status` sin drift.

## Tareas
- [x] T1 — Documento ODD y alcance aprobado.
- [x] T2 — Columna "por que" en la traza + seccion de desplegables en Ayuda + test anti-drift en `control/web/index.html` y `control/tests/test_frontend.py`. Worker atomico (dos intentos de delegacion abortados a mitad; el trabajo persistio en el arbol y un tercer worker lo completo con el boton ❓ junto a "filtros:" del mapa).
- [x] T3 — Verificacion independiente read-only.
- [x] T4 — Cierre con evidencia y qa-gate.

## Criterios de aceptacion
- [x] La traza despliega traza + "¿Por qué tiene este resultado?" lado a lado (apilado en estrecho); la tabla no se estrecha.
- [x] La explicacion cubre dead (contract/timeout/reconciliador/generico), waiting (review/blocked/transicion), done (rc=0 + verificador + intentos), pending/running, y dice "no hay informacion suficiente" si no se puede saber.
- [x] Ayuda documenta cada opcion de agente/modelo/sensibilidad/filtros de cola/filtros de mapa con ejemplo; los 7 estados se enlazan sin duplicar.
- [x] Enlace ❓ contextual junto a filtros y formulario.
- [x] Test anti-drift: opcion sin documentar rompe la suite.
- [x] Suite verde; `./verify.sh` verde; `qa-gate --strict` exit 0; `status` sin drift.

## Decisiones aceptadas
- Explicacion en el frontend con datos ya existentes, no endpoint ni modelo (YAGNI, sin coste, no inventa).
- Dos columnas DENTRO del panel de traza, no al lado de la tabla (no estrecha la tabla; reutiliza patron `.map-layout`).
- La ayuda es la fuente de verdad de las opciones: test anti-drift la convierte en contrato.
- Los 7 estados ya documentados se enlazan; duplicarlos crearia doble fuente.

## Reutilizacion investigada
- Existente: `#trace-panel`/`#trace-body` con `showTrace(id)`/`hideTrace()` (index.html), `/api/tasks/<id>/trace` que ya devuelve `stop_reason` traducido, `error_kind`, `phase`, `attempts`, `timeline`, `verifier` (`control/trace.py:105-129`); patron de layout a dos columnas `.map-layout`/`.map-main` (index.html:117-122); seccion Ayuda con tablas y `TestVistaAyuda` por marcas (test_frontend.py); lista JS de agentes en `loadTasks` (index.html ~linea 985); `<option>` estaticas de new-model/new-sensitivity/f-status/f-sens/mf-status/mf-source; Escape ya cierra la traza.
- Canonica: reutilizar `stop_reason` + campos de la traza para el "por que"; reutilizar el patron de tablas de la Ayuda para las opciones; no crear helper/formato nuevo mas alla de lo necesario.
- Descartado: endpoint `/api/tasks/<id>/why` (la traza ya trae los campos); chatbot/LLM (coste, inventa); tooltips por `<option>` (soporte HTML inconsistente entre navegadores).

## Evidencia
- T2 (worker): `control/web/index.html` (#trace-panel con #trace-body + aside#trace-why en .map-layout, apilado bajo 900px; `explainTrace(tr)` con todas las ramas y fallback honesto; Ayuda con "Desplegables y sus opciones", 3 tablas Opcion|Que significa|Ejemplo, 9 agentes + 3 modelos + 2 sensibilidades + filtros de cola/mapa; 4 enlaces a `showView('ayuda')`: pestana, formulario, filtros de cola, filtros de mapa) y `control/tests/test_frontend.py` (`TestColumnaPorQue` + `TestAntiDriftAyuda`). Observado por el worker: 172 tests OK (1 skip), `node --check` OK en ambos bloques.
- T3 (verificador read-only): layout y ramas confirmados; backend intacto (diff vacio en trace/graph/collect/db/runner/reconcile/server); `/*__CSRF__*/` x1, `alert()` x0, sin secretos; tests estructurales; suite 172 tests OK (1 skip), `node --check` OK. Observacion no bloqueante: `AGENTS.md` y `test_playwright_e2e.py` traen cambios previos ajenos a T2, triviales y sin rotura.
- T4 (cierre padre): `python3 -m unittest discover -s control/tests` -> 172 tests OK (skipped=1); `./verify.sh` -> `[ok] verify verde`; `scripts/qa-gate.sh --strict` -> EXIT=0; `./opencode-ecosystem status` -> `[ok] sin drift`.

## Progreso
- Estado: completada (T1-T4).
- Ultima tarea: T4 cierre.
- Bloqueos: ninguno.
