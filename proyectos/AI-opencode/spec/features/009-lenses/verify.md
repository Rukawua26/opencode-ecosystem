# 009-lenses — verify.md (2026-09-11)

## Evidencia
1. **Validador**: 9 skills válidas (5 core + 4 lens) — nombre regex, description trigger, cuerpo no vacío.
2. **Runtime**: `opencode debug skill` carga las 9 propias una sola vez desde `skills/`, más `customize-opencode` integrada, total 10.
3. **Ecosistema**: `sync --apply` OK, `status sin drift`, `verify.sh` verde.
4. **AGENTS.md**: actualizado — 9 skills, regla de cuándo usar cada lens, y que todas son informativas (ninguna bloquea).

## Errores encontrados y corregidos
1. `validate-skills.py` devolvió "Permiso denegado" al ejecutarlo directamente; es un script Python, necesita `python3` o ejecutable explícito.
2. Las 4 skills lens pasaron el validador sin errores — diseño pre-validado en la discusión de plan.

## Estado de la filosofía
- 0 dependencias nuevas, 0 binarios, 0 plugins TUI.
- Máximo ~200 tokens adicionales en contexto por las 4 descripciones.
- `readability-lens` nunca automatiza juicio humano (diseño, no bug).
- `risk/resilience/reliability` informan candidatos; el humano decide si es issue o no.
