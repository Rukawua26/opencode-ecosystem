# 001-ecosystem-lite — Plan

## F0 auditoría (hecho parcial)
- doctor + plugin_doctor + backup /tmp/opencode-backup-20260911 + nota ADR-004.

## F1 lite in-place (~/.config/opencode)
1. `opencode.jsonc`: schema y configuracion minima. MCP memory-adapter/local-router diferidos al no existir sus binarios.
2. `dcp.jsonc`: enabled, 32-40k límites, protege task/skill/todowrite.
3. `memory/`: observations.log, kairos.sh (30min), autodream.sh (idle), MEMORY.md + topics/.
4. `scripts/ram-guard-lite.sh` + `scripts/qa-gate.sh` (warn) + `co-change-analyzer.sh` mínimo.
5. `skill/` 5 curadas lite (md + frontmatter).
6. `cron-jobs.json` + `systemd --user` timers (ram-guard 5min, kairos 30min).

## F2 extraer a ~/opencode-ecosystem
- `configs/`, `skills/`, `memory/`, `scripts/{publish,sync,status}` con symlinks y `.ecosystem-managed-files`. publish=solo copia desde repo; sync=aplica a ~/.config con backup; status=diff.

## Verificación
- `plugin_doctor`, `opencode --version`, `ollama list`, ejecución en seco de scripts, `verify.md`.
