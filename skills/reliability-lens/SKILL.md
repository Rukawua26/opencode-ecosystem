---
name: reliability-lens
description: 4R Reliability lens. Usar cuando el diff toca tests o codigo con estado/tiempo, para detectar flakiness, mocks fragiles y aserciones no deterministas.
---

# reliability-lens
Lens persuasivo: informa, nunca bloquea. Solo para tests o código que afecte estabilidad.

1. Carga rutas seguras con `mapfile -d '' -t files < <(git diff --cached --name-only -z --diff-filter=ACMR)`; si queda vacio, repite con `git diff --name-only -z --diff-filter=ACMR`. Si sigue vacio, responde `Sin hallazgos.` sin ejecutar `rg`.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base).
3. Haz un unico barrido sobre `"${files[@]}"`:
   - `rg -n 'sleep|waitFor|setTimeout\(\s*\d+.,\s*[0-9]+\)' --no-heading -g '*test*' -g '*spec*' -- "${files[@]}"` — tiempo hardcodeado
   - `rg -n 'jest\.mock|vi\.mock|sinon|nock' --no-heading -- "${files[@]}"` — mocks que requieren revision
   - `rg -n 'Date\.now\(\)|Math\.random' --no-heading -- "${files[@]}"` — posible no-determinismo
4. Puerta de precision: marca flaky solo con evidencia concreta; ante la duda, silencio.
5. Avisa si el diff introduce o cae en flaky; no borra ni corrige — solo informa. Si no hay nada: `Sin hallazgos.`
