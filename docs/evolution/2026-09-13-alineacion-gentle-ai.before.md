# Baseline anterior a la alineacion gentle-ai

Esta excepcion conserva el comportamiento previo porque las mejoras se aplicaron antes
de iniciar el historial Git de `~/opencode-ecosystem`. No es contenido activo ni una
segunda fuente de verdad. Solo se usa para rollback durante el periodo de observacion.

## risk-lens

```markdown
1. `bash ~/.config/opencode/scripts/qa-gate.sh` (base: catch vacio, console.log).
2. `rg -n 'catch.*\{\}|\.catch\(\)|.edge.|TODO|FIXME' --no-heading -g '!*.bak-*'` sobre staged diff y archivos del PR.
3. `rg -n 'log\.\w+\(|fmt\.Error' -g '!*_test.go' -g '!*.bak-*'` — errores que nunca se verifican.
4. Reporta solo los hallazgos que correspondan al staged diff o cambio activo; ignora HeatMaps internos y archivos no tocados.
5. Si el hallazgo fue introducido por el candidato actual, notalo explicitamente. No genera correcciones.
```

## resilience-lens

```markdown
1. `bash ~/.config/opencode/scripts/qa-gate.sh` (base anti-slop).
2. Busca patrones:
   - `rg -n 'fetch|http\.|axios\.get|axios\.post' --no-heading` en staged/archivos del diff
   - `rg -n 'setTimeout|setInterval|sleep|delay' --no-heading` — sin timeout ni fallback
   - `rg -n 'retry|fallback|offline' --no-heading` — deberian existir en cambios de red, ausencia = riesgo
3. `risk` de red incompleto = informe persuasivo, no issue.
4. Solo si el cambio introduce dependencia de red nueva: reporta que falla al no poder inicializar, cargar o cancelar correctamente.
5. No bloquea; el revisor humano decide si es blocking o cosmetic.
```

## reliability-lens

```markdown
1. `bash ~/.config/opencode/scripts/qa-gate.sh` (base).
2. Busca en staged/archivos del diff:
   - `rg -n 'sleep|waitFor|setTimeout\(\s*\d+.,\s*[0-9]+\)' --no-heading -g '*test*' -g '*spec*'` — tiempo hardcodeado
   - `rg -n 'jest\.mock|vi\.mock|sinon|nock' --no-heading` — mocks que parecen implementaciones pero solo guardan tests propios
   - `rg -n 'expect\.\w+\(.*\)\.(and|or)\.' --no-heading` — aserciones no deterministas en el ANTES
   - `rg -n 'Date\.now\(\)|Math\.random' --no-heading` — no-determinismo
3. Marca si alguno es flaky o cambia comportamiento sin mockearlo correctamente.
4. Avisa si el diff introduce o cae en flaky; no borra ni corrige — solo informa.
5. No bloquea; el PR tiene merge protection, la lens solo anade evidencia como comentario.
```

## readability-lens

```markdown
1. `bash ~/.config/opencode/scripts/qa-gate.sh` (base).
2. Pistas mecanicas (no bloquean, solo avisan si el humano quiere mirar):
   - `rg -n '^\s{16,}' --no-heading -g '!*test*'` — sangria > 4 niveles (senal de complejidad)
   - `rg -n 'function [a-zA-Z_]+\s*\([^)]*\)\s*\{[^{}]*(?:{[^{}]*}){3,}' --multiline --no-heading -g '!*_test.*'` — funciones con 3+ bloques anidados
   - `rg -n 'let |var |const ' --no-heading | rg -v '(const|let|var) [a-z]'` — nombres cortos sin contexto (`d`, `res`, `tmp`)
3. `code-forge-fix-lite` nunca automatica; el agente recomienda `gofmt -w`/`prettier` si aplica, pero el humano decide.
4. Esto es un punto de partida de revision — indica donde mirar mas que que corregir.
```

## git-atomic-committer

```markdown
1. Solo crea commits si el usuario lo pide explicitamente.
2. Revisa `git status`, el diff completo y el log reciente antes de preparar grupos.
3. Stagea solo ficheros intencionados; nunca reviertas ni incluyas cambios ajenos.
4. Separa por unidad de trabajo. Infere el estilo de mensaje del `git log` del repo; usa Conventional Commits `tipo(alcance): mensaje` solo si el repo ya los usa, con task ID si existe.
5. No mezcles refactor y feature en el mismo commit.
```

## Regla global de autoría de skills

```markdown
- Al crear o modificar una skill de OpenCode, carga primero la built-in `customize-opencode`, edita `~/opencode-ecosystem/skills` antes que el runtime, valida con `python3 ~/opencode-ecosystem/validate-skills.py ~/opencode-ecosystem/skills`, sincroniza, ejecuta `opencode debug skill` y reinicia OpenCode. Manten coherencia de estilo con las skills existentes: espanol, descripcion "que hace + Usar cuando", cuerpo breve, sin acentos en el contenido. **Documenta todo cambio al ecosistema en `~/opencode-ecosystem/docs/evolution/` usando `_TEMPLATE.md`; el cambio debe ser mejor o igual que lo anterior (no regresion) y lo anterior no se borra hasta que el nuevo se verifique sin errores dentro de un periodo prudencial.**
```
