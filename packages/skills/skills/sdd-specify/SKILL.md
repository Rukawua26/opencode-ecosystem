---
name: sdd-specify
description: Create a project-local feature specification with scope and acceptance criteria before implementing a complex change.
---

# SDD Specify

Convierte una idea de feature en una especificacion tecnica local al proyecto actual.

## Cuando Usar

- Cuando el usuario pida crear una feature nueva o cambio complejo con SDD.
- Cuando diga "spec", "especifica", "SDD" o quiera definir el alcance antes de implementar.

## Trigger

Activa esta skill cuando:

- El usuario pida una nueva feature, cambio complejo o behavior contract.
- El usuario mencione `spec`, `especifica`, `SDD`, `/spec` o `criterios de aceptacion`.
- El cambio pueda afectar contratos publicos, runtime critico, datos persistidos o mas de una capa.

## Regla Principal

Las specs son locales por proyecto. Trabaja siempre en `./spec/` relativo al directorio del proyecto actual. No uses ni crees una carpeta global de specs.

## Flujo

### 1. Detectar Proyecto

- Verifica el directorio actual y archivos de proyecto relevantes.
- Si no estas en la raiz de un proyecto, busca una raiz razonable por archivos como `package.json`, `pyproject.toml`, `Cargo.toml`, `.git`, `README.md`.
- Si no puedes identificar el proyecto, pregunta antes de crear archivos.

### 2. Crear Estructura Minima

Si no existe, crea:

```txt
spec/
  constitution/
    mission.md
    tech-stack.md
    working-agreement.md
    roadmap.md
  features/
    README.md
```

No rellenes constitucion con informacion inventada. Usa placeholders claros cuando falten datos.

### 3. Crear Feature

Crea una carpeta numerada bajo `spec/features/`:

```txt
spec/features/001-feature-name/spec.md
```

Usa el siguiente numero disponible. El slug debe ser corto, en minusculas y con guiones.

### 4. Contenido De `spec.md`

Incluye:

- Objetivo
- Usuario / caso de uso
- Alcance
- Fuera de alcance
- Limites de contexto
- Fuentes de verdad
- Criterios de aceptacion verificables
- Riesgos
- Preguntas abiertas

### 5. Limites De Contexto

Toda spec debe declarar explicitamente que contexto puede cargarse:

```md
## Limites De Contexto

- Leer solo: [archivos/directorios necesarios]
- No leer: [directorios que aumentan tokens sin aportar]
- Si la implementacion requiere mas contexto, actualizar esta seccion antes de continuar.
```

### 6. Fuentes De Verdad

Toda spec debe listar fuentes verificables para mitigar alucinaciones:

```md
## Fuentes De Verdad

- [Tipos/schemas/contratos que validan datos]
- [Archivos existentes que definen comportamiento]
- [Docs o AGENTS.md relevantes]
- [Comandos de build/test que validan el resultado]
```

## Restricciones

- No implementes codigo durante Specify.
- No leas specs de otras features salvo dependencia explicita.
- Si falta informacion critica, deja preguntas abiertas en `spec.md` y pregunta al usuario.
- Mantén la especificacion concreta y verificable.
- No afirmes comportamiento tecnico sin fuente de verdad verificable.

## Output Esperado

```txt
SDD SPEC CREATED

Feature: spec/features/NNN-name/
Spec: spec/features/NNN-name/spec.md
Preguntas abiertas: X
Proximo paso: planificar con sdd-plan
```
