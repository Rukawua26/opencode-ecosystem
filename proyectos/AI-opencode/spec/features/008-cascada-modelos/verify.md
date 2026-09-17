# 008-cascada-modelos — verify.md (2026-09-11)

## Evidencia
1. **Config**: `debug config` muestra `small_model: opencode/nemotron-3-ultra-free` y
   variante `low` (reasoningEffort+textVerbosity) en gpt-5.6-sol/terra/luna. JSONC parsea OK.
2. **Playbook**: `~/docs/runbooks/runbook-cascada-modelos.md` creado (6 peldaños + medio-peldaño
   de variante + matriz de datos free). AGENTS.md apunta al runbook.
3. **Ecosistema**: `sync --apply` OK, `status sin drift`, `verify.sh` verde.
4. **Descubrimiento confirmado**: los GPT-5.6 viven bajo provider `openai/` (no `opencode/`);
   free bajo `opencode/`. IDs verificados con `opencode models` el 2026-09-11.

## Errores encontrados y corregidos
1. **Provider prefix equivocado**: la doc de Zen dice `opencode/<id>` pero la lista real
   usa `openai/gpt-5.6-*`. Se usó el prefijo real; si se hubiera escrito `opencode/gpt-5.6-sol`
   en small_model/variantes no habría coincidido con ningún modelo.
2. **Coste de contexto**: piso fijo subió ~2819 → ~3085 tok (+10%). Aceptado: 14 líneas compran
   degradación de coste automática; queda registrado.

## Acción humana
- Reiniciar OpenCode: la config se carga al arranque, no en caliente.
- Dashboard Zen: revisar auto-reload y monthly limits (prevención, fuera del código).
