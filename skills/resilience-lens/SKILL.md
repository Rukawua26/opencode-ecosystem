---
name: resilience-lens
description: 4R Resilience lens. Usar cuando el diff toca red o dependencias externas, para revisar timeouts, fallbacks y degradacion elegible; no usar en cambios sin red.
---

# resilience-lens
Lens persuasivo: informa, nunca bloquea. Solo para cambios que toquen red o dependencias externas.

1. Base del barrido: `F=$(git diff --cached --name-only; git diff --name-only | sort -u)`. Un unico barrido sobre esos ficheros.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base anti-slop).
3. Busca solo en `$F`:
   - `rg -n 'fetch|http\.|axios\.get|axios\.post' $F --no-heading` — llamadas de red
   - `rg -n 'setTimeout|setInterval|sleep|delay' $F --no-heading` — posible espera sin timeout
   - `rg -n 'retry|fallback|offline' $F --no-heading` — deberian existir en cambios de red; ausencia = riesgo
4. Puerta de precision: la sola presencia de un patron no es defecto; reporta solo si falta timeout/fallback con impacto real. Ante la duda, silencio.
5. No bloquea; el revisor humano decide si es blocking o cosmetic. Si no hay nada: `Sin hallazgos.`
