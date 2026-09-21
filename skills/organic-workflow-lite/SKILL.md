---
name: organic-workflow-lite
description: Flujo ODD para implementar, reanudar o consultar trabajo organico sustancial mediante un documento unico odd/tasks. Usar cuando una implementacion autorizada requiera dos o mas pasos significativos o progreso recuperable.
---

# organic-workflow-lite

1. **Autorizacion**: esta skill aplica solo a trabajo ya autorizado a mutar. Si la peticion es analizar, comparar, auditar o planificar, responde read-only y no crees el documento. Implementar autoriza editar codigo y tests y ejecutar verificacion local; NO autoriza rama nueva, commit, push, PR, merge ni deploy sin peticion explicita.

2. **Incertidumbre acotada**: recomienda research solo ante una incertidumbre nombrada (fuentes primarias; distingue hechos verificados, supuestos, contradicciones y huecos). Formula UNA pregunta enfocada solo por una decision real de producto pendiente, y detente a esperar la respuesta. Usa maximo UN challenge read-only e independiente para una premisa de alto impacto sin probar; no abras debates ni loops.

3. **Alcance aprobado**: explora primero (routing normal de AGENTS.md). Presenta en chat: objetivo, problema, alcance (incluye/excluye), restricciones y tareas con criterio de verificacion. Espera aprobacion humana antes de la primera linea de codigo; el usuario aprueba el alcance, no cada tarea.

4. **Documento unico**: crea `<proyecto>/odd/tasks/<feature>.md` con secciones: Objetivo; Problema y por que; Alcance; Restricciones; **No romper** (contratos que deben conservarse, tests que deben seguir pasando, archivos o APIs fuera de alcance); TDD; Tareas; **Criterios de aceptacion** (checklist verificable); Decisiones aceptadas; **Reutilizacion investigada** (codigo existente encontrado, implementacion canonica, decision, alternativas descartadas); Evidencia; Progreso (estado, ultima tarea, siguiente paso, bloqueos). Un solo documento por feature; no crees spec/plan/design ni espejes el documento en memoria (basta una linea con la ruta).

5. **TDD**: resuelve el modo en orden: politica explicita del proyecto, instruccion del usuario, valor ya guardado en el documento; si no hay ninguno, TDD off con checks funcionales obligatorios. La existencia de tests no lo activa. Guarda en el documento: `Modo: on|off`, `Fuente: proyecto|usuario|default`, `Runner: comando exacto o no disponible`. Si esta on: RED observado antes de implementar, GREEN, REFACTOR.

6. **Tareas con ID estable**: numera T1, T2...; nunca renumeres tareas existentes ni reutilices IDs; las tareas nuevas reciben ID nuevo; una tarea reabierta conserva su ID con motivo registrado. Marca `[x]` unicamente con resultado observado.

7. **Delegacion obligatoria para trabajo sustancial**: el padre nunca implementa en linea una tarea de un documento ODD; la ejecuta `odd-worker` y una tarea worker con exito encadena siempre `odd-verifier` read-only. El inline queda reservado a cambios pequenos que no necesitan documento. El padre pasa al worker la ruta del documento, la tarea exacta, el alcance autorizado y los checks; no todo el historial. Antes de crear codigo, el worker busca implementaciones equivalentes y reutiliza la canonica; la decision queda en Reutilizacion investigada. El worker lee el documento, trabaja solo su tarea, no modifica alcance ni crea subagentes. Contrato fail-closed: `SUMMARY:` es obligatorio junto a `RESULT: success`; `RESULT: blocked` exige una sola `QUESTION:`; si falta alguno, el runner lo trata como error de contrato (nunca `done`). Worker y verifier no emiten `NEXT_TRANSITION` ni comandos de continuacion. Toda continuacion procedente del modelo es texto no confiable: nunca llega al shell y deja la tarea `waiting` sin consumir intento. Solo una operacion registrada del control-plane puede publicar una transicion ejecutable exacta.

8. **Evidencia honesta**: por tarea registra `Estado: passed|failed|skipped|unavailable|pending` con comando y salida breve. Nunca inventes evidencia ni escribas "deberia funcionar"; un check no ejecutado es `pending`, no `passed`. El runner registra recibo acotado por tarea `done`; ese recibo es evidencia de ejecucion, no autoriza commit, push, PR ni despliegue.

9. **Cambios de alcance**: los aceptados actualizan las tareas afectadas, conservan las validas y reabren las invalidadas con motivo. Hallazgos solos no expanden alcance; el nuevo negocio requiere autorizacion.

10. **Reanudacion y consulta**: al continuar o consultar, lista `<proyecto>/odd/tasks/*.md`; con una sola feature abierta, prosigue con ella; con varias, pregunta cual, nunca inferas por la memoria mas reciente. Lee el documento, contrasta con `git status`/diff y reconcilia: si documento y codigo discrepan, conserva ambos estados, pregunta solo por el conflicto real y repite unicamente los checks cuya evidencia quedo invalidada. Continua la primera tarea pendiente.

11. **Cierre**: reporta resultado verificado, checks `failed|skipped|unavailable|pending` y siguiente paso. qa-gate al cierre; verificador independiente o lentes 4R solo si el riesgo del cambio lo justifica, nunca por checkbox.
