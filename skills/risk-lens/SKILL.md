---
name: risk-lens
description: 4R Risk lens. Usar cuando una review busca errores no verificados, fallos silenciosos o condiciones de borde en el diff. NO usar en diffs de solo docs o config.
---

# risk-lens
Lens persuasivo: informa, nunca bloquea. Revisa el staged diff buscando patrones de riesgo.

1. Carga rutas seguras con `mapfile -d '' -t files < <(git diff --cached --name-only -z --diff-filter=ACMR)`; si queda vacio, repite con `git diff --name-only -z --diff-filter=ACMR`. Si sigue vacio, responde `Sin hallazgos.` sin ejecutar `rg`.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base: catch vacio, console.log).
3. Ejecuta un unico barrido sobre `"${files[@]}"`: `rg -n 'catch.*\{\}|\.catch\(\)|TODO|FIXME' --no-heading -g '!*.bak-*' -- "${files[@]}"` y `rg -n 'log\.\w+\(|fmt\.Error' -g '!*_test.go' -g '!*.bak-*' -- "${files[@]}"`.
4. Puerta de precision: reporta solo defectos reales con evidencia (path:linea + por que importa); ante la duda, silencio; prohibidos hallazgos de estilo.
5. Si el hallazgo fue introducido por el candidato actual, notalo explicitamente. No genera correcciones. Si no hay nada, responde exactamente: `Sin hallazgos.`
