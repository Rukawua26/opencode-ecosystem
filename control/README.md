# Plano de control del ecosistema OpenCode

## Qué es
Panel local (127.0.0.1:8765) que observa tu `opencode-ecosystem` y muestra:

- skills, comandos, agentes, scripts, configs
- timers systemd (activos, última ejecución, próxima)
- salud del servicio OpenCode
- flujos declarados (ODD, ODD delegado, QA-gate)
- cola de tareas del lanzador y actividad auditable
- acciones cerradas desde el panel (Etapa 4, ver abajo)

## Uso

### Recoger snapshot una vez
```bash
python3 -m control --once --pretty
```

### Servir el panel local
```bash
python3 -m control --serve
# abrir http://127.0.0.1:8765
```

### CLI rápido
```bash
python3 -m control.cli status
python3 -m control.cli snapshot
# diagnostico sanitizado (salud, cola, reconciliador, sin prompts ni comandos)
python3 -m control.cli doctor
python3 -m control.cli doctor --json
# registrar un recibo de ejecucion real (Fase 2)
python3 -m control.cli receipt odd-worker --status ok --duration 12.5 --note "tarea T3"
```

## Modelo de verdad
```
Observado  → leído directamente de fs/systemd/`opencode service status`
Declarado  → listado explícito (flujos ODD)
Inferido   → no usado en F1
Desconocido → sin evidencia
```

## Qué no hace
- No acepta comandos arbitrarios desde el navegador: `verification_command` y el
  contrato completo solo via CLI (`control.cli task add ...`).
- No abre la API interna de OpenCode (usa CLI `opencode service status`).
- La API y el panel nunca muestran prompts, workspace ni comandos de verificacion.
- La cola SQLite guarda temporalmente el prompt necesario para ejecutar; tareas `sensitive`
  purgan el payload al terminar y las normales lo purgan tras 30 dias.
- Nunca guarda respuestas completas del modelo, variables de entorno ni credenciales.
- No relanza trabajo automaticamente: ejecutar tareas es decision humana
  (boton "▶ ejecutar siguiente" o `control.cli task run`).

## Historial y recibos (Fase 2)
```
~/.local/share/opencode-control/control.db   # SQLite (WAL), retencion 30 dias / 20k filas
```
- **Eventos automáticos**: cambios de estado detectados entre recolecciones (timer parado, servicio caído, componente añadido/eliminado, resultado cambiado).
- **Recibos explícitos**: `control.cli receipt` — la forma honesta de saber que algo se ejecutó de verdad.
- Panel: sección "Actividad reciente" + historial por componente (clic en la tarjeta).
- Solo se registra lo que cambia (sin ruido por polling).

## Estructura
```
control/
  model.py      — dataclasses Component, TimerInfo, Flow, Snapshot
  collect.py    — scan fs + systemd + opencode service status
  state.py      — cache TTL + escritura atómica del snapshot
  server.py     — http.server, solo 127.0.0.1, read-only
  cli.py        — status/snapshot rápido
  main.py       — entrada --once / --serve
  web/index.html — interfaz sin dependencias
```

## Donde se guarda
```
~/.local/share/opencode-control/snapshot.json
```

## Servicios systemd (Etapa 7)

```
~/.config/systemd/user/
  opencode-control.service            ← panel web (Restart=on-failure)
  opencode-control-reconcile.timer    ← cada 5 min
  opencode-control-reconcile.service  ← oneshot: reconcile --apply
```

Si matas el proceso del panel, systemd lo reinicia automaticamente. El reconciliador corre solo en background y marca `dead` las tareas atascadas sin intervencion.

## Etapa 10A — Mapa operativo con filtros e inspector visual (2026-09-19)

Panel local con tres vistas (`Resumen` · `Mapa` · `Actividad`), navegacion por hash URL,
mapa operativo SVG inline (11 nodos agrupados) con filtros por capa/estado/fuente,
inspector lateral (estado, capa, fuente, evidencia, antiguedad, conexiones, eventos),
datos observados vs. declarados diferenciados (fuente + tipo de linea),
accesible (aria, teclado, Escape, responsive) y con pruebas E2E.

Inspiracion conceptual (sin copiar codigo): Public APIs (categorias + evidencia),
Free Programming Books (busqueda + categorias), freeCodeCamp (vistas separadas),
Brahma Echo (bento + panel inspector).

Decisiones clave: SVG inline sin librerías, sin React/Mermaid/WebSockets,
sin acceso remoto, sin undo genérico, sin voz. Solo fuentes
`observado | declarado | inferido`.

Verificacion: 108/108 tests OK, Playwright real (0 console errors, 0 HTTP 404,
movil sin overflow), `verify.sh` verde, `status` sin drift, qa-gate strict OK.

### Reconciliador (Etapa 5)
Vigilante de consistencia. Preview por defecto:
```bash
python3 -m control.cli reconcile           # solo detecta, no toca nada
python3 -m control.cli reconcile --apply   # marca dead tareas huerfanas (cooldown 120s)
```

Reglas:
- Task `running` que supera timeout+5min → marca `dead` (huerfana).
- Timer declarado en `cron-jobs.json` pero ausente/inactivo en systemd → **notifica**, no reinicia (lo haces desde el panel con ↻).
- **Nunca** relanza trabajo automaticamente. Eso es decision humana.
- Estado y cooldown persisten en `~/.local/share/opencode-control/reconcile-state.json`.
- Seccion "🩺 Reconciliador" en el panel muestra el ultimo chequeo.
- Desde Etapa 7 corre solo via `opencode-control-reconcile.timer` (cada 5 min).

## Acciones desde el panel (Etapa 4)
Tras la lista de "solo lectura", el panel admite acciones cerradas:

- **↻ actualizar** (arriba): fuerza recoleccion real.
- **▶ ejecutar siguiente**: lanza la primera tarea `pending` (1 a la vez; si hay otra corriendo, avisa).
- **＋ encolar**: agente + prompt + modelo opcional, whitelist de agentes.
- **↻ / ✖** por tarea: reintenta (`dead` o `waiting`) o cancela (`pending`).
- **↻** por timer: reinicia el timer systemd (`confirm()` antes).

Seguridad:
- Token CSRF por proceso; sin el, 403. Origin debe ser `127.0.0.1:8765`.
- Sin shell arbitrario; solo las acciones listadas.
- Cada accion deja evento auditable en `/api/events`.

## Lanzador de tareas (Etapa 3)
```bash
# encolar
python3 -m control.cli task add odd-worker "implementa X" --model openai/gpt-5.6-luna
# ver la cola
python3 -m control.cli task list
# ejecutar la siguiente (UNA a la vez, timeout 15min, max 2 intentos)
python3 -m control.cli task run
```

Contrato completo (Etapa 6):
```bash
python3 -m control.cli task add odd-worker "implementa T1 de odd/tasks/001-feature.md" \
  --workflow odd \
  --workspace "$HOME/proyecto" \
  --feature 001-feature \
  --expected-outputs "src/a.py" \
  --verification-command "pytest -q" \
  --model openai/gpt-5.6-luna \
  --model-policy paid \
  --sensitivity normal
```

Reglas del lanzador:
- **1 tarea a la vez** (proceso sincrono).
- Claim atomico SQLite (`BEGIN IMMEDIATE`) + lease; dos runners no ejecutan la misma tarea.
- rc=0 + `RESULT: success` → `done`; rc≠0 o contrato ODD invalido → reintenta hasta 2 veces → luego `dead`.
- `RESULT: blocked` → `waiting` sin consumir intento; tras registrar la decision en ODD se reintenta manualmente.
- Un `odd-worker` ok encadena automaticamente un `odd-verifier`.
- El verificador hereda workspace, feature, modelo y criterios; tras rc=0 ejecuta el `verification_command` determinista (timeout 120s).
- El stdout del modelo NUNCA se guarda en el historial (solo rc + duracion + resumen).
- Fallos del proveedor (saldo/rate limit) no consumen intentos funcionales.
- Modelos free requieren `free-allowed` y estan prohibidos en tareas `sensitive`.
- El panel muestra la cola en vivo (seccion "Cola de tareas").

## Worktree manual (opcional)
Procedimiento aprobado:
```bash
git worktree add --detach <ruta-dentro-de-HOME> HEAD
python3 -m control.cli task add odd-worker "implementa X" --workspace <ruta>
```
- El runner solo acepta workspaces dentro de `HOME`.
- Haz una revision humana del diff antes de integrar cambios.
- Ejecuta `git worktree remove <ruta>` solo cuando este limpio; nunca uses `--force`.

## Limitaciones conocidas
- Los timers se leen del systemd del usuario actual.
- Los "agentes" se extraen del `configs/opencode.jsonc` con regex — suficiente para esta etapa.
- Los flujos no se infieren automaticamente: solo los declarados.
- Sin WebSockets; refresco cada 30s.
- El runner es 1-tarea-a-la-vez: boton del panel o `control.cli task run`; el reconciliador
  (timer cada 5 min) solo marca atascadas, no las relanza.
