---
description: Implementa la siguiente tarea de tasks.md delegando en el subagente sdd-implement. Una tarea por turno.
---

1. Detecta la feature activa; si falta `tasks.md`, detente y sugiere `/tasks-spec`.
2. Toma UNICAMENTE la primera tarea pendiente `[ ]` de `tasks.md` y delega su implementacion al subagente `sdd-implement` (tool task, subagent_type sdd-implement) con contexto minimo: feature, tarea exacta, archivos objetivo. No hagas el trabajo inline.
3. Al volver el subagente con status exito, invoca al subagente `sdd-verify` (subagent_type sdd-verify) UNA sola vez para contrastar la tarea implementada con spec.md y criterios; reporta su dictamen (hallazgos con evidencia o `Sin hallazgos.`). Si verifica con hallazgos, permite UNA correccion acotada repitiendo el ciclo (sdd-implement -> sdd-verify); un segundo rechazo = STOP y decision humana. No hay loop-until-clean.
4. Marca la tarea `[x]` en tasks.md solo si la verificacion pasa. Espera aprobacion del usuario antes de delegar la siguiente tarea. No avances en cadena salvo modo auto acordado en el preflight.
