---
nombre: 2026-09-18-plano-control-ecosistema
fecha: 2026-09-18
estado: en_observacion
afecta: [scripts, git]
fuente: otro-repo
---

# Plano de control del ecosistema (panel localhost + lanzador + reconciliador)

## Por que
El ecosistema tenia skills, comandos, subagentes y timers, pero ninguna vista unificada
ni forma de saber que se ejecuto, que fallo, o que esta corriendo. El video de Emowe
(ejDH5-Q9bu4) describia un "mapa visual" generado automaticamente; el paquete
descargado (`~/Descargas/NEXUS 0`) resulto ser otra cosa (vault Obsidian), asi que se
implemento la idea desde cero sobre nuestros datos reales.

## Antes
No habia control/ — ningun inventario rotativo, ni historial, ni cola, ni panel.

## Despues
- `control/model.py, collect.py, state.py, server.py, web/index.html` — panel read-only 127.0.0.1:8765.
- `control/db.py` — SQLite con eventos (recibos) y tasks (cola). Wal mode, retencion 30d/20k.
- `control/runner.py` — cola FIFO, 1 tarea a la vez, timeout 900s, 2 intentos -> dead.
- `control/actions.py` — acciones panel con CSRF token por proceso, whitelist.
- `control/reconcile.py` — watchdog conservador: marca dead lo atascado, notifica timers.
- Etapa 6: contrato de tarea v2, lease atomico SQLite entre procesos, politica paid/free y sensibilidad, workspace acotado, check determinista tras verificador.
- Tests: 74.

## Beneficio
1 comando para ver todo (health, cola, actividad) y ejecutar el siguiente paso del flujo.

## No regresion
- El panel nunca escribe fuera de su DB/state en ~/.local/share/opencode-control/.
- El runner no almacena stdout del modelo.
- Nada de esto toca `~/.config/opencode` salvo lectura.

## Verificacion
- `python3 -m unittest discover -s control/tests` — 77/77 tests OK (Etapa 6).
- `./opencode-ecosystem status` — sin drift.
- `./verify.sh` — verde.
- Piloto E2E inicial: task #2 done rc=0 (nemotron free).
- Piloto SDD real: tasks #4 implement / #5 verify / #6 check automatico, Luna, workspace aislado; `CONTROL_PILOT_OK`, rc=0.
- Etapa 7 (2026-09-18): `systemctl --user enable --now opencode-control.service opencode-control-reconcile.timer`; el timer reconcile disparo solo a las 18:23:47 con `findings=0 ok=True`; kill del panel manual -> systemd levanto el servicio automaticamente.

## Periodo prudencial
- Estable tras 1 semana sin regressions de drift/tests.
- Si rompe: quitar `control/` no afecta al resto del ecosistema (self-contained).

## Fuente (si aplica)
Video Emowe "Como controlo +50 Agentes IA y +200 Skills con un SOLO Mapa Visual"
(2026-09-17): toma la IDEA de panel automatico, NO el artefacto descargado (NEXUS 0
resulto ser un Vault Obsidian, no el mapa — ver `~/docs/sources/emowe-mapa-agentes-analysis.md`)
