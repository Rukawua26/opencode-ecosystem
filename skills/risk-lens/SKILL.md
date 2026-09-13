---
name: risk-lens
description: 4R Risk lens. Usar cuando una review busca errores no verificados, fallos silenciosos o condiciones de borde en el diff. NO usar en diffs de solo docs o config.
---

# risk-lens
Lens persuasivo: informa, nunca bloquea. Revisa el staged diff buscando patrones de riesgo.

1. Base del barrido: `F=$(git diff --cached --name-only; git diff --name-only | sort -u)`. Un unico barrido sobre esos ficheros; nunca el arbol completo.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base: catch vacio, console.log).
3. `rg -n 'catch.*\{\}|\.catch\(\)|TODO|FIXME' $F --no-heading -g '!*.bak-*'` y `rg -n 'log\.\w+\(|fmt\.Error' $F -g '!*_test.go' -g '!*.bak-*'` — errores que nunca se verifican.
4. Puerta de precision: reporta solo defectos reales con evidencia (path:linea + por que importa); ante la duda, silencio; prohibidos hallazgos de estilo.
5. Si el hallazgo fue introducido por el candidato actual, notalo explicitamente. No genera correcciones. Si no hay nada, responde exactamente: `Sin hallazgos.`
