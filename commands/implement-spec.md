---
description: Implementa la siguiente tarea de tasks.md delegando en el subagente sdd-implement. Una tarea por turno.
---

1. Detecta la feature activa; si falta `tasks.md`, detente y sugiere `/tasks-spec`.
2. Toma UNICAMENTE la primera tarea pendiente `[ ]` de `tasks.md` y delega su implementacion al subagente `sdd-implement` (tool task, subagent_type sdd-implement) con contexto minimo: feature, tarea exacta, archivos objetivo. No hagas el trabajo inline.
3. Al volver el subagente, reporta su contrato de resultado (status, resumen, archivos, riesgos) y marca la tarea `[x]` solo si status es exito.
4. Espera aprobacion del usuario antes de delegar la siguiente tarea. No avances en cadena salvo modo auto acordado en el preflight.
