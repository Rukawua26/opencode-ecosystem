# panel-detalle-escritorio

Fecha inicio: 2026-09-27
Estado: completada

## Objetivo
Pulir el detalle de componentes en escritorio: que se note que las tarjetas son clicables, que el detalle explique el estado con datos reales y que la seleccion sobreviva a los refrescos.

## Problema y por que
Tras la etapa anterior el detalle funciona, pero: (1) no hay hover ni pista clara de que la tarjeta es clicable (el hint dice "haz clic en un tipo para filtrar", que describe los chips, no las tarjetas); (2) el detalle no muestra "estado" y los eventos no distinguen carga/vacio/error (el catch muestra el mismo texto que "sin eventos"); (3) hay que confirmar que la seleccion sobrevive al polling de 30s. Todo solo-escritorio por decision del humano: sin prioridad movil.

## Alcance
### Incluye
- Affordance en `control/web/index.html`: hover en `.comp`, pista en el hint de Componentes (chips filtran, tarjetas muestran detalle), seleccion `.sel` ya existente.
- Detalle honesto en `#comp-detail`: solo datos reales del snapshot (nombre, tipo, descripcion, path, fuente, etiquetas) + ultimo estado derivado de eventos recientes si existe (si no hay, decir "sin estado", nunca inventar).
- Eventos con tres mensajes distintos: "cargando eventos…", "sin eventos recientes de este componente", "no se pudieron cargar los eventos".
- Confirmar/asegurar que `SEL_COMP` sobrevive a `renderComponents`/`loadData` mientras el componente siga presente (filtrado/busqueda que lo excluye -> mensaje neutro, sin errores).
- Ajuste minimo de tests en `control/tests/test_frontend.py` o `test_playwright_e2e.py` solo si el cambio lo exige.

### Excluye
- Version movil (decision explicita del humano).
- Nuevos endpoints; cambios en `server.py`, `graph.py`, `collect.py`, `db.py`, `runner.py`, `reconcile.py`.
- Migracion SQLite, nuevos servicios, polling extra, dependencias, React/SSE/WebSockets.
- Acciones nuevas, cambios de contratos, tocar memoria viva, receipts, backups, logs.

## Restricciones
- Python stdlib; frontend vanilla JS sin dependencias.
- i5-1235U/8GB: sin procesos ni polling extra.
- `./opencode-ecosystem status` = `[ok] sin drift` (salvo diff intencionado).
- `python3 -m unittest discover -s control/tests`, `./verify.sh` verde, `scripts/qa-gate.sh --strict` exit 0.
- Sin commit/push/PR/merge ni ramas nuevas sin peticion explicita.

## No romper
- Contratos `/api/*` intactos; `showHistory`, `renderInspector`, `selectNode`, `selectComponent`, filtros, traza en vivo y acciones CSRF intactos.
- Tests existentes siguen pasando; accesibilidad (role=button, teclado, aria-live, focus-visible, prefers-reduced-motion) intacta.
- Sin `alert()`; mensaje CSRF y favicon intactos; sin exponer prompt, workspace, verification_command, expected_outputs ni stdout.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks obligatorios: `node --check` del script inline via `test_frontend.py`.

## Tareas
- [x] T1 — Documento ODD y alcance aprobado.
- [x] T2 — Pulido escritorio en `control/web/index.html` (hover, hint, estado honesto, 3 textos de eventos, seleccion estable). Worker atomico; sin cambios de tests.
- [x] T3 — Verificacion independiente read-only.
- [x] T4 — Cierre con evidencia y qa-gate.

## Criterios de aceptacion
- [x] Las tarjetas muestran hover/seleccion y el hint explica: chips filtran, tarjetas detallan.
- [x] El detalle muestra solo datos reales + estado derivado de eventos o "sin estado"; nunca inventa estado.
- [x] Eventos distinguen carga, vacio y error con tres textos distintos.
- [x] La seleccion sobrevive al refresco de 30s mientras el componente exista; si el filtro lo excluye, mensaje neutro.
- [x] Suite verde; `./verify.sh` verde; `scripts/qa-gate.sh --strict` exit 0.

## Decisiones aceptadas
- Sin trabajo movil (panel local de escritorio).
- No inventar campo "estado" de componente: el snapshot no lo trae; derivar de eventos o declarar ausencia.
- Reutilizar estilos/patrones existentes (`.sel`, `statusBadge`, `pushError` si aplica) antes de crear nuevos.

## Reutilizacion investigada
- Existente: `.comp`/`.comp.sel` + `#comp-detail` (`index.html:58-69`), tarjetas con `selectComponent` y `aria-pressed` (`:430-444`), `renderCompDetail`/`loadCompEvents` con guardia `SEL_COMP` (`:466-497`), modal `showHistory` (`:905+`), `statusBadge`/`fmtTs`, `pushError`/banners, Escape con `clearCompSelection` (`:943`), marcadores `test_frontend.py`, flujo E2E actualizado en `test_playwright_e2e.py`.
- Canonica: reutilizar ese bloque; el worker solo anade hover, textos y estado derivado.
- Descartado: endpoint de estado por componente (el snapshot no lo trae; derivar de eventos basta); drawer nuevo (ya existe `#comp-detail`).

## Evidencia
- T2 (worker): solo `control/web/index.html` (hover `.comp:hover`, hint "los tipos filtran la lista; haz clic en una tarjeta para ver su detalle", fila `estado` derivada del ultimo evento con `statusBadge` o "sin estado"/"no se pudo determinar", tres textos de eventos, `LAST_COMP_LIST` + `SEL_COMP` estable sin reinicios en render/loadData). Suite 159 tests OK (1 skip); `node --check` OK.
- T3 (verifier read-only): hover, hint, estado honesto y 3 textos confirmados; sin `alert()` ni secretos; accesibilidad intacta; suite 159 tests OK (skipped=1); `node --check` OK. Nota menor: Escape tambien limpia `SEL_COMP` ademas de cerrar el modal, sin romper el E2E. `AGENTS.md` trae 1 linea previa ajena a la tarea.
- T4 (cierre padre): `python3 -m unittest discover -s control/tests` -> 159 tests OK (skipped=1); `./verify.sh` -> `[ok] verify verde`; `scripts/qa-gate.sh --strict` -> EXIT=0; `./opencode-ecosystem status` -> `[ok] sin drift`.

## Progreso
- Estado: completada (T1-T4); documento en `odd/tasks/panel-detalle-escritorio.md`.
- Ultima tarea: T4 cierre.
- Bloqueos: ninguno.
