---
name: reliability-lens
description: 4R Reliability lens. Usar cuando el diff toca tests o codigo con estado/tiempo, para detectar flakiness, mocks fragiles y aserciones no deterministas.
---

# reliability-lens
Lens persuasivo: informa, nunca bloquea. Solo para tests o código que afecte estabilidad.

1. Base del barrido: `F=$(git diff --cached --name-only; git diff --name-only | sort -u)`. Un unico barrido sobre esos ficheros.
2. `bash ~/.config/opencode/scripts/qa-gate.sh` (base).
3. Busca solo en `$F`:
   - `rg -n 'sleep|waitFor|setTimeout\(\s*\d+.,\s*[0-9]+\)' $F --no-heading -g '*test*' -g '*spec*'` — tiempo hardcodeado
   - `rg -n 'jest\.mock|vi\.mock|sinon|nock' $F --no-heading` — mocks que parecen implementaciones pero solo guardan tests propios
   - `rg -n 'Date\.now\(\)|Math\.random' $F --no-heading` — no-determinismo
4. Puerta de precision: marca flaky solo con evidencia concreta; ante la duda, silencio.
5. Avisa si el diff introduce o cae en flaky; no borra ni corrige — solo informa. Si no hay nada: `Sin hallazgos.`
