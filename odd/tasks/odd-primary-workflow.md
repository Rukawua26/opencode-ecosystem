# Feature: ODD primary workflow

## Objetivo

Convertir ODD en el unico flujo de desarrollo activo del ecosistema, conservando
implementacion delegada, verificacion independiente y reanudacion con evidencia.

## Problema y por que

ODD-lite ya es el flujo predeterminado, pero el ecosistema mantiene seis comandos,
dos subagentes y reglas globales SDD. Esto duplica filosofia y mantenimiento. El
runner, ademas, no distingue una tarea completada de una bloqueada cuando el agente
sale con codigo cero.

## Alcance

Incluye:
- agentes `odd-worker` y `odd-verifier`;
- runner con workflow ODD, salida `RESULT` y estado `waiting`;
- panel, flujo declarado y tests asociados;
- skills ODD/plan sin activacion SDD;
- piloto real antes de retirar comandos y agentes SDD;
- retirada del SDD activo conservando specs e historial legacy.

Excluye:
- sockets, IPC, plugins push o columnas de sesion;
- OpenSpec, Spec Kit, Engram, RDD nativo o telemetria nueva;
- borrar specs legacy, documentos de evolucion o registros antiguos;
- commit, push, PR o deploy.

## Restricciones

- Profundidad maxima 1: el worker no delega y el verifier es read-only.
- Sin migracion de esquema SQLite.
- No persistir stdout completo; solo resumen o pregunta acotados.
- El documento ODD es el portador de estado entre intentos.
- Fuente de verdad: `~/opencode-ecosystem`; validar, sincronizar y comprobar drift.

## TDD

- Modo: off
- Fuente: default
- Runner: `cd ~/opencode-ecosystem && python3 -m unittest discover -s control/tests`
- Checks funcionales y tests nuevos obligatorios, sin ciclo RED estricto.

## Tareas

- [x] T1 Crear `odd-worker` y `odd-verifier` en coexistencia temporal.
- [x] T2 Adaptar runner a ODD, `RESULT`, `SUMMARY`, `QUESTION` y `waiting`.
- [x] T3 Adaptar acciones: whitelist ODD y reintento de `waiting`.
- [x] T4 Adaptar panel para mostrar, filtrar y reintentar `waiting`.
- [x] T5 Sustituir el flujo SDD declarado por ODD delegado.
- [x] T6 Actualizar y ampliar tests del control-plane.
- [x] T7 Actualizar `organic-workflow-lite` y `ultraplan-lite`.
- [x] T8 Ejecutar piloto real de exito, verificacion y bloqueo.
- [x] T9 Retirar comandos/agentes/reglas SDD y verificar purga del runtime.
- [x] T10 Documentar evolucion, ejecutar higiene y cerrar evidencia.

## Decisiones aceptadas

- D1: no persistir sesiones en el runner; cada intento relee el documento ODD.
- D2: salida final `RESULT: success|blocked|failed`; ausencia mantiene compatibilidad
  y se interpreta como exito para agentes no ODD.
- D3: `waiting` reutiliza la accion de reintento tras registrar la decision en ODD.
- D4: `SUMMARY` y `QUESTION` se limitan a 200 caracteres; no se guarda transcripcion.
- D5: retirar SDD solo despues de un piloto ODD satisfactorio.
- D6: para el piloto de bloqueo T8, elegir estrategia ALFA.

## Evidencia

- T1: Estado: passed. `opencode debug config` proyecto ambos agentes ODD con
  modelo y permisos V2 normalizados.
- T2: Estado: passed. Suite cubre success, failed, blocked y parseo acotado.
- T3: Estado: passed. Test `test_retry_dead_or_waiting` verde.
- T4: Estado: passed. Smoke test Node del frontend verde en suite.
- T5: Estado: passed. Flow declarado sustituido por `odd-delegado`.
- T6: Estado: passed. `python3 -m unittest discover -s control/tests`: 87/87 OK.
- T7: Estado: passed. `python3 validate-skills.py skills`: 10/10 validas.
- T8: Estado: passed. Tasks #7/#8 completaron worker y verifier con marcador
  `ODD_PILOT_OK`; task #9 paso por `waiting` con attempts=0, se reencolo tras
  D6 y termino done; verifier #10 done rc=0.
- T9: Estado: passed. Runtime sin comandos Markdown, `opencode debug config`
  lista `odd-worker`, `odd-verifier` y `title`; `status` sin drift; grep activo
  sin referencias SDD.
- T10: Estado: passed. 88/88 tests, `verify.sh` verde, `qa-gate --strict` exit 0,
  `plugin_doctor.sh` sano, control doctor ok y servicio activo. Higiene recomienda
  prune de 4 backups y reset de observations; no aplicado por quedar fuera de alcance.

## Progreso

- Estado: en_observacion
- Ultima tarea: T10
- Siguiente paso: reiniciar OpenCode y observar tareas ODD reales durante 2 semanas
- Bloqueos: ninguno
