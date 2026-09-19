# ecosystem-control

Fecha inicio: 2026-09-18
Estado: en_observacion

## Objetivo
Plano de control local del ecosistema OpenCode: inventario observable, estado de salud y panel web `localhost`, antes de cualquier orquestación automática.

## Problema
Skills, comandos, agentes, timers y scripts existen pero no hay una vista unificada y fiable que muestre qué existe, cómo se relaciona, qué corre, qué falló ni qué está sano. Video Emowe (17-sep-2026) aporta el concepto; `~/Descargas/NEXUS 0` está descartado (es vault Obsidian, no el mapa).

## Alcance
### Incluye
- Core en Python stdlib (sin dependencias externas): `control/`
- Fuentes de verdad: `skills/`, `commands/`, `configs/opencode.jsonc`+`dcp.jsonc`, `configs/cron-jobs.json`, `scripts/`, `memory/*.sh`, systemd user units.
- Salud OpenCode vía `opencode service status` (exit code + URL/pid). No se usa API HTTP interna por auth/cambios.
- Snapshot JSON canónico: `~/.local/share/opencode-control/snapshot.json`
- Servicio web `127.0.0.1:8765`, read-only, HTML estático embebido, polling cliente.
- Panel con secciones: resumen, actores/componentes, flujos (declarados), calendario/timers, salud.
- Datos marcados: Observado | Declarado | Inferido | Desconocido.

### Excluye
- Nada de React/FastAPI/deps externas.
- Sin SQLite ni historial (F2+).
- Sin cola de tareas ni lanzador (F3+).
- Sin reintentos automáticos ni acciones mutantes desde UI.
- Sin agentes 24x7 nuevos ni Telegram.

## Restricciones
- Sin drift al final: `./opencode-ecosystem status` = `[ok] sin drift`.
- `verify.sh` verde.
- `validate-skills.py` pasa (no se añaden skills en esta feature).
- Token/ramguard timers no se alteran.
- i5-1235U/8GB: polling ligero cada 30s, sin procesos extra pesados.

## TDD
- Modo: **off** (no hay runner de tests del proyecto; se valida por verificación funcional).
- Fuente: default (ninguna política explícita).
- Runner: `python3 -m unittest discover control/tests -v` si añadimos tests unitarios atomic; obligatorio: smoke funcional por CLI.

Checks funcionales obligatorios al cierre:
1. `python3 -m control.cli status` → exit 0 e imprime resumen.
2. `python3 -m control.main --once --pretty` genera snapshot `~/.local/share/opencode-control/snapshot.json` válido (parseable, contiene `skills` >= 10, `timers` >= 2, `opencode_service.active = true`).
3. Servidor: `python3 -m control.main --serve` en bg + `curl -fsS http://127.0.0.1:8765/api/health` → JSON con `ok=true`, components/skills>0, timers>0.
4. `curl -fsS http://127.0.0.1:8765/` devuelve HTML.
5. `./opencode-ecosystem status` → `[ok] sin drift` (sin cambios).

## Tareas
- [x] T1 — Alcance y documento único. `odd/tasks/ecosystem-control.md`
- [x] T2 — `control/model.py`: Snapshot{version,generated_at,counts,components,timers,flows,health,sources}; Component{kind,name,title,description,path,source,tags}; TimerInfo{name,active,next_run,last_run,result}; Flow{name,title,description,steps}; Health{ok,errors,warnings,open_code_active,timers_active,timers_total}; Enum Source{observado/declarado/inferido/desconocido}.
- [x] T3 — `control/collect.py`: escanea skills/, commands/, configs/opencode.jsonc (+ regex de subagentes), configs/dcp.jsonc, scripts/, memory/.systemctl --user list-timers --output=json con whitelist opencode-*; detalle por systemctl show. Salud: `opencode service status` (subprocess, timeout=5). Salida `Snapshot` y writer atómico+load.
- [x] T4 — `control/state.py`: StateStore con cache TTL=15s y persistencia atómica (tmp+replace) en SNAPSHOT_PATH; singleton global `get_store()`.
- [x] T5 — `control/server.py`: ThreadingHTTPServer; GET / (HTML), /api/health, /api/snapshot, /api/components, /api/timers, /static/ (con place-check traversal); POST/PUT/DELETE → 405; 404 para rutas desconocidas. Bind estricto 127.0.0.1:8765.
- [x] T6 — `control/web/index.html`: panel 3-pane (componentes/flujos/timers) + resumen + health arriba; polling cada 30s; badges por fuente; <2KB CCS+JS sin CDN.
- [x] T7 — CLI `python3 -m control` (main: --once/--serve) y `python3 -m control.cli` (status/snapshot) — ambos probados.
- [x] T8 — `control/__init__.py`, `control/__main__.py`, `control/README.md`. Sin pyproject (entrypoints vía `-m` suficientes y cumple YAGNI).
- [x] T9 — README en `control/README.md` (uso/campos/no-hace).
- [x] T10 — Checks finales: T10 actualiza evidencia aquí abajo.
- [x] T11 — Pulido visual del panel (peticion del humano tras ver captura): stat cards con iconos, chips de filtro por tipo, buscador, pasos de flujo como chips, badges por color de tipo, banner de salud. Sin deps externas.
- [x] T12 — Fase 1.1: corregir refresco `StateStore.current()` (ignoraba TTL); boton actualizar fuerza recoleccion (`?refresh=1`); indicador de antiguedad del dato. Evidencia: `stale: 0.0` tras 17s y `generated_at` nuevo (recoleccion real); tests TTL.
- [x] T13 — Fase 1.1: cruce `configs/cron-jobs.json` vs systemd en `crosscheck_timers()` (declarado-no-activo, activo-no-declarado, declarado-inactivo) -> health.warnings.
- [x] T14 — Fase 1.1: tests `control/tests/test_control.py` 11/11 OK (defaults Health, roundtrip snapshot, crosscheck 4 casos, TTL/force/fallo de recoleccion).
- [x] T15 — Fase 2: `control/db.py` SQLite WAL en `~/.local/share/opencode-control/control.db`. Tabla `events(id,ts,kind,category,event,status,detail,duration_s)`, indices, retencion 30d + tope 20k filas, detail truncado a 300 chars. Tests: record/read, receipt, truncation, filtro por kind, retencion.
- [x] T16 — Fase 2: `_diff_events(prev, snap)` en `state.py`: flips de servicio (cayó/recuperado), timers (parado/reanudado, resultado cambiado), componentes (añadido/eliminado). Registrado tras cada refresh exitoso; fallo de DB nunca rompe recoleccion. Tests: 7 casos incl. `refresh_records_events` con mock.
- [x] T17 — Fase 2: CLI `python3 -m control.cli receipt <componente> --status ok|fail|skipped --duration S --note "..."` (nota max 200). Probado: `recibo registrado: sdd-implement status=ok`, EXIT=0.
- [x] T18 — Fase 2: `GET /api/events?limit=N&kind=K` + seccion "Actividad reciente" en panel + modal de historial al clicar tarjeta. Probado: 2 recibos listados, filtro por kind devuelve 1, HTML contiene seccion, POST sigue 405.
- [x] T19 — Cierre F2: `python3 -m unittest discover -s control/tests` = 23/23 OK; `./opencode-ecosystem status` = sin drift; `./verify.sh` = verde. Errores corregidos en ruta: (a) `record_event` no llamaba `init_db` -> sqlite OperationalError "no such table", corregido llamando `init_db` en record; (b) `TimerInfo` slots sin `__dict__` en test -> `dataclasses.replace`; (c) `pkill -f` mataba el shell propio -> reinicio manual.
- [x] T20 — Bug frontend: pagina en "cargando..." por `SyntaxError` en el JS inline (comentario `/* */` dentro de template literal en el onclick de tarjetas). Detectado con `node --check` tras extraer el script. Corregido quitando el comentario del template. Regresion prevenida con nuevo test `test_frontend.py` que extrae el `<script>` y lo valida con `node --check` (skip si node ausente). Tests totales: 24/24 OK. Servidor sirviendo version corregida.

## Evidencia (checks ejecutados)

**T2-T6 (funcional):**
1. `python3 -m control --once` → `skills=10 comandos=6 agentes=2 timers=2/2 opencode_activo=True` (EXIT=0).
2. Snapshot JSON válido en `~/.local/share/opencode-control/snapshot.json`.
3. `--pretty` parseable: `health.ok=True`, `counts.skills=10`, `counts.comandos=6`, `counts.agentes=2`, `counts.timers=2`, `counts.flujos=3`.
4. `python3 -m control.cli status` → mismo resumen, EXIT=0.

**T5 (servidor):**
- Arranca en 127.0.0.1:8765; `GET /api/health` 200 retorna JSON con ok=true, counts, timers=2/2.
- `GET /api/timers` → opencode-ram-guard + opencode-kairos con `last_run` real.
- `GET /api/components` → lista 27 items con source=observado.
- `GET /` → HTML completo.
- `POST /api/snapshot` → 405.
- `GET /api/nada` → 404.
- `GET /healthz` → 000 después de `kill` del server (confirmo que se cerró).

**Checks globales (drift/regresión):**
- `./opencode-ecosystem status` → `[ok] sin drift` (múltiples veces).
- `./verify.sh` → `[ok] 10 skills valid` × 2 + `[ok] sin drift` + `[ok] verify verde`.
- Timers intactos: ram-guard y kairos activos tras los cambios.

**Correcciones aplicadas:**
- argparse: `--once`/`--serve` no son válidos en subparsers. Solución: `add_mutually_exclusive_group` con flags directos.
- systemd: `list-timers` en formato tabla es inestable. Solución: `--output=json` + filtro por whitelist `opencode-*`.
- Modelo: `health.ok` sin default rompía `load_snapshot()` (dataclass requiere defaults en orden). Solución: `ok: bool = False`.
- OpenCode: no usar `/api/info` HTTP (auth por pairing); usar `opencode service status` del CLI con timeout. Exit=0 → activo, exit≠0 → inactivo.

**T11 (pulido visual, 2026-09-18):** panel rediseñado: stat cards con iconos emoji, chips de filtro por tipo, buscador por texto, componentes como tarjetas con borde izquierdo coloreado por tipo, flujos con pasos en chips conectados por flechas, tabla de timers con pill activo/inactivo, banner de errores/advertencias, dark/light por `prefers-color-scheme`. Server sirviendo OK, `/api/health` verde tras verificación.

## Decisiones aceptadas
- Auth OpenCode local: **no** usar API HTTP interna (auth por pairing; inestable entre versiones). Se usa `opencode service status` (exit code + salida) y systemd como señales.
- Representación de flujos: Solo los **declarados** (SDD/ODD/patrones conocidos) se mapean como flujos; no se infieren automáticamente en F1.
- NEXUS 0: revisado y descartado, no forma parte del alcance.
- Copias de repo/datos sensibles: ninguna.

## Etapa 3 — Flujo piloto con lanzador (aprobada por el humano 2026-09-18)

Alcance aprobado: launcher 1 tarea/vez, sin recuperacion automatica, cola visible en panel, limites duros (timeout 15min, max 2 intentos, dead-letter), recibo automatico al terminar, verificador sdd-verify tras sdd-implement. Primera ejecucion con tarea inofensiva.

- [x] T21 — Tabla `tasks` (+ columna `model`, migracion automatica `ALTER TABLE` en `init_db` si falta). CRUD: `add_task`, `next_pending` FIFO, `update_task` (campos whitelist), `list_tasks`.
- [x] T22 — `control/runner.py`: `run_next()` FIFO exclusivo, `opencode run "<prompt>" --agent X [--model M]`, timeout 900s, exit->done; rc!=0 -> pending si intentos<2, dead si >=2. Sin guardar stdout del modelo (tokens/secretos). CLI `task add/list/run` con `--model`.
- [x] T23 — Cadena piloto en runner: `sdd-implement` ok -> encola `sdd-verify` con nota "encadenada de task #N". Cubierto en test.
- [x] T24 — `GET /api/tasks?limit=N` devuelve `{summary, tasks}`; panel con seccion "Cola de tareas" (pills por estado, resumen por conteo).
- [x] T25 — Tests runner: 10 casos mockeando `_run_agent` (FIFO, done, reintento->dead, timeout, encadenado verify, no almacenar stdout, summary). +2 tests de modelo/migracion. 37/37 OK.
- [x] T26 — Piloto real E2E: tarea #1 con modelo default fallo por "Insufficient Balance" (error del proveedor, no del runner) -> dead tras marcar nota; re-encolada con `opencode/nemotron-3-ultra-free` -> tarea #2 `done` rc=0 en 18.48s. Recibos automaticos en `/api/events`: iniciada/completada con duracion. Panel muestra cola correctamente.

## Progreso
- Última tarea terminada: T64 (Etapa 9A mapa operativo); T47 queda pendiente por calendario ~2026-09-25
- Estado: en observacion
- Bloqueos: ninguno
- Commits: 9381d5e (feature T1-T46), 8fd46fd (evidencia odd-contract), protegido en git 2026-09-18

## Etapa 9A — Mapa operativo visual (implementada 2026-09-19)

Origen: concepto tipo Archify adaptado al plano de control. SVG inline sin dependencias;
nodos agrupados (11) en lugar de los 21 componentes individuales (evita grafo spaghetti);
solo aristas declaradas/observadas; zoom avanzado fuera (viewBox responsive).

- [x] T60 — `control/graph.py`: build_graph(snap) -> {nodes, edges} con coordenadas fijas, estado por nodo, detalle sanitizado; cola defensiva (si queue_summary falla, el grafo no se rompe).
- [x] T61 — Endpoint `GET /api/graph` en server.py. Requirio reiniciar `opencode-control.service` (el servidor tiene el codigo en memoria; el HTML se lee por peticion pero el routing no).
- [x] T62 — Frontend: seccion "Mapa operativo" tras las stats; SVG con flechas (marker), leyenda en hint, continua=observado/discontinua=declarado, clic+Enter/Space -> detalle con conexiones y resaltado de aristas.
- [x] T63 — Tests: 8 de grafo (estructura, estados timers/opencode/cola/runner, cola caida, sanitizado) + 1 estructural frontend + 1 E2E Playwright (nodos, seleccion, detalle).
- [x] T64 — Verificacion: 104/104 OK, panel validado con captura real (seleccion Reconciliador resalta sus 3 aristas), movil sin overflow, 0 console errors, verify verde, sin drift.

Errores encontrados en la iteracion y corregidos: (a) queue_summary vive en runner.py, no db.py; (b) borre accidentalmente la firma de loadReconcile al insertar JS -> node --check lo cazo; (c) /api/graph 404 hasta reiniciar el servicio; (d) regla "dead>0 -> err" marcaba la cola en rojo siempre por tareas dead historicas T1: cambiada a warn (dead terminal != fallo activo).

## Etapa 8B — Pulido seguro del panel (aprobada e implementada 2026-09-19)

Origen: auditoria real con Playwright + Chromium del sistema sobre el panel vivo.

- [x] T54 — Footer corregido: "solo lectura" -> "acciones limitadas y protegidas" (el panel muta desde Etapa 4).
- [x] T55 — `favicon.ico` 404 eliminado con `<link rel="icon" href="data:,">` (0 bytes, sin archivo nuevo).
- [x] T56 — Modal accesible: `role=dialog`, `aria-modal`, `aria-labelledby`, cierre con Escape, foco devuelto al disparador.
- [x] T57 — Sin `alert()` nativo: errores de acciones y validacion via banner `pushError`; el formulario conserva lo escrito.
- [x] T58 — Smoke E2E opcional `test_playwright_e2e.py` (3 tests: carga+salud+sin errores/404, filtros+modal+Escape, movil 390px sin overflow). Skip automatico si falta playwright/chromium/panel.
- [x] T59 — Verificacion: 94/94 tests OK; Playwright real confirma footer nuevo, 0 console errors, 0 HTTP 404; `verify.sh` verde; `status` sin drift; qa-gate strict ok.

Decision: `comandos: 0` es correcto y observado — los antiguos comandos SDD fueron sustituidos por el flujo ODD; en `~/.config/opencode/commands/` solo quedan backups `.md.bak-*` que el glob `*.md` ignora correctamente. No se resucita nada.

Evidencia: console_errors=[], http_404=[], footer nuevo verificado en navegador headless (2026-09-19).

## Etapa 8A — Estabilidad y usabilidad (aprobada 2026-09-18, plan v2 iterado)

Contexto: plan de mejora iterado contra el codigo real. Correcciones al plan original:
duration se calcula de started_at/finished_at y duration_s ya existentes (sin backend nuevo);
verification_command NO se expone al navegador (ejecuta comandos locales arbitrarios);
diagnostico por CLI en vez de endpoint HTTP. Formulario avanzado generico descartado;
si se demuestra necesidad, Etapa 8B con perfiles predefinidos.

- [ ] T47 — Cerrar periodo de observacion (bloqueado por calendario, ~2026-09-25): servicio+reconciliador+3 timers, tests, verify.sh, drift, revision de actividad de la semana.
- [x] T48 — Documentacion coherente: README sin claims obsoletos (titulo Fase 1, "sin botones", "no lanza tareas" eliminados), doctor documentado, reconciliador con su propio encabezado, registro Etapa 8A aqui.
- [x] T49 — Errores visibles y CSRF recuperable: fetchJSON con HTTP status; pushError con banner (max 3, dedup) para snapshot/tareas/eventos; 403 -> "La sesion del panel expiro... Recarga la pagina" sin tocar el formulario; clearErrors al recuperar.
- [x] T50 — Cola sin backend nuevo: filtros f-status/f-agent/f-model/f-sens (locales, poblando opciones de la propia cola), columna Duracion (started_at/finished_at), duracion_s en actividad, badge parent_id "↳ de #N". Micro-fix: `--help` global y `task --help` verificados (exit 0).
- [x] T51 — Accesibilidad: chips como <button>, tarjetas con role=button+teclado, aria-labels en formularios, aria-live en errores, :focus-visible, .table-wrap para scroll horizontal, prefers-reduced-motion, stats a 2 col en movil.
- [x] T52 — `control.cli doctor [--json]`: salud, antiguedad, cola, reconciliador y ultimos errores sin prompt/workspace/comandos. Probado real: ok=True, timers 3/3, reconciliador ok. Tests: 4 casos con mocks (estructura, sanitizado, ok=False, --help).
- [x] T53 — Verificacion Etapa 8A: 84/84 tests OK (77 + 4 doctor + 3 estructurales frontend); servidor sirve el HTML nuevo sin reinicio (lee disco por peticion); `verify.sh` verde; `status` sin drift; panel vivo 3/3 timers.
  - Incidencia ajena encontrada y resuelta en ruta: `plugin_doctor` fallaba porque OpenCode se actualizo 2.0.5 -> 2.0.8 y el pin estaba viejo. Hooks auditados (config, event) presentes en el binario, sin hooks muertos ni experimentales -> `plugin_doctor.sh pin` re-pinea a v2.0.8. Fallo pre-existente, no causado por Etapa 8A (reproducido con cambios en stash).

No incluye: endpoint de descarga, verification_command en UI, migraciones DB, dependencias, voz, WebSockets, acceso remoto, reintentos automaticos.
- Servicios: `opencode-control.service` (panel, http://127.0.0.1:8765) y `opencode-control-reconcile.timer` (5min) activos via systemd.

## Etapa 7 — Operacion persistente (aprobada 2026-09-18)

- [x] T42 — `systemd/user/opencode-control.service` creado y `enable --now`: WorkingDirectory=%h/opencode-ecosystem, ExecStart con python3.12 local, Restart=on-failure, RestartSec=5, bind 127.0.0.1:8765.
- [x] T43 — `opencode-control-reconcile.{service,timer}`: Type=oneshot, OnBootSec=3min, OnUnitActiveSec=5min, corre `reconcile --apply`. enable --now OK.
- [x] T44 — `configs/cron-jobs.json` incluye `control-reconcile` (fuente de verdad); `sync --apply` con backups; `systemctl --user daemon-reload`; panel muestra 3/3 timers activos (ram-guard, kairos, control-reconcile).
- [x] T45 — Verificacion E2E real: `kill <pid>` del panel viejo -> systemd levanto el servicio (is-active=active, health ok=True timers 3/3). El timer reconcile corrio solo: journalctl muestra `Starting ... [reconcile] findings=0 ok=True Finished` a las 18:23:47 sin intervencion manual. Tests: 77/77 OK, `verify.sh` verde, `status` sin drift, qa-gate strict exit 0.
- [x] T46 — Docs: este documento; README seccion Etapa 7 (pendiente abajo).

## Etapa 4 — Acciones manuales con CSRF (completada)

- [x] T27 — `control/actions.py`: token CSRF (`secrets.token_urlsafe(24)`, un por proceso); acciones cerradas: refresh, run-next (con lock anti-concurrencia), retry (solo dead), cancel (solo pending), add-task (agentes whitelist), restart (solo timers `opencode-*`); cada accion registra evento en SQLite.
- [x] T28 — `server.py` POST con `_csrf_ok()` (token + Origin `127.0.0.1:8765`); token inyectado en HTML (`window.CSRF`), nunca en URL/log; body JSON limitado a 8KB; POST desconocido con token valido -> 400, sin token -> 403.
- [x] T29 — Frontend: boton "▶ ejecutar siguiente", formulario encolar (agente+prompt), reintentar "↻" (dead) y cancelar "✖" (pending) por fila, "↻" restart por timer con `confirm()`. Tras cada accion, `loadData(true)` refresca.
- [x] T30 — Tests `test_actions.py`: 11 casos iniciales; ampliados en Etapa 6 con politica modelo/sensibilidad.
- [x] T31 — Verificacion E2E: CSRF/Origin, add/cancel/retry/run-next y whitelists verificados; status sin drift y verify verde.

## Etapa 5 — Reconciliador automatico (aprobada 2026-09-18)

Watchdog de inconsistencias: tareas `running` que superan timeout+gracia, timers declarados que no estan activos en systemd. Conservador: marca y notifica; no relanza trabajo automatico por si mismo (requiere run-next manual o timer aparte).

- [x] T32 — `control/reconcile.py`: `check()` detecta task_huerfana (running > timeout+300s), timer_ausente, timer_inactivo; `apply_fixes()` solo marca dead lo que sabe, cooldown 120s via `~/.local/share/opencode-control/reconcile-state.json`, preview por defecto. Estilo conservador: NO relanza trabajo.
- [x] T33 — CLI `python3 -m control.cli reconcile [--apply]`. Salida real: `findings=0 ok=True` (sistema sano). Tests `test_reconcile.py`: 9 casos (sano, huerfana, fresca, naive-UTC, timer ausente/inactivo, apply marca dead + evento, cooldown, sin-findings-sin-state).
- [x] T34 — `GET /api/reconcile` + seccion "🩺 Reconciliador" en panel (pill verde/roja, tasks/timers revisadas). HTML verificado.
- [x] T35 — Cierre Etapa 5: 57/57 tests OK, JS validado con `node --check`, `./opencode-ecosystem status` sin drift, `verify.sh` verde.

## Etapa 6 (revisada) — Contrato + lease + piloto SDD

- [x] T36 — 6A: `.gitignore` depurado; doc evolucion `docs/evolution/2026-09-18-plano-control-ecosistema.md`; nota fuente `~/docs/sources/emowe-mapa-agentes-analysis.md` + enlaces en `Sources.md` y `_MOC.md`. Sin commit (pendiente aprobacion).
- [x] T37 — 6B: SQLite schema v2 registrado en `schema_meta`; contrato completo y migracion idempotente; `claim_next()` usa `BEGIN IMMEDIATE`, owner UUID y lease. Test multiproceso: 2 procesos compiten, exactamente 1 reclama.
- [x] T38 — 6B: runner usa claim atomico y workspace validado dentro de HOME; clasifica provider_balance/provider_rate/timeout/infra/contract/agent/verification. Error de proveedor vuelve a pending sin consumir intento. Modelo free exige `free-allowed` y queda prohibido para `sensitive`. API publica redacta prompt/workspace/comandos. Payload sensible se purga al terminar; payload normal terminal, tras 30 dias.
- [x] T39 — 6B: reconciliador prioriza `lease_until`; lease vencido -> hallazgo `lease_vencido` -> dead al aplicar; lease vigente no se toca. Tests cubren ambos casos.
- [x] T40 — 6C: piloto SDD real aislado en `~/.local/share/opencode-control/pilots/sdd-KBr3qh`: task #4 `sdd-implement` (Luna) creo `pilot-result.txt`; task #5 `sdd-verify` heredada termino rc=0; task #6 valido el nuevo check automatico y emitio evento `verification/check determinista` rc=0. Contenido exacto `CONTROL_PILOT_OK`. Ningun proyecto existente fue tocado. Commit: 9381d5e.
- [x] T41 — Cierre 6: 77/77 tests OK; `py_compile` OK; test multiproceso del lease OK; piloto SDD real OK; API tasks redactada; politica free/sensitive y purga probadas; reconciliador sano; `git diff --check` OK; qa-gate strict exit 0; `./opencode-ecosystem status` sin drift; `./verify.sh` verde. Panel reiniciado con codigo actual (pid 178358). Sin commit (no autorizado).
