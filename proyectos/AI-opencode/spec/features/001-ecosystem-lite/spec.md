# 001-ecosystem-lite — Spec

## Problema
OpenCode está vanilla (`opencode.jsonc` vacío, sin plugins/MCP) mientras `AGENTS.md` describe un ecosistema que no existe. El repo de referencia (`noffolo/opencode-ecosystem`) pide 16-32GB RAM y modelos 7-14B; la máquina tiene 7.5GB y modelos 1-3B. Sin adaptación ligera hay OOM o deriva docs-vs-realidad.

## Alcance
- ENTRA: config lite `~/.config/opencode` (jsonc + dcp 32-40k), memoria Bash 4 fases, ram-guard-lite + qa-gate warn, 5 skills curadas, timers systemd, `~/opencode-ecosystem` como fuente de verdad con publish/sync/status.
- DIFERIDO: MCP memory-adapter/local-router; no existian binarios y configurarlos habria roto el arranque.
- FUERA: modelos ≥7B, oh-my-openagent completo/bun build, CodeMEM pnpm, Docker obligatorio, Sentry, ghgrab global, cientos de skills, brew.

## Criterios de aceptación
1. `opencode --version` 1.18.x; Ollama 1-3B puede existir externamente, pero no queda mapeado en OpenCode.
2. `plugin_doctor.sh --no-binary` verde y `query_context.py doctor` <4k piso fijo.
3. `ram-guard-lite.sh` + `kairos.sh` ejecutables y timers instalados (o documentado por qué no).
4. `qa-gate.sh` en warn no rompe commits; `MEMORY.md` se actualiza sin Docker.
5. `~/opencode-ecosystem status` sin drift; backup `.bak` existe; `.env`/memoria/logs nunca sincronizados.
