---
name: sdd-tasks
description: Break an approved SDD plan into ordered, verifiable implementation tasks scoped to the active feature.
---

# SDD Tasks

Divide `plan.md` en tareas atómicas, ordenadas y verificables. Aplica las secciones
A-D y plantillas de `../sdd-phase-common.md`.

## Cuándo usar / Trigger
- Existen `spec.md` y `plan.md`; falta `tasks.md`. Usuario pide dividir en tareas
  (`/tasks-spec`, `breakdown`).

## Flujo
1. **Leer**: `spec.md` + `plan.md` de la feature.
2. **Crear `tasks.md`**: cada tarea lleva checkbox y define un cambio pequeño, ordenado y
   verificable; usa TDD cuando aplique (RED/GREEN/REFACTOR/VERIFY).
3. **Crear `verify.md`** si no existe.

## Restricciones (específicas)
- No implementes código durante Tasks.
- No crees tareas vagas ("mejorar código"); si no verificable, reescríbela.

## Output
Usa el envelope de la sección D con encabezado `SDD TASKS CREATED`, número de tareas,
artefactos `tasks.md` y `verify.md`, y siguiente paso `sdd-implement`.
