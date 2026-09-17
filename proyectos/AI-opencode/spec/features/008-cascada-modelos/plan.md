# 008-cascada-modelos — Plan

1. Spec (hecho).
2. ECO `configs/opencode.jsonc`: `small_model: opencode/nemotron-3-ultra-free` + `provider.openai.models` con variante `low` (reasoningEffort low, textVerbosity low) para sol/terra/luna.
3. Runbook `~/docs/runbooks/runbook-cascada-modelos.md`.
4. AGENTS.md: 1 línea de cascada.
5. `sync --apply` → `status` → `verify.sh` → `debug config`.
6. `verify.md` + aviso de reinicio.
