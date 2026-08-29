# Spec: SDD Prompt Optimization

## Problema

El commit `420555a` de `gentle-ai/beta/token-optimization` reduce duplicación
entre fases SDD, pero su ahorro estimado de ~12,900 tokens por sesión pertenece
al stack upstream y no es transferible directamente: este repositorio ya usa un
archivo común. Falta adoptar solo los contratos útiles sin duplicar el envelope,
inventar escrituras de memoria ni aumentar innecesariamente los prompts de fase.

## Alcance

- Reescribir `skills/sdd-phase-common.md` con secciones A-D:
  - A: Skill Loading (via `.skills-index.json` existente)
  - B: Artifact Retrieval (archivos canónicos + contexto durable read-only)
  - C: Artifact Persistence (archivos canónicos + captura durable explícita)
  - D: Return Envelope (reconciliada con `Formato de salida` existente)
- Preservar templates: Limites De Contexto, Fuentes De Verdad,
  Verificacion Contra Alucinaciones, Condiciones De Salida Del Loop, Anti-alucinacion.
- Actualizar `sdd-specify/SKILL.md`, `sdd-plan/SKILL.md`,
  `sdd-tasks/SKILL.md`, `sdd-implement/SKILL.md` para referenciar A-D.
- Sincronizar las cinco copias del paquete npm y desplegar el archivo común en
  instaladores Bash/PowerShell.
- Restaurar `review-risk` como juez sin tools para ejecutar el Juicio Dual documentado.
- Anadir tests en `tests/sdd-phase-common.test.js`.

## Fuera de Alcance

- `sdd-verify`, `sdd-continue`, `sdd-ff`, `sdd-archive` (YAGNI)
- Engram, `mem_search`/`mem_get_observation`/`mem_save`
- Cualquier componente de gentle-ai
- Cambios en `spec/constitution/`
- Nuevas dependencias
- TUI, orquestación multi-agente general o CLI de gentle-ai

## Requisitos

### R1 - Secciones A-D presentes

`sdd-phase-common.md` MUST tener las secciones A (Skill Loading),
B (Artifact Retrieval), C (Artifact Persistence) y D (Return Envelope).
La sección A MUST reutilizar `opencode-skills --search`. Las secciones B/C MUST
mantener los archivos SDD como fuente de verdad y MUST tratar las tools MCP de
`memory-adapter` como read-only.

### R2 - Templates preservados

Los templates existentes (Limites De Contexto, Fuentes De Verdad,
Verificacion Contra Alucinaciones, Condiciones De Salida Del Loop,
Anti-alucinacion) MUST conservar su comportamiento.

### R3 - Reconciliacion de envelope

La seccion D (Return Envelope) MUST reconciliarse con el `Formato de
salida (envelope)` existente en `sdd-phase-common.md`. MUST haber
exactamente un contrato de salida por fase.

### R4 - SKILLs actualizadas

Cada una de las 4 SKILLs (sdd-specify, sdd-plan, sdd-tasks, sdd-implement)
MUST referenciar las secciones A-D de `sdd-phase-common.md`.

### R5 - Tests

`tests/sdd-phase-common.test.js` MUST verificar:
- Presencia de secciones A-D en `sdd-phase-common.md`.
- Presencia de templates existentes.
- Cada SKILL referencia `../sdd-phase-common.md` o `sdd-phase-common`.
- No duplicacion de los campos comunes del envelope en las cuatro SKILLs.
- Ausencia de escrituras ficticias mediante tools read-only de `memory-adapter`.
- Paridad byte-a-byte entre fuente y paquete npm, más instalación del archivo común.

### R6 - Frontmatter valido

Cada SKILL MUST seguir el patron `--- name: ... description: ... ---`.

## Criterios de aceptacion

- AC1: `sdd-phase-common.md` tiene secciones A-D + templates preservados.
- AC2: 4 SKILLs referencian A-D sin duplicar los campos comunes del envelope.
- AC3: La medición local antes/después queda documentada, no atribuye el ahorro upstream al repo local y limita la sobrecarga combinada al 5%.
- AC4: `npm test` pasa completo.
- AC5: Coverage >= 93% statements.
- AC6: `npm run lint` y `npm run check-docs` sin hallazgos.
- AC7: `opencode-doctor --json` todos checks requeridos pasan.
- AC8: `review-risk` no dispone de tools y conserva un contrato de salida único.
