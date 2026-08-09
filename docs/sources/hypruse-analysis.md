---
titulo: "hypruse — Análisis"
tipo: fuente
fuente: "https://pypi.org/project/hypruse/0.9.4/"
autor: ""
fecha: 2026-08-08
estado: verificado
tags: [referencia, mcp, hyprland, ipc, opencode]
relacionado: ["[[Sources]]", "[[_MOC]]", "[[OpenCode System]]", "[[Plugins OpenCode]]"]
---

# hypruse — Análisis de repositorio

> [!info] Origen y baseline
> - URL: https://pypi.org/project/hypruse/0.9.4/ (upstream `gentman59/hypruse`)
> - Versión verificada: **0.9.4** (`hypruse/__init__.py: __version__ = "0.9.4"`), provisto por el runtime importando el paquete de caché uv (`/home/miguel/.cache/uv/archive-v0/e7P3Sb7OcsBZ1keN/hypruse/`)
> - No hay git repo en el workspace; baseline de *hardware*: i5-1235U (12 hilos), **8GB RAM**, Ollama local (qwen2.5-coder:3b), filosofía de **ahorro de tokens**
> - Stack del repo: Python MCP server que envuelve el IPC de Hyprland (`hyprctl`/socket de `hyprland`) exponiendo observación de escritorio + dispatchers (`workspace`/`focus`/`exec`/etc.). El runtime lo expone como herramientas nativas `hypruse_*` (no como plugin OpenCode ni MCP server en `opencode.jsonc`).

## Qué es (resumen)
`hypruse` es un servidor MCP en Python que convierte Hyprland en *tools* usables por agentes: observa monitores/workspaces/ventanas/cursor, captura screenshots, lee árbol de accesibilidad (AT-SPI), y ejecuta acciones (focus de ventana, cambio de workspace, lanzar apps, teclear/click en ventanas). En este entorno se importa directamente del *cache* uv de `hypruse 0.9.4`; **no hay parche local ni modificación de disco** — todo funciona con el código stock.

## Verificación de línea base
| Cosa | Estado |
|---|---|
| Versión inspeccionada | ✅ 0.9.4 (`__init__.py`) |
| Source on disk inspeccionado | ✅ caché uv (`/.../hypruse/{server.py,input.py,cli.py}`) |
| Dispatcher identificado | ✅ `hyprctl.dispatch(name, args)` (envoltura sobre el socket de `hyprland`) |
| Observación tools | ✅ `hypruse_desktop` funciona |
| Acción tools (stock) | ✅ `hypruse_hypr workspace`, `focus_window`, `launch` funcionan end-to-end |
| P4 focus ventana flotante | ✅ `focus_window` enfoca `0x565060eafef0` (Ghostty, floating) → `active_window` cambia |

## Hallazgo principal: NO HAY BUG, fue uso incorrecto de la tool
Durante P4 se llamó a `hypruse_keyboard` con `action='focus'`. El *enum* de `hypruse_keyboard` es **estrictamente `type|key`** (server.py:610) — no existe `action='focus'`. El error `unknown action 'focus': type|key` es un *mismatch de contrato de uso*, no un defecto del código.
- El foco de ventana NO se hace con `hypruse_keyboard`. El *modo correcto* es `hypruse_hypr action='focus_window' target=<address>` (server.py:811-812 → `hyprctl.dispatch("focuswindow", _addr(target))`).
- `hypruse_keyboard(window=<addr>, action='type'|'key', …)` **enfoca la ventana objetivo primero** (valida `_addr(window)`) y luego escribe/teclea en ella — es para *input*, no para *focus puro*.

## ✅ Lo que se verifica que TOMAMOS
1. **Mapa de tools vs dispatchers stock** (para no volver a usar la tool equivocada):
   | Necesidad | Tool correcta | Dispatcher | Path server.py |
   |---|---|---|---|
   | Cambiar workspace | `hypruse_hypr action='workspace'` | `hyprctl.dispatch("workspace", ws)` | :806-809 |
   | **Focus ventana (por address)** | `hypruse_hypr action='focus_window' target=<addr>` | `hyprctl.dispatch("focuswindow", addr)` | :811-812 |
   | Lanzar app | `hypruse_launch command=…` | `hyprctl.dispatch("exec", cmd)` | :865/868, :880 |
   | Teclear en ventana | `hypruse_keyboard window=<addr> action='type'|'key'` | focus implícito + `wtype` | :609-615 |
2. **`_addr()`** (server.py:741) normaliza la dirección (`0x565060…` → `address:0x565060…`), por lo que addresses de ventanas flotantes (`at=[-2,-2]`, `floating:true`) se enfocan igual que las normales → P4 lo confirma.

## ❌ Lo que DEJAMOS (y por qué)
1. **No aplicar parche `hl.dsp.*`** — no existe `hl.dsp` en 0.9.4; todo va por `hyprctl.dispatch`/socket. Cualquier "parche" es pura invención y corrompe el registro.
2. **No añadir `action='focus'` a `hypruse_keyboard`** — su contrato es `type|key`; forzar `focus` ahí rompería la claridad. El foco tiene su propia tool (`hypruse_hypr focus_window`).
3. **No instalar ni bumpear hypruse** — funciona como está.

## ⚖️ Lo nuestro vs lo suyo
| Área | Nuestro (uso) | Upstream hypruse 0.9.4 | Veredicto |
|---|---|---|---|
| Observación | `hypruse_desktop` | idéntico | ✅ match |
| Focus | `hypruse_hypr focus_window` | idéntico | ✅ match |
| Exec/launch | `hypruse_launch` | idéntico | ✅ match |
| Keyboard | `hypruse_keyboard` (type\|key) | idéntico | ✅ match |
| Parche | — | — | ✅ **no se necesita** |

## 📋 Plan de implementación
- [x] **P1 — Identificar el dispatcher real** (`hyprctl.dispatch` sobre socket; no `hl.dsp`).
- [x] **P2 — Corregir el uso**: P4 repetido con `hypruse_hypr action='focus_window' target=0x565060eafef0` → `active_window` == objetivo ✅.
- [x] **P3 — Confirmar launch end-to-end**: `hypruse_launch "brave --new-window https://www.youtube.com"` → ventana `0x565060f187a0` (ws2) cargó YouTube ("(354) YouTube - Brave") ✅.
- [x] **P4 — Focus ventana flotante**: Ghostty (`floating:true`, address `0x565060eafef0`) enfocado via `focus_window`; `then=desktop` confirmó `active_workspace: 2` y `active_window: 0x565060eafef0` ✅.

## 🔄 Protocolo de re-verificación
1. Focus de cualquier ventana: usar SIEMPRE `hypruse_hypr action='focus_window' target=<address>` (no `keyboard`). Confirmar con `then=desktop` → `active_window == target`.
2. Ventana flotante (`floating:true`, `at` fuera de rango): el mismo `focus_window` vale (`_addr` normaliza).
3. Lanzar: `hypruse_launch` con `wait_s` suficiente; si la app abre login/sign-in (ej. YouTube sin cuenta) el `title` cambia a la ruta de sign-in — no confundir con fallo del tool.
4. Nunca necesario rever: tools de solo observación (`desktop`/`screenshot`/`ui`/`marks`) no usan el dispatcher.

## Relacionado
- [[Sources]]
- [[_MOC]]
- [[OpenCode System]]
- [[Plugins OpenCode]]
