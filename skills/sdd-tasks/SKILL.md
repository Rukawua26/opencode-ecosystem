---
name: sdd-tasks
description: Break an approved SDD plan into ordered, verifiable implementation tasks scoped to the active feature.
---

# SDD Tasks

Divide un plan tecnico SDD en tareas atomicas, ordenadas y verificables.

## Cuando Usar

- Cuando existan `spec.md` y `plan.md` para una feature.
- Antes de pasar a implementacion.

## Trigger

Activa esta skill cuando:

- El usuario pida dividir una feature SDD en tareas.
- Existan `spec/features/<feature>/spec.md` y `plan.md`, pero falte `tasks.md`.
- El usuario mencione `/tasks-spec`, `crear tasks`, `tareas SDD` o `breakdown`.

## Regla Principal

Trabaja solo con la feature solicitada en `spec/features/<feature>/`. No leas ni modifiques otras features salvo dependencia explicita.

## Flujo

### 1. Leer Artefactos

Lee:

- `spec/features/<feature>/spec.md`
- `spec/features/<feature>/plan.md`

### 2. Crear `tasks.md`

Cada tarea debe ser:

- Pequena
- Ordenada
- Verificable
- Limitada a un cambio claro
- Compatible con TDD cuando el plan lo pida: test esperado, implementacion minima y verificacion.

Formato recomendado:

```md
# Tasks: Feature Name

- [ ] 1. Preparar estructura o dependencias necesarias
- [ ] 2. Implementar comportamiento principal
- [ ] 3. Cubrir casos de borde
- [ ] 4. Agregar o actualizar tests
- [ ] 5. Ejecutar verificacion
- [ ] 6. Actualizar documentacion si aplica
```

Si la feature requiere TDD, usa este formato por comportamiento:

```md
- [ ] N. RED: agregar test que falla por [comportamiento]
- [ ] N. GREEN: implementar minimo para pasar el test
- [ ] N. REFACTOR: limpiar sin cambiar comportamiento
- [ ] N. VERIFY: ejecutar comandos definidos en `plan.md`
```

### 3. Crear `verify.md` Si No Existe

Inicializa el archivo para registrar verificacion posterior.

## Restricciones

- No implementes codigo durante Tasks.
- No crees tareas vagas como "mejorar codigo".
- Si una tarea no puede verificarse, reescribela.

## Output Esperado

```txt
SDD TASKS CREATED

Feature: spec/features/NNN-name/
Tasks: X
Verify file: spec/features/NNN-name/verify.md
Proximo paso: implementar con sdd-implement
```
