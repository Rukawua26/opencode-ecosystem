# Acuerdos de trabajo

- El humano define el alcance, aprueba los planes y verifica los resultados finales. El agente ejecuta tacticamente: implementa, verifica y registra evidencia. (Fuente: /home/miguel/AGENTS.md, Rol Del Programador).
- No avanzar a implementacion sin un plan aprobado. (Fuente: /home/miguel/AGENTS.md, Rol Del Programador).
- Implementar una tarea por turno. (Fuente: ~/opencode-ecosystem/commands/implement-spec.md, descripcion y pasos 2 y 4; alcance explicito: spec/features/012-spec-constitution/spec.md, Alcance, y tasks.md, T1).
- Ciclo RDD: tras implementar, realizar una verificacion independiente unica; si hay rechazo, permitir como maximo una correccion acotada y su verificacion. Un segundo rechazo implica STOP y decision humana; no hay loop-until-clean. (Fuente: spec/features/011-routing-proporcional-rdd/verify.md, Ciclo RDD en /implement-spec).
- Fail-closed: si una decision humana es ambigua o no puede representarse fielmente, volver a preguntar; nunca inferir una alternativa. (Fuente: /home/miguel/AGENTS.md, Decisiones Y Revision).
- Evidencia-first: registrar el dictamen y la evidencia en verify.md al cerrar el lote. (Fuente: spec/features/011-routing-proporcional-rdd/verify.md, Resultado y SUGGESTION; /home/miguel/AGENTS.md, Spec-Driven Development).
