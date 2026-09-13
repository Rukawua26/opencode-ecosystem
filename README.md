# opencode-ecosystem (lite, 8GB RAM)

Fuente de verdad local. Derivado de `noffolo/opencode-ecosystem` (ver `~/docs/sources/noffolo-ecosystem-analysis.md`), adaptado a i5-1235U / 7.5GB RAM / Ollama 1-3B.

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
Reinicia OpenCode para cargar la skill actualizada.

## Contenido
- `configs/`: opencode.jsonc (mínimo válido, sin MCP inexistentes), dcp.jsonc (32-40k), cron-jobs.json
- `skills/`: 9 curadas lite (5 core + 4 lentes 4R); OpenCode descubre nombre/description y carga el cuerpo bajo demanda con la tool `skill`
- `memory/`: kairos.sh, autodream.sh, MEMORY.md (plantilla; lo vivo queda en ~/.config)
- `scripts/`: ram-guard-lite.sh, qa-gate.sh (warn), co-change-analyzer.sh, hygiene.sh (`triggers|prune|reset`, manual, preview por defecto)
- `verify.sh` (raíz, no se sincroniza): validación única (triggers + debug config + status + doctores)

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
