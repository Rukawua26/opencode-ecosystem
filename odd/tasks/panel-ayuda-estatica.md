# panel-ayuda-estatica

Fecha inicio: 2026-09-27
Estado: completada

## Objetivo
Una vista ❓ Ayuda en el panel que explique cada elemento: que es, para que sirve, como funciona y que limites tiene. Referencia consultable cuando se olvida un detalle.

## Problema y por que
El panel tiene muchas piezas (3 vistas, ~7 secciones, estados de tarea, badges, reconciliador, leases, CSRF) y ninguna explicacion dentro de la interfaz. Quien lo usa forgets what `waiting` means, what the reconciler touches, or what the panel deliberately does NOT do. La ayuda vive dispersa entre `control/README.md` y los documentos ODD, neither of which is visible from the panel.

Decision humana (2026-09-27): ayuda estatica, no chatbot. Motivo: sin coste de tokens, instantanea, no depende de red ni cuota, y no puede inventar. Un chat con modelo queda como etapa posterior opcional, anclado a este glosario.

## Alcance
### Incluye
- Nueva vista ❓ Ayuda en la pestana de vistas (`showView`/`VIEWS` y `data-view`), de solo lectura.
- Glosario en `control/web/index.html` con los 3 bloques: (1) que es y para que sirve cada seccion (Resumen, Mapa, Actividad, Ayuda); (2) estados de tarea (`pending`/`running`/`waiting`/`done`/`failed`/`dead`/`cancelled`) y que hace el lanzador con cada uno; (3) limites y garantias (no relanza, no expone prompts, CSRF, 127.0.0.1, retencion SQLite).
- Referencias a comandos CLI equivalents (`control.cli doctor`, `task add/run`, `receipt`, `reconcile`) para lo que solo se puede hacer por terminal.
- Enlace a `control/README.md` y a `odd/tasks/` como fuente completa.
- `title` (tooltip) en los controles principales que hoy no lo tienen, para ayuda en contexto sin salir de la vista.
- `control/tests/test_frontend.py`: test estructural de la vista de ayuda y sus bloques.

### Excluye
- Chatbot, LLM, endpoint de preguntas, SSE/WebSockets, React, dependencias.
- Cambios en `server.py`, `graph.py`, `collect.py`, `db.py`, `runner.py`, `reconcile.py`, `model.py`, esquema SQLite.
- Reordenar o renombrar secciones/vistas existentes; el panel sigue siendo read-only con las mismas acciones.
- Trabajo movil, ramas, commits, push, PR, merge, deploy.

## Restricciones
- Python stdlib; JS vanilla sin dependencias; sin procesos ni polling extra (i5-1235U/8GB).
- `/*__CSRF__*/` sigue una sola vez en el script del body.
- `./opencode-ecosystem status` = `[ok] sin drift`; `python3 -m unittest discover -s control/tests` verde; `./verify.sh` verde; `scripts/qa-gate.sh --strict` exit 0.

## No romper
- Contratos `/api/*`; `showView`, `VIEWS`, `viewFromLocation`, `data-view`, `showHistory`, `renderInspector`, `selectComponent`, `renderCompDetail`, `loadCompEvents`, `clearCompSelection`, `isDarkTheme`, `paintThemeBtn`, `toggleTheme`, `loadData`.
- La vista por defecto sigue siendo `resumen`; el hash y `localStorage.panel-view` siguen funcionando con la nueva vista incluida.
- Accesibilidad: `role=tab`/`aria-selected` en la nueva pestana, `role=button`, teclado, `aria-live`, `:focus-visible`, `prefers-reduced-motion`.
- Sin `alert()`; sin exponer prompt, workspace, verification_command, expected_outputs ni stdout.
- El E2E `test_filtros_e_historial` sigue pasando.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks obligatorios: `node --check` de cada bloque `<script>` (via test), suite completa, `verify.sh`, `qa-gate --strict`, `status` sin drift.

## Tareas
- [x] T1 — Documento ODD y alcance aprobado (decisión humana: ayuda estática).
- [x] T2 — Vista ❓ Ayuda + glosario + tooltips en `control/web/index.html` y test estructural en `control/tests/test_frontend.py`. Worker atomico.
- [x] T3 — Verificacion independiente read-only. Fidelidad al codigo confirmada; 6 hallazgos menores, 3 corregidos en T4.
- [x] T4 — Cierre con evidencia y qa-gate.

## Criterios de aceptacion
- [x] La pestana ❓ Ayuda aparece junto a las otras 3 y abre/cierra con el mismo mecanismo (`showView`).
- [x] Explica las 4 vistas, las secciones principales, los 7 estados de tarea, y los limites/garantias del panel.
- [x] Incluye los comandos CLI para lo que no se puede hacer desde el panel.
- [x] Los controles principales sin `title` lo reciben.
- [x] Suite verde; `./verify.sh` verde; `qa-gate --strict` exit 0; `status` sin drift.

## Decisiones aceptadas
- Ayuda estatica, no chatbot (humano, 2026-09-27): sin coste, sin red, no inventa.
- Glosario en el HTML, no en un endpoint ni en Markdown servido: una sola fuente que el panel lee sin red y sin backend nuevo.
- Contenido derivado de lo que el codigo ya hace (`runner.py`, `reconcile.py`, `server.py`, `db.py`, `README.md`), no de suposiciones.

## Reutilizacion investigada
- Existente: pestanas de vistas (`showView`, `VIEWS`, `tab-<name>`, `data-view` en cada seccion, `viewFromLocation` con hash + `localStorage`); estilos `.panel`, `.hint`, `.tag`, `.pill`, `.btn`; tabla y `.table-wrap` para estados; `.muted`/`.mono`; comandos CLI documentados en `control/README.md`; estados y limites reales en `control/runner.py` (MAX_ATTEMPTS, lease, timeouts), `control/reconcile.py` (solo marca dead, cooldown, no relanza), `control/server.py` (CSRF, 127.0.0.1, rutas 405), `control/db.py` (retencion 30d/20k); tests estructurales de marcas en `control/tests/test_frontend.py`.
- Canonica: reutilizar el mecanismo de vistas y los estilos existentes; la ayuda es una `section.panel` mas con `data-view="ayuda"`.
- Descartado: endpoint `/api/help` (el glosario es estatico, no necesita backend); Markdown aparte (doble fuente que se desincroniza); chatbot (coste, red, inventa).

## Evidencia
- T2 (worker): `control/web/index.html` (`'ayuda'` en `VIEWS`, `tab-ayuda` con `type/id/role/aria-selected/onclick/title`, `section.panel[data-view="ayuda"]` con 8 bloques `h3` y 4 tablas usando `.hint`/`.table-wrap`/`table`/`.mono`/`.tag`/`.pill`; `title` en 18 controles que estaban sin él, ninguno de los que ya lo tenian) y `control/tests/test_frontend.py` (helpers `panel_view()`/`declared_views()` + `TestVistaAyuda` con 9 tests estructurales por marcas). Observado por el worker: 169 tests OK (1 skip opt-in `OPENCODE_E2E=1`), `node --check` rc 0 en ambos `<script>`, `/*__CSRF__*/` = 1, E2E Playwright 7/7 (incl. `test_filtros_e_historial`; ayuda visible al pulsar, `aria-selected=true`, hash y `localStorage` correctos, 0 errores de consola, sin HTTP >=400, sin overflow a 1280px y 390px, en claro y oscuro), `verify.sh` verde, `qa-gate --strict` exit 0, `status` sin drift.
- T3 (verificador read-only): `showView`/`viewFromLocation` genericas (sin cambios), default `resumen` intacto, 0 lineas eliminadas con `title=`, backend con 0 lineas modificadas, sin `alert(` ni exposicion de datos sensibles, tests no fragiles (substrings/regex, sin parrafos exactos). **Punto critico confirmado**: la seccion es fiel al codigo — `failed` nunca se escribe (solo `queue_summary`/`TASK_BADGE`/filtro), `cancelled` solo existe como filtro de UI y `do_cancel` marca `dead` + «cancelada manualmente»; lease = timeout+2min, orphan = timeout+5min, cooldown 120s, `MAX_ATTEMPTS=2`, `TIMEOUT_S=900`, retencion 30d/20k, CSRF por token+Origin, free-allowed y nunca sensitive: todo cuadra con `runner.py`, `db.py`, `reconcile.py`, `server.py`, `actions.py`, `graph.py`. Observado: 169 tests OK (1 skip), `test_frontend` 19/19, E2E verde, `node --check` OK.
- T4 (cierre padre): corregidos 3 de los 6 hallazgos menores del verificador — (a) «11 nodos por capa» -> «11 nodos agrupados en 6 capas»; (b) intervalo de refresco separado: estado 30s fijo vs poll adaptativo de tareas (5s/60s); (c) `cancelled` reexpresado como comportamiento («el lanzador nunca escribe este estado») en vez de afirmacion sobre el esquema. No corregidos por no afectar al panel: (d) `20k` unificado a `20 000` en ambos bloques; (e) tablist sin roving tabindex (preexistente en las 3 pestanas originales, la nueva no introduce regresion); (f) el working tree mezcla tres features sin commitear, riesgo de atribucion en un commit atomico futuro, no defecto de T2. Observado: 169 tests OK (skipped=1); `./verify.sh` -> `[ok] verify verde`; `scripts/qa-gate.sh --strict` -> EXIT=0; `./opencode-ecosystem status` -> `[ok] sin drift`.

## Progreso
- Estado: completada (T1-T4).
- Ultima tarea: T4 cierre.
- Bloqueos: ninguno. Deuda declarada: tablist sin roving tabindex (preexistente). Etapa posterior opcional: chat con modelo anclado a este glosario (no aprobada).
