# Plan: SDD Prompt Optimization

## Objetivo

Adoptar los contratos A-D útiles sin atribuir al repositorio el ahorro upstream,
manteniendo los archivos SDD como fuente de verdad y evitando duplicación local.

## Estrategia

1. Rediseñar `sdd-phase-common.md`: secciones A-D + templates preservados.
2. Actualizar 4 SKILLs para referenciar A-D.
3. Sincronizar paquete npm e instaladores.
4. Restaurar el juez `review-risk` sin tools.
5. Anadir tests y verificar.

## Decisiones

- **Merge, no reemplazo**: conservar templates existentes + anadir A-D.
- **Seccion A via `opencode-skills --search`**: reutilizar `skills.js` sin refresh implícito.
- **Seccion D reconciliada**: un solo `Formato de salida` por fase.
- **Secciones B/C file-first**: memoria read-only para contexto durable; archivos para artefactos.
- **Medición honesta**: comparar bytes antes/después y no extrapolar el 63% upstream.
- **Sin `sdd-verify`**: YAGNI, `verify.md` + `review_verify` ya cubren.
- **Juez sin tools**: el expediente contiene todo el contexto; `permission: deny` elimina efectos laterales.

## Tareas

- [x] T1: Rediseñar `skills/sdd-phase-common.md` con A-D + templates preservados
- [x] T2: Actualizar `sdd-specify/SKILL.md` para referenciar A-D
- [x] T3: Actualizar `sdd-plan/SKILL.md` para referenciar A-D
- [x] T4: Actualizar `sdd-tasks/SKILL.md` para referenciar A-D
- [x] T5: Actualizar `sdd-implement/SKILL.md` para referenciar A-D
- [x] T6: Anadir `tests/sdd-phase-common.test.js`
- [x] T7: Sincronizar paquete npm e instaladores
- [x] T8: Verificar `npm test`, coverage, install Bash, lint, docs y doctor
- [x] T9: Registrar test PowerShell bloqueado por ausencia de `pwsh`
