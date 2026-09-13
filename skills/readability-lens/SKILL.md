---
name: readability-lens
description: 4R Readability lens. Usar para sugerir revision humana de legibilidad; nunca automatiza la decision ni bloquea. NO usar en cambios triviales de 1-3 lineas.
---

# readability-lens
Lens persuasivo: solo sugiere revisión humana — los juicios de legibilidad no se pueden automatizar decentemente.

1. Base del barrido: `F=$(git diff --cached --name-only; git diff --name-only | sort -u)`. Un unico barrido sobre esos ficheros.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base).
3. Pistas mecanicas solo en `$F` (no bloquean, solo avisan si el humano quiere mirar):
   - `rg -n '^\s{16,}' $F --no-heading -g '!*test*'` — sangría > 4 niveles (señal de complejidad)
   - `rg -n 'function [a-zA-Z_]+\s*\([^)]*\)\s*\{[^{}]*(?:{[^{}]*}){3,}' $F --multiline --no-heading -g '!*_test.*'` — funciones con 3+ bloques anidados
   - `rg -n 'let |var |const ' $F --no-heading | rg -v '(const|let|var) [a-z]'` — nombres cortos sin contexto (`d`, `res`, `tmp`)
4. Puerta de precision: solo senala lineas realmente distraedoras; ante la duda, silencio. Si no hay nada: `Sin hallazgos.`
5. `code-forge-fix-lite` nunca automática; el agente recomienda `gofmt -w`/`prettier` si aplica, pero el humano decide.
