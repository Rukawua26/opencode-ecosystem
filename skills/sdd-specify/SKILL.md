---
name: sdd-specify
description: Create a project-local feature specification with scope and acceptance criteria before implementing a complex change.
---

# SDD Specify

Convierte una idea de feature en una especificación técnica local al proyecto.
Aplica las secciones A-D y plantillas de `../sdd-phase-common.md`.

## Cuándo usar / Trigger
- Usuario pide feature nueva, cambio complejo o behavior contract; o menciona `spec`, `especifica`,
  `SDD`, `/spec`, `criterios de aceptación`.
- El cambio puede afectar contratos públicos, runtime crítico, datos persistidos o >1 capa.

## Flujo
1. **Detectar proyecto**: raíz por `package.json`, `pyproject.toml`, `Cargo.toml`, `.git`, `README.md`.
   Si no clara, pregunta.
2. **Estructura mínima** (si no existe): `spec/constitution/{mission,tech-stack,working-agreement,roadmap}.md`
   + `spec/features/README.md`. Placeholders claros, sin inventar.
3. **Feature**: `spec/features/NNN-feature-name/spec.md` (siguiente número, slug corto).
4. **Contenido de `spec.md`**: Objetivo, Usuario/caso, Alcance, Fuera de alcance, Límites de contexto,
   Fuentes de verdad, Criterios de aceptación verificables, Riesgos, Preguntas abiertas
   (usa las plantillas de `../sdd-phase-common.md`).

## Clarificación (opcional)
Ejecuta solo si la spec quedó con "Preguntas abiertas" o la autoauditoría no tiene
respuesta clara al alcance. Revisa `spec.md` como un QA, en una lista numerada, **sin
proponer soluciones todavía**:
- ambigüedades (términos o criterios con más de un significado);
- contradicciones entre requisitos;
- casos límite no cubiertos;
- conflictos con `spec/constitution/`.

Si hay hallazgos, resuélvelos en `spec.md` antes de cerrar; si no, se marca "sin hallazgos".

## Restricciones (específicas)
- No implementes código durante Specify.
- No leas specs de otras features salvo dependencia explícita.
- Deja preguntas abiertas en `spec.md` y pregunta si falta info crítica.

## Output
Usa el envelope de la sección D con encabezado `SDD SPEC CREATED`, artefacto
`spec/features/NNN-name/spec.md`, número de preguntas abiertas y siguiente paso `sdd-plan`.
