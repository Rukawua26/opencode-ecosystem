---
name: sdd-implement
description: Implement an approved project-local SDD feature task by task and verify it against its acceptance criteria.
---

# SDD Implement

Implementa una feature siguiendo `spec.md`, `plan.md` y `tasks.md` como ancla de verdad.

## Cuando Usar

- Cuando existan `spec.md`, `plan.md` y `tasks.md`.
- Cuando el usuario pida implementar una feature SDD.

## Trigger

Activa esta skill cuando:

- El usuario pida implementar una feature con spec existente.
- Existan `spec/features/<feature>/spec.md`, `plan.md` y `tasks.md`.
- El usuario mencione `/implement-spec`, `SDD implement`, `implementar spec` o `feature SDD`.

## Regla Principal

La spec manda. Si el alcance cambia, actualiza primero `spec.md` o `plan.md` antes de modificar codigo.

## Prompt Engineering Obligatorio

Antes de implementar, estructura el trabajo con los 5 ejes:

- Rol: actua como especialista del stack del proyecto actual.
- Contexto: usa solo la constitucion minima, la feature solicitada y los archivos listados en `plan.md`.
- Tarea: completa las tareas de `tasks.md` una por una.
- Restricciones: no amplíes alcance, no refactorices fuera del plan, no leas archivos no necesarios, no inventes comportamiento no especificado.
- Formato: actualiza progreso relevante en `tasks.md`, registra verificacion en `verify.md` y reporta archivos/comandos al final.

## Contexto Permitido

Lee solo:

- `spec/constitution/working-agreement.md`
- `spec/constitution/tech-stack.md`
- `spec/features/<feature>/spec.md`
- `spec/features/<feature>/plan.md`
- `spec/features/<feature>/tasks.md`
- Archivos de codigo directamente necesarios para las tareas actuales

No cargues otras features salvo dependencia explicita.

## Flujo

### 0. Entender

- Lee `spec.md` completo una vez para entender el objetivo global.
- Identifica el por que de la feature: que problema resuelve y que no debe cambiar.
- Lee solo los archivos de codigo que `spec.md`, `plan.md` o `tasks.md` referencian como necesarios.
- Si algo no esta claro, pregunta antes de implementar.
- No escribas codigo en esta fase; solo entiende y valida el alcance.

### 1. Preparar

- Confirma criterios de aceptacion.
- Carga tareas y marca progreso con la herramienta de tareas de sesion si el trabajo tiene varios pasos.

### 2. Implementar Por Tarea

- Ejecuta una tarea a la vez.
- Haz el cambio minimo correcto.
- No refactorices fuera del plan.
- Actualiza `tasks.md` al completar tareas si es util para persistir progreso.

### 2.4 TDD Opcional

Si el plan lo especifica o el usuario lo pide:

- Antes de implementar cada tarea, escribe el test que describe el comportamiento esperado.
- Verifica que el test falla por la razon esperada (RED).
- Implementa el codigo minimo para que pase (GREEN).
- Refactoriza solo si mantiene tests verdes y no amplia alcance.
- Usa la skill `tdd-workflow` como guia del ciclo RED/GREEN/REFACTOR.

### 2.5 Loop Auto-Correctivo

Si se necesita iterar, usa la skill `loop-engineering`. Max 3 iteraciones por tarea; tras 3 fallos, documentar como bloqueante en `verify.md`. En tests: corregir solo lo que falla. En types/lint/build: re-verificar hasta pasar.

### 2.6 Paso Anti-Alucinacion Obligatorio

Antes de marcar una tarea como completa:

- Lee los archivos modificados o las secciones relevantes para confirmar que el cambio existe.
- Compara el cambio con `spec.md`, `plan.md` y `tasks.md`.
- Verifica que no agregaste comportamiento fuera de los criterios de aceptacion.
- Verifica que los tipos, imports, nombres de archivos y APIs usadas existen en el codigo real.
- Si algo fue inventado o excede el alcance, corrige antes de continuar.

### 3. Verificar

- Ejecuta checks definidos en `plan.md`.
- Usa la skill `debug-bugs` para verificacion completa cuando aplique.
- Si el diff contiene `.tsx`, `.jsx`, `.html` o `.css`, incluye `accessibility-audit` como paso condicional.
- Registra resultado en `spec/features/<feature>/verify.md`.
- Incluye una seccion `Verificacion Anti-Alucinacion` en `verify.md` con evidencia de que los cambios coinciden con archivos reales y criterios de aceptacion.

### 3.5 Cross-Review via Subagente

Antes de cerrar, lanza un subagente revisor via Task tool con contexto limpio:

- **Skill**: code-reviewer-v2
- **Contexto minimo del subagente**:
  - `git diff` de los cambios actuales
  - `spec.md`, `plan.md`, `tasks.md` de la feature
  - Stack del proyecto (`tech-stack.md`)
- El subagente NO recibe informacion de como se implemento (contexto aislado)
- Devuelve findings ordenados por leverage (impacto ÷ esfuerzo × confianza)
- **Si hay findings CRITICAL**: corregir antes de cerrar, repetir cross-review
- **Si hay findings HIGH**: decidir si corregir o documentar como riesgo residual
- Registrar resultado en `verify.md` bajo seccion `Cross-Review Findings`
- Si la feature tiene 3+ capas, escala a multi-agent con rol Verificador dedicado

### 3.6 Reality-Check Gate

Evaluar resultados de verification-loop + cross-review:

- **Si todo PASS + sin CRITICAL findings + sin HIGH blockers**: AUTO-APPROVE. Humano no interviene.
- **Si CRITICAL findings**: PAUSAR. Corregir, re-ejecutar verificacion y cross-review.
- **Si HIGH findings sin CRITICAL**: Documentar en `verify.md` como riesgo residual. Dejar decision final para humano en PR.
- **Si WARN/INFO findings**: No bloquean. Documentar como observaciones.

Registrar decision en `verify.md` bajo seccion `Reality-Check`:
```
REALITY-CHECK: AUTO-APPROVED / NEEDS HUMAN
Reason: ...
Findings: X CRITICAL / Y HIGH / Z WARN
```

### 4. Cerrar

- Resume archivos modificados.
- Indica criterios de aceptacion validados.
- Lista pruebas/comandos ejecutados.

## Restricciones

- No implementes features que no esten en la spec.
- No ignores criterios de aceptacion fallidos.
- No ocultes fallos de tests; reportalos y corrige si esta dentro del alcance.

## Output Esperado

```txt
SDD IMPLEMENTATION COMPLETE

Feature: spec/features/NNN-name/
Tasks completed: X/Y
Verification: PASS/FAIL
Comandos ejecutados: ...
Archivos modificados: ...
```
