# opencode-ecosystem (lite, 8GB RAM)

Fuente de verdad local del ecosistema OpenCode del usuario. Derivado de
`noffolo/opencode-ecosystem`, adaptado a i5-1235U / 8GB RAM con filosofia de
ahorro de tokens y YAGNI. Incluye el plano de control local (`control/`) y el
formato de trabajo organico ODD (`odd/`).

## Flujo oficial

```bash
# Si editaste esta fuente de verdad:
./opencode-ecosystem sync --apply
./opencode-ecosystem status

# Solo si editaste ~/.config/opencode en caliente:
./opencode-ecosystem publish --yes
```
> Regla anti-wipe (2026-09-11): `sync` va ECO→CFG y pisa cambios en caliente.
> Si editaste `~/.config` directo, haz `publish` ANTES de `sync`. Ante duda, `status` primero.

- `status`: diff ECO vs `~/.config/opencode` (drift).
- `sync --apply`: ECO→CFG con backup `.bak-FECHA`. `opencode.jsonc` solo se reemplaza aquí.
- `publish --yes`: CFG→ECO (recoge cambios hechos en caliente).
- `capture --apply`: recuperación manual controlada.
- `uninstall [--apply]`: inverso selectivo por manifiesto (preview por defecto, backup `.pre-uninstall-*`). Reporta lo eliminado y lo retenido.
- Nunca se sincronizan: `.env`, `observations.log`, `topics/`, logs, backups, plugins personales.
- El uninstall retiene esos recursos por diseño: contienen secretos, historia viva o personalizaciones ajenas al ecosistema.
- Reinicia OpenCode si cambian plugins, config de arranque o skills.

## Autoría de skills

Contrato oficial: <https://opencode.ai/docs/skills/>. Edita siempre la fuente en `skills/<name>/SKILL.md` y ejecuta:

```bash
python3 ./validate-skills.py ./skills
./opencode-ecosystem sync --apply
opencode debug skill
```

Reinicia OpenCode para cargar la skill actualizada. Documenta cada cambio en `docs/evolution/` (usar `_TEMPLATE.md`).

## Contenido

- `AGENTS.md`: reglas del agente (autorización humana, ODD, routing, autopistas de contexto).
- `commands/`: comandos personalizados de OpenCode.
- `configs/`: opencode.jsonc (mínimo válido, sin MCP inexistentes), dcp.jsonc (32-40k), cron-jobs.json.
- `control/`: **plano de control** — panel local y lanzador de tareas (Python). Ver `control/README.md`.
- `docs/evolution/`: historial de cambios al ecosistema (patrón `_TEMPLATE.md`).
- `memory/`: kairos.sh, autodream.sh, MEMORY.md (plantilla; lo vivo queda en ~/.config).
- `odd/tasks/`: documentos ODD de features activas (formato de trabajo organico sustancial).
- `scripts/`: ram-guard-lite.sh, qa-gate.sh (warn), co-change-analyzer.sh, hygiene.sh (`triggers|prune|reset`, manual, preview por defecto).
- `skills/`: 10 curadas lite (6 core + 4 lentes 4R); OpenCode descubre nombre/description y carga el cuerpo bajo demanda con la tool `skill`. `organic-workflow-lite` (ODD) solo se carga en trabajo sustancial.
- `opencode-ecosystem` (raíz): CLI de gestión ECO↔CFG.
- `validate-skills.py` / `verify.sh` (raíz, no se sincronizan): validación única (triggers + debug config + status + doctores).

## Plano de control (control/)

Panel local (127.0.0.1:8765) que observa el ecosistema: skills, comandos, agentes,
scripts, configs, timers systemd, salud del servicio OpenCode, flujos declarados
(ODD, ODD delegado, QA-gate), cola de tareas del lanzador y actividad auditable.

```bash
python3 -m control --once --pretty     # snapshot una vez
python3 -m control --serve             # panel local -> http://127.0.0.1:8765
python3 -m control.cli status          # CLI rapido
python3 -m control.cli doctor          # diagnostico sanitizado
python3 -m control.cli receipt odd-worker --status ok --duration 12.5 --note "tarea T3"
```

- Modelo de verdad: `Observado` (leído de fs/systemd/`opencode service status`) vs `Declarado` (flujos ODD explícitos).
- Lanzador de tareas: `python3 -m control.cli task add oddd-worker --model ...` encola tareas para subagentes `odd-worker` / `odd-verifier`.
- Tests: `python3 -m unittest discover control/tests` (suite completa en `control/tests/`).

## Ámbito: global vs proyecto (004-E, patron gentle-ai --scope)

- Global (`~/.config/opencode`, este repo): todo lo de arriba. Es el default.
- Proyecto (`opencode.json` en la raíz del repo): solo overrides puntuales (modelo, 1-2 permisos).
  Nunca dupliques aquí lo global; el merge de OpenCode ya lo combina (precedencia: proyecto > global).
- Pin de backups (004-G): renombra el `.bak-*` que quieras conservar fuera del patrón
  (p. ej. `.bak-pinned`) y `prune` lo ignorará.

## Timers

`configs/cron-jobs.json` es declarativo (qué jobs existen); el ejecutor real son los
`systemd --user` timers (`opencode-ram-guard.timer` 5min, `opencode-kairos.timer` 30min).
Si editas el JSON, replica el cambio en `~/.config/systemd/user/` y haz `daemon-reload`.
Alternativa sin systemd: cron clásico con las mismas líneas.

## Tests y verificación

```bash
python3 -m unittest discover control/tests        # suite completa
./verify.sh                                        # triggers + config + status + doctores
./scripts/hygiene.sh triggers                      # higiene manual (preview por defecto)
```