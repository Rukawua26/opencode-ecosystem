---
name: organic-workflow-lite
description: Flujo ODD para implementacion organica sustancial con un documento unico odd/tasks. Usar cuando una implementacion autorizada requiera dos o mas pasos significativos o progreso recuperable, sin activar SDD.
---

# organic-workflow-lite

1. **Autorizacion**: esta skill aplica solo a trabajo ya autorizado a mutar. Si la peticion es analizar, comparar, auditar o planificar, responde read-only y no crees el documento. Implementar autoriza editar codigo y tests y ejecutar verificacion local; NO autoriza rama nueva, commit, push, PR, merge ni deploy sin peticion explicita.

2. **Alcance aprobado**: explora primero (routing normal de AGENTS.md). Presenta en chat: objetivo, problema, alcance (incluye/excluye), restricciones y tareas con criterio de verificacion. Espera aprobacion humana antes de la primera linea de codigo; el usuario aprueba el alcance, no cada tarea.

3. **Documento unico**: crea `<proyecto>/odd/tasks/<feature>.md` con secciones: Objetivo; Problema y por que; Alcance; Restricciones; Tareas (`[ ]` con criterio); Decisiones aceptadas; Evidencia; Progreso (estado, ultima tarea, siguiente paso, bloqueos). Un solo documento por feature; no crees spec/plan/design ni espejes el documento en memoria (basta una linea con la ruta).

4. **Implementa tarea por tarea**: enruta cada una segun AGENTS.md (1-3 ficheros inline; 4+ delega exploracion; 2+ escrituras no triviales -> writer acotado). TDD solo si el proyecto o el usuario lo piden; si no, checks funcionales. Marca `[x]` unicamente con resultado observado y registra en Evidencia `comando -> salida breve`.

5. **Cambios de alcance**: los aceptados actualizan las tareas afectadas, conservan las validas y reabren las invalidadas con motivo. Hallazgos solos no expanden alcance; el nuevo negocio requiere autorizacion.

6. **Reanudacion**: al continuar una feature, lee el documento, contrasta con `git status`/diff y valida que la evidencia previa sigue vigente (en duda, repite el check). Continua la primera tarea pendiente; no reejecutes verificaciones intactas.

7. **Cierre**: reporta resultado verificado, checks fallidos o pendientes y siguiente paso. qa-gate al cierre; verificador independiente o lentes 4R solo si el riesgo del cambio lo justifica, nunca por checkbox.
