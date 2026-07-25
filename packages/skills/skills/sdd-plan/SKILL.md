---
name: sdd-plan
description: Produce a technical implementation plan from an approved project-local feature specification without changing code.
---

# SDD Plan

Convierte una especificacion existente en un plan tecnico local al proyecto actual.

## Cuando Usar

- Cuando ya exista `spec/features/<feature>/spec.md`.
- Cuando el usuario pida planificar una feature SDD antes de implementarla.

## Regla Principal

Lee solo la constitucion minima y la feature solicitada:

- `spec/constitution/working-agreement.md`
- `spec/constitution/tech-stack.md`
- `spec/features/<feature>/spec.md`

No cargues otras features salvo dependencia explicita.

## Flujo

### 1. Validar Entrada

- Confirma que existe `spec.md`.
- Si hay preguntas abiertas bloqueantes, pregunta antes de planificar.

### 2. Inspeccionar Codigo Minimo Necesario

- Usa busquedas dirigidas con Glob/Grep.
- Lee solo archivos relevantes al alcance.
- Evita exploraciones amplias si no hacen falta.

### 3. Crear `plan.md`

En `spec/features/<feature>/plan.md`, documenta:

- Enfoque tecnico
- Archivos a tocar
- Datos, APIs o configuracion involucrada
- Dependencias
- Estrategia de testing
- Verificacion contra alucinaciones
- Riesgos tecnicos
- Criterios que guian decisiones

### 4. Verificacion Contra Alucinaciones

Todo `plan.md` debe incluir:

```md
## Verificacion Contra Alucinaciones

- Confirmar que cada archivo listado existe antes de editarlo.
- Confirmar que cada tipo/schema usado coincide con el codigo real.
- Confirmar que no se agrega comportamiento fuera de los criterios de aceptacion.
- Confirmar con build, typecheck, tests o lectura post-cambio segun aplique.
```

### Condiciones De Salida Del Loop

- Incluir en cada `plan.md` un maximo de iteraciones por tarea (default: 3).
- Si una tarea no puede completarse dentro del limite, documentar en `verify.md` y escalar al humano.

## Restricciones

- No implementes codigo durante Plan.
- No amplíes el alcance de `spec.md` sin actualizar primero la spec.
- Si detectas que la spec es ambigua, detente y pide aclaracion.
- No planifiques sobre APIs, tipos o archivos que no hayas verificado en el codigo real.

## Output Esperado

```txt
SDD PLAN CREATED

Feature: spec/features/NNN-name/
Plan: spec/features/NNN-name/plan.md
Archivos previstos: X
Riesgos: X
Proximo paso: crear tasks con sdd-tasks
```
