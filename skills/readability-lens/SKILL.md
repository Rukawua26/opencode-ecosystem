---
name: readability-lens
description: 4R Readability lens. Usar para sugerir revision humana de legibilidad; nunca automatiza la decision ni bloquea. NO usar en cambios triviales de 1-3 lineas.
---

# readability-lens
Lens persuasivo: solo sugiere revisión humana — los juicios de legibilidad no se pueden automatizar decentemente.

1. Carga rutas seguras con `mapfile -d '' -t files < <(git diff --cached --name-only -z --diff-filter=ACMR)`; si queda vacio, repite con `git diff --name-only -z --diff-filter=ACMR`. Si sigue vacio, responde `Sin hallazgos.` sin ejecutar `rg`.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base).
3. Busca pistas mecanicas solo en `"${files[@]}"` (no bloquean, solo avisan si el humano quiere mirar):
   - `rg -n '^\s{16,}' --no-heading -g '!*test*' -- "${files[@]}"` — sangria > 4 niveles (senal de complejidad)
   - `rg -n 'function [a-zA-Z_]+\s*\([^)]*\)\s*\{[^{}]*(?:{[^{}]*}){3,}' --multiline --no-heading -g '!*_test.*' -- "${files[@]}"` — funciones con 3+ bloques anidados
   - `rg -n 'let |var |const ' --no-heading -- "${files[@]}" | rg -v '(const|let|var) [a-z]'` — nombres cortos sin contexto (`d`, `res`, `tmp`)
4. Puerta de precision: solo senala lineas realmente distraedoras; ante la duda, silencio. Si no hay nada: `Sin hallazgos.`
5. `code-forge-fix-lite` nunca automática; el agente recomienda `gofmt -w`/`prettier` si aplica, pero el humano decide.
