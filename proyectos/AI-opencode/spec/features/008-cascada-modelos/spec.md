# 008-cascada-modelos — Spec

## Problema
Si se agota saldo/cuota de los modelos GPT-5.6 (pay-as-you-go en Zen vía provider `openai`), no hay guía ni configuración para degradar por potencia sin perder la sesión. Además, el modelo de fondo (títulos/compactación) no está acotado en coste.

## Alcance
- ENTRA: `small_model` free, variantes `low` en gpt-5.6-sol/terra/luna, playbook de cascada en `~/docs/runbooks/`, 1 línea en AGENTS.md.
- FUERA: failover automático (no existe en OpenCode), `model` default fijo (sigue last-used), Gemini/Qwen (requieren `/connect` del humano, anexo), Ollama backup, auto-reload/limits (dashboard, humano).

## Criterios de aceptación
1. `debug config` válido con `small_model` y variantes `low` en openai/gpt-5.6-{sol,terra,luna}.
2. Playbook existe con 6 peldaños + medio-peldaño de variante + matriz de datos de los free.
3. `status sin drift`, `verify.sh` verde, piso fijo sin crecimiento significativo.
4. Requiere reinicio de OpenCode (config no hot-reload).
