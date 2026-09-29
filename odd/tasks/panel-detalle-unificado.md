# panel-detalle-unificado

Fecha inicio: 2026-09-27
Estado: completada

## Objetivo
Al hacer clic en una tarjeta de Componentes (Resumen/Actividad) o en un nodo del Mapa, abrir un detalle consistente y mas completo sin perder el contexto de la vista actual.

## Problema y por que
El detalle esta repartido: las tarjetas abren solo el modal de historial (`showHistory`), y el Mapa tiene inspector lateral (`renderInspector`) con evidencia/capa/fuente/conexiones/eventos. El usuario pide que al clicar una funcion se vea mas detalle. Unificar evita duplicar UI y reutiliza datos ya disponibles en snapshot/graph/events.

## Alcance
### Incluye
- Reutilizar el inspector lateral del Mapa como panel de detalle compartido para tarjetas y nodos.
- Tarjetas de Componentes seleccionables (raton + teclado Enter/Espacio) que muestran: estado, descripcion, path, source, evidencia si existe, y eventos recientes via `/api/events?kind=` existente.
- Mantener el modal de historial (`showHistory`) como vista ampliada, sin duplicar datos.
- Sin nuevos endpoints ni cambios de backend: solo `control/web/index.html` (+ ajustes minimos de tests en `control/tests/test_frontend.py` si hacen falta marcadores).
- Accesibilidad: foco visible, Escape cierra/deselecciona, `aria-live` en detalle.

### Excluye
- Nuevos endpoints, cambios en `server.py`, `graph.py`, `collect.py`, `db.py`, `runner.py`, `reconcile.py`.
- Migracion SQLite, nuevos servicios, polling extra, SSE/WebSockets, React/deps externas.
- Auto-reintentos, acciones nuevas, cambios de contratos publicos.
- Tocar memoria viva, receipts, backups, logs.

## Restricciones
- Python stdlib solamente; frontend vanilla JS sin dependencias (patron existente).
- i5-1235U/8GB: sin procesos permanentes ni polling agresivo; reutilizar polling actual.
- `./opencode-ecosystem status` debe terminar en `[ok] sin drift` (salvo el diff intencionado del panel).
- `python3 -m unittest discover -s control/tests`, `./verify.sh` verde, `scripts/qa-gate.sh --strict` exit 0.
- No commitear, pushear, mergear ni crear PR sin peticion explicita.

## No romper
- Contratos `/api/snapshot`, `/api/graph`, `/api/events`, `/api/tasks`, `/api/reconcile` intactos.
- `showHistory`, `renderInspector`, `selectNode`, `renderGraph`, filtros de mapa/cola, traza en vivo y acciones CSRF siguen funcionando.
- Tests existentes en `control/tests/` siguen pasando.
- Accesibilidad existente: `role=button`, teclado, `aria-live`, `:focus-visible`, `prefers-reduced-motion`.
- Sin `alert()` nativo; mensaje CSRF con "Recarga la pagina" intacto; favicon `data:,` intacto.
- Sin exponer prompt, workspace, verification_command, expected_outputs ni stdout.

## TDD
- Modo: off
- Fuente: default (sin politica explicita; los tests existentes no activan TDD)
- Runner: `python3 -m unittest discover -s control/tests`
- Checks funcionales obligatorios: `node --check` del script inline via `test_frontend.py`, servidor local `http://127.0.0.1:8765/` sin errores de consola en smoke existente.

## Tareas
- [x] T1 — Documento ODD y alcance aprobado.
- [x] T2 — Implementar detalle unificado en `control/web/index.html` (tarjetas seleccionables + inspector compartido + eventos recientes, manteniendo modal). Worker atomico. Ver Evidencia.
- [x] T2b — Ajuste minimo autorizado por el humano (2026-09-27): actualizar `test_filtros_e_historial` en `control/tests/test_playwright_e2e.py` para el flujo nuevo (clic en tarjeta aserta `#comp-detail` visible, luego "ver historial" abre el modal). Sin cambiar produccion mas alla de T2.
- [x] T3 — Verificacion independiente read-only (contraste en contexto fresco, tests + verificacion funcional).
- [x] T4 — Cierre con evidencia y qa-gate.
- [ ] T3 — Verificacion independiente read-only (contraste en contexto fresco, tests + verificacion funcional).
- [ ] T4 — Cierre con evidencia y qa-gate.

## Criterios de aceptacion
- [x] Clic/Enter en tarjeta muestra detalle con nombre, tipo, descripcion, path/source y eventos recientes; no navega fuera de la vista.
- [x] Clic/Enter en nodo del Mapa sigue mostrando inspector con evidencia, capa, fuente, conexiones y eventos.
- [x] Escape cierra modal y luego deselecciona; el foco vuelve al disparador del modal.
- [x] Sin nuevos endpoints; sin secretos en el HTML/JS; `node --check` pasa.
- [x] `python3 -m unittest discover -s control/tests` verde; `./verify.sh` verde; `scripts/qa-gate.sh --strict` exit 0.

## Decisiones aceptadas
- Reutilizar el inspector lateral existente en vez de crear un drawer/modal nuevo (YAGNI, menos RAM/tokens).
- No crear endpoint de detalle: `/api/snapshot` + `/api/graph` + `/api/events?kind=` ya cubren lo necesario.
- Si una tarjeta no tiene eventos, mostrar "sin eventos" en vez de ocultar el panel.
- Humano 2026-09-27: ante el conflicto E2E, se actualiza el test (flujo detalle -> "ver historial" -> modal) en vez de abrir el modal directo al clicar.

## Reutilizacion investigada
- Codigo existente encontrado: `renderInspector` + `selectNode` + `loadNodeEvents` (`control/web/index.html:510-612`), modal `showHistory`/`closeHist` con `histTrigger` (`:840-878`), tarjetas `.comp` con `onclick showHistory` (`:423-433`), nodos `.gnode` con click/teclado (`:551-569`), `/api/events?kind=&limit=` en `control/server.py:144-157`, `node_event_kinds` en `control/graph.py:40-48`, smoke `control/tests/test_frontend.py`.
- Implementacion canonica: inspector lateral + `loadNodeEvents(kind)` + modal de historial; las tarjetas reutilizan ese patron en vez de duplicarlo.
- Decision: reutilizar; no crear helper/formato/modulo nuevo salvo que el worker demuestre que no existe equivalente.
- Alternativas descartadas: drawer nuevo solo para tarjetas (duplica inspector); endpoint `/api/components/<name>` (innecesario, snapshot ya trae componentes); SSE/WebSockets (coste, polling actual suficiente).

## Evidencia
- T2 (worker): solo `control/web/index.html` (tarjetas `.comp` con `selectComponent`, `aria-pressed`, clase `.sel`; nuevo aside `#comp-detail` con nombre/tipo/descripcion/path/source/etiquetas, eventos recientes via `/api/events?kind=`, "sin eventos" si vacio, boton "ver historial" hacia `showHistory`; inspector del Mapa intacto; Escape extiende a deseleccion con `clearCompSelection`; sin `alert()`, sin secretos). `test_frontend.py` 9/9 OK, `node --check` OK; suite completa con 1 fallo esperado en `test_filtros_e_historial` (punto de bloqueo, resuelto en T2b).
- T2b (worker): `control/tests/test_playwright_e2e.py` actualizado al flujo nuevo (tarjeta -> `#comp-detail` visible + modal oculto; "ver historial" -> `#hist-modal`; Escape cierra). Suite: 159 tests OK (1 skipped: E2E Playwright requiere panel vivo en 127.0.0.1:8765).
- T3 (verifier read-only): diff en `control/web/index.html` y `control/tests/test_playwright_e2e.py`; backend intacto (sin diff en server/graph/collect/db/runner/reconcile, sin migracion); funciones preservadas (`showHistory`, `renderInspector`, `selectNode`); marcadores `test_frontend.py` intactos; suite 159 tests OK (skipped=1) en 14.1s; `node --check` OK (node v24.15.0). Nota: `AGENTS.md` trae 1 linea previa (ruta `qa-gate.sh` -> `scripts/qa-gate.sh`), ajena a T2 e inocua.
- T4 (cierre padre): `python3 -m unittest discover -s control/tests` -> 159 tests OK (skipped=1); `./verify.sh` -> `[ok] verify verde`; `scripts/qa-gate.sh --strict` -> EXIT=0; `./opencode-ecosystem status` -> `[ok] sin drift`.

## Progreso
- Estado: completada (T1-T4); documento en `odd/tasks/panel-detalle-unificado.md`.
- Ultima tarea: T4 cierre.
- Bloqueos: ninguno.
