# panel-tema-oscuro

Fecha inicio: 2026-09-27
Estado: completada

## Objetivo
Anadir un interruptor explicito de tema (claro/oscuro) en la cabecera del panel, con preferencia persistente, sin perder el comportamiento actual por `prefers-color-scheme`.

## Problema y por que
El panel solo sigue el tema del sistema (`@media (prefers-color-scheme: light)`). Si el sistema esta en claro, no hay forma de forzar oscuro sin tocar el SO, y si esta en oscuro no hay forma de ver el claro. El usuario pide "modo oscuro" explicito. Ademas, en tema claro hay dos senales casi invisibles por usar blanco translucido: `.tag` (blanco 12%) y `.trow:hover` (blanco 8%), que al activar el tema claro se leerian como bug.

## Alcance
### Incluye
- `control/web/index.html`: variables de tema en `:root` (oscuro) y `:root[data-theme="light"]` + regla de sistema `:root:not([data-theme="dark"])`; boton interruptor en la cabecera; script minimo en `<head>` que aplica la preferencia antes de pintar (evita destello); persistencia en `localStorage` con la clave ya usada por el panel (`panel-view` -> `panel-theme`).
- Contraste minimo en tema claro: `--tagbg` y `--hover` como variables, para que etiquetas y hover de filas se vean.
- `control/tests/test_frontend.py`: `test_inline_script_parses` pasa a validar **todos** los bloques `<script>` (hoy valida el primero; con el script de `<head>` dejaria de cubrir el principal) y nuevo test estructural del interruptor.

### Excluye
- Trabajo movil, React, dependencias, nuevas vistas o endpoints.
- Cambios en `server.py`, `graph.py`, `collect.py`, `db.py`, `runner.py`, `reconcile.py`, esquema SQLite, memoria viva, receipts, backups, logs.
- Selector de 3 estados (auto/claro/oscuro): el valor inicial ya sigue al sistema; el interruptor solo alterna y persiste. YAGNI.
- Ramas, commits, push, PR, merge, deploy.

## Restricciones
- Python stdlib; JS vanilla sin dependencias; sin procesos ni polling extra (i5-1235U/8GB).
- El marcador `/*__CSRF__*/` debe seguir siendo sustituido por el servidor (esta en el script del body: no duplicarlo ni moverlo).
- `./opencode-ecosystem status` = `[ok] sin drift`; `python3 -m unittest discover -s control/tests` verde; `./verify.sh` verde; `scripts/qa-gate.sh --strict` exit 0.

## No romper
- Contratos `/api/*`; `showHistory`, `renderInspector`, `selectComponent`, `renderCompDetail`, `loadCompEvents`, `clearCompSelection`, `loadData`, `showView`.
- Accesibilidad: `role=button`, teclado, `aria-live`, `:focus-visible`, `prefers-reduced-motion`, y el boton nuevo con `aria-label` + `title` explicito.
- Sin `alert()`; sin exponer prompt, workspace, verification_command, expected_outputs ni stdout.
- El E2E `test_filtros_e_historial` sigue pasando.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks obligatorios: `node --check` de cada bloque `<script>` (via test), suite completa, `verify.sh`, `qa-gate --strict`, `status` sin drift.

## Tareas
- [x] T1 — Documento ODD y alcance aprobado.
- [x] T2 — Implementar interruptor de tema + contraste minimo + tests en `control/web/index.html` y `control/tests/test_frontend.py`. Worker atomico; corrigio en ruta que `test_sin_alert_nativo` quedara tapado por el script nuevo de `<head>`.
- [x] T3 — Verificacion independiente read-only. Sin hallazgos bloqueantes; 2 nits no bloqueantes (ver Evidencia).
- [x] T4 — Cierre con evidencia y qa-gate.

## Criterios de aceptacion
- [x] Boton en la cabecera alterna claro/oscuro, con icono, `title` y `aria-label` coherentes con la accion siguiente.
- [x] La preferencia persiste entre recargas; sin preferencia guardada se sigue al sistema.
- [x] Sin destello visible al cargar (atributo aplicado antes de pintar).
- [x] En tema claro se ven las etiquetas y el hover de filas.
- [x] `test_inline_script_parses` sigue cubriendo el script principal; suite verde; `verify.sh` verde; `qa-gate --strict` exit 0.

## Decisiones aceptadas
- Dos estados (claro/oscuro) con default del sistema, no selector de 3: menos codigo y cubre el caso pedido.
- Aplicacion antes de pintar via script en `<head>`: evita destello; compensa actualizando el test para validar todos los bloques `<script>`.
- Contraste claro con dos variables (`--tagbg`, `--hover`) en vez de editar cada uso: 3 lineas similares, sin abstraccion extra.

## Reutilizacion investigada
- Existente: bloque `:root` con variables (index.html:9-15) y override claro en `@media (prefers-color-scheme: light)` (:16-21); `.tag` (:74); `.trow:hover,.trow:focus-visible{background:#ffffff08}` (:128); boton `.btn` y `top-right` en cabecera (:35-37, :146-149); `localStorage` para `panel-view` en `showView`/`viewFromLocation`; marcador `/*__CSRF__*/` al inicio del script del body; `test_inline_script_parses` (test_frontend.py:15-26) y tests estructurales de marcas.
- Canonica: mismo patron de persistencia y de test estructural por marcas; no crear helper de tema nuevo mas alla de lo necesario.
- Descartado: CSS-only con `prefers-color-scheme` (ya existe, no es controlable); 3 estados; librería de toggles.

## Evidencia
- T2 (worker): `control/web/index.html` (variables `--tagbg`/`--hover` en los 3 bloques de tema; `.tag` y `.trow:hover` las usan; override claro duplicado en `:root[data-theme="light"]` y `:root:not([data-theme="dark"])` con las mismas 9 vars; `<script>` propio en `<head>` sin defer que aplica `panel-theme` antes de pintar en try/catch; `#theme-toggle` en `.top-right` con `isDarkTheme`/`paintThemeBtn`/`toggleTheme`; `/*__CSRF__*/` 1 vez) y `control/tests/test_frontend.py` (`inline_scripts()`, `test_inline_script_parses` valida los 2 bloques, `test_sin_alert_nativo` corregido, `test_interruptor_de_tema` nuevo). Observado por el worker: 160 tests OK (1 skip opt-in `OPENCODE_E2E=1`), `node --check` rc=0 en ambos bloques con comprobacion negativa del head, logica de tema ejecutada en node con stub de DOM, contraste claro medido (tag 4.75:1, hover visible), E2E Playwright 7/7.
- T3 (verificador read-only): los 9 puntos del contrato cumplidos (`:root` oscuro con 0 vars perdidas, overrides identicos 9/9, `--tagbg`/`--hover` sin blancos hardcodeados, script head sincrono en parseo, boton nativo accesible, `/*__CSRF__*/` exactamente 1, un solo listener `DOMContentLoaded`, 8 funciones de contrato definidas una vez, sin `alert()` ni secretos). Confirma que `split("<script>")` no queda en ningun test. Observado: 160 tests OK (1 skip), E2E 7/7, `node --check` rc=0 en ambos bloques. Nits no bloqueantes: (1) etiqueta estatica del boton incoherente con el icono inicial si el SO arranca en oscuro; (2) sin listener `change` de `matchMedia` si el SO cambia de tema en caliente. Nota de atribucion: el working tree mezcla esta feature con `panel-detalle-unificado` y un cambio ajeno en `AGENTS.md`.
- T4 (cierre padre): nit (1) corregido por el padre — etiqueta estatica neutra (`🌓` / "cambiar de tema") y marcador de `test_interruptor_de_tema` actualizado en consecuencia. Nit (2) **no corregido**: queda declarado, no es requisito (el CSS si sigue al SO; solo el icono/label no se repinta). Observado: 160 tests OK (skipped=1); `./verify.sh` -> `[ok] verify verde`; `scripts/qa-gate.sh --strict` -> EXIT=0; `./opencode-ecosystem status` -> `[ok] sin drift`.

## Progreso
- Estado: completada (T1-T4).
- Ultima tarea: T4 cierre.
- Bloqueos: ninguno. Deuda declarada: repintar `#theme-toggle` si el SO cambia de tema en caliente (sin listener `change` en `matchMedia`).
