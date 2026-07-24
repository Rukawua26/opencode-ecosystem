# Multiagent Orchestrator

Orquesta subagentes especializados solo cuando el aislamiento de contexto reduce riesgo o carga cognitiva.

## Cuando Usar

- Feature que cruza 3+ capas: frontend, backend, datos, infra o runtime critico.
- Cambio que introduce logica de negocio nueva en cualquier capa.
- Modificacion de contratos publicos, schemas de datos o logica transaccional.
- Revision independiente de cambios sensibles.
- Investigacion amplia que conviene aislar del hilo principal.

## Cuando No Usar

- Cambio de un solo archivo o una sola funcion.
- Fix mecanico con verificacion clara.
- Repos runtime critico donde el humano debe validar cada decision antes de implementar.

## Roles

- Coordinador: reparte trabajo, mantiene el alcance y no escribe codigo si delega.
- Implementador: ejecuta una tarea atomica siguiendo spec/plan/tasks.
- Verificador: valida resultado con tests, diff y criterios de aceptacion.

## Flujo

### 1. Decidir Si Escalar

- Escala solo si la feature cruza 3+ capas o requiere revision independiente.
- Limite recomendado: maximo 3 subagentes por feature.

### 2. Preparar Contexto Minimo

Cada subagente recibe solo:

- Objetivo de la tarea.
- Archivos especificos a leer.
- Criterios de aceptacion.
- Comandos de verificacion.
- Restricciones de no tocar fuera de alcance.

### 3. Delegar

- Usa Task tool con tipo de agente especializado.
- Pide un unico mensaje final con hallazgos, archivos tocados y evidencia.
- No dupliques el trabajo delegado en el hilo principal.

### 4. Integrar

- Revisa el resultado del subagente contra la spec.
- Si hay codigo, corre verificacion local antes de cerrar.
- Registra decisiones relevantes en memoria/verify.md.

## Output Esperado

```txt
MULTIAGENT PLAN

Use multiagent: YES/NO
Reason: ...
Agents: Coordinator / Implementer / Verifier
Context per agent: ...
Exit condition: ...
```
