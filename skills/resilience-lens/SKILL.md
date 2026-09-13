---
name: resilience-lens
description: 4R Resilience lens. Usar cuando el diff toca red o dependencias externas, para revisar timeouts, fallbacks y degradacion elegible; no usar en cambios sin red.
---

# resilience-lens
Lens persuasivo: informa, nunca bloquea. Solo para cambios que toquen red o dependencias externas.

1. Carga rutas seguras con `mapfile -d '' -t files < <(git diff --cached --name-only -z --diff-filter=ACMR)`; si queda vacio, repite con `git diff --name-only -z --diff-filter=ACMR`. Si sigue vacio, responde `Sin hallazgos.` sin ejecutar `rg`.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base anti-slop).
3. Haz un unico barrido sobre `"${files[@]}"`:
   - `rg -n 'fetch|http\.|axios\.get|axios\.post' --no-heading -- "${files[@]}"` — llamadas de red
   - `rg -n 'setTimeout|setInterval|sleep|delay' --no-heading -- "${files[@]}"` — posible espera sin timeout
   - `rg -n 'retry|fallback|offline' --no-heading -- "${files[@]}"` — evidencia auxiliar, no requisito universal
4. Puerta de precision: la sola presencia de un patron no es defecto; reporta solo si falta timeout/fallback con impacto real. Ante la duda, silencio.
5. No bloquea; el revisor humano decide si es blocking o cosmetic. Si no hay nada: `Sin hallazgos.`
