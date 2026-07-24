# Working Agreement

## Principios

1. **Spec es la ancla de verdad**: si cambia el alcance, actualizar spec antes de tocar codigo
2. **Implementar feature por feature**: una a la vez, verificar contra criterios de aceptacion
3. **Human in the loop**: el humano aprueba, el agente ejecuta
4. **No avanzar sin plan aprobado**: para features pequenas, iterar respetando criterios
5. **Si escala a runtime critico, pausar y preguntar**

## Multiagentes

- **Coordinador**: reparte trabajo, mantiene alcance, no escribe codigo si delega
- **Implementador**: subagente con contexto aislado, ejecuta tarea atomica
- **Verificador**: valida resultado con tests, diff y criterios

Reglas:
- Profundidad maxima: 1 nivel
- Maximo 3 subagentes por feature
- No usar multiagentes para fixes de un archivo

## Memoria

- Guardar decisiones, bugs, arquitectura y preferencias
- NO guardar chat completo
- Usar `isPrivate` para datos sensibles
- Buscar contexto al inicio de sesion

## Token Economy

- Subagentes en hoja en blanco
- Skills cargadas por necesidad
- Multi-modelo por fase
- Compaction con prune
