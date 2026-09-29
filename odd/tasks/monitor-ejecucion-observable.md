# Monitor de ejecucion observable

## Objetivo
Seguir tareas del runner en una vista En vivo y comparar resultados y tiempos por agente/fase sin afirmar observacion de sesiones interactivas.

## Problema y por que
El mapa muestra topologia; la tarjeta en Resumen no muestra los hitos internos y su boton de traza abre un panel oculto en Actividad. No hay datos de duracion de verificacion separados del agente.

## Alcance
Incluye checkpoints acotados del runner, endpoint de metricas agregadas basado en SQLite existente, vista dedicada con traza y refresco adaptativo ya existente. Excluye sesiones interactivas ajenas a la cola, SSE/WebSockets, automatizar acciones y calificar skills sin recibos.

## Restricciones
Python stdlib, sin migracion de esquema, sin stdout/prompts/comandos en eventos ni API nueva, localhost. No tocar memoria viva, receipts, backups ni logs.

## No romper
Contratos actuales de /api/tasks y /api/tasks/<id>/trace, estados del runner, cola atomica, panel Mapa/Resumen/Actividad/Ayuda y cambios de usuario ya presentes en index.html.

## TDD
Modo: off. Fuente: default. Runner: `python3 -m unittest discover -s control/tests`. Checks funcionales obligatorios.

## Tareas
- [x] T1: checkpoints de fase y tiempos seguros, corregir fase en reintentos; tests con DB efimera.
- [x] T2: metricas agregadas de tareas finalizadas y etapas instrumentadas, distinguir sin datos de cero; tests de API.
- [x] T3: vista En vivo con traza visible, hitos y metricas; tests frontend.
- [x] T4: verificar suite, skills, status, verify.sh y qa-gate; documentar limites.

## Criterios de aceptacion
- [x] En vivo muestra tarea activa o reposo, fase, duracion, timeline y motivo sin prometer detalle interno del modelo.
- [x] Las metricas por agente diferencian done/dead/waiting y tiempos observados; datos no disponibles no se muestran como exito o fallo.
- [x] Traza accesible tanto desde Resumen como desde la cola; no se exponen datos privados.
- [x] Suite obligatoria, status, verify y qa-gate verdes.

## Decisiones aceptadas
Polling existente de 5s activo, 30s reposo, 60s oculto; SSE solo si se demuestra insuficiencia. ODD de esta feature nuevo, no reutilizar las otras features del panel en curso.

## Reutilizacion investigada
Reusar `db.events_for_task`, `trace.build_trace`, `runner.record_event`, `server._json`, `renderLive`, `showTrace` y `scheduleTaskPoll`. El intento anterior de almacenar contadores por componente en snapshot se retiro porque confundia nombres de agente con tipos e inducia ceros falsos. No se crea esquema ni protocolo de streaming.

## Evidencia
T1-T4: Estado: passed. `python3 -m unittest discover -s control/tests`: 181 tests OK (1 skip E2E opt-in ajeno). Playwright E2E: 7/7 OK con servidor temporal. `python3 validate-skills.py skills`: 10 skills valid; `./opencode-ecosystem status`: `[ok] sin drift`; `./verify.sh`: `[ok] verify verde`; `scripts/qa-gate.sh --strict`: exit 0; `git diff --check`: limpio. Fallo inicial del navegador: 7 timeouts con servicio instalado anterior (endpoint nuevo = 404). Corregido en test E2E: ahora usa servidor y DB temporales, sin reiniciar servicio ni tocar DB instalada.

## Progreso
Estado: implementado, pendiente observacion real tras publicacion autorizada. Ultima tarea: T4. Siguiente: revision humana y decision de activacion del servicio instalado. Bloqueos: ninguno.
