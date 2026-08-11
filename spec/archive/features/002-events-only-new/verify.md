# Verify — Incremental Memory Event Export

Fecha: 2026-08-10 · Verificador: SDD verify independiente

## Veredicto

**PASS** — REQ-001..REQ-008 y los siete escenarios de aceptación cumplen. Las advertencias de los pases independientes fueron corregidas: prueba CLI para actualización pública con el mismo ID, IDs estables de preferencias, aliases de ruta, escrituras atómicas, lock exclusivo, límite por bytes, diagrama y tabla de archivos.

## Matriz de requisitos

| Requisito | Evidencia | Estado |
|---|---|---|
| REQ-001 Compatibilidad | Sin `knownEvents`, `exportEventsJsonl` conserva `listEvents`; pruebas previas y MCP sin cambios | PASS |
| REQ-002 Estado verificable | CLI usa `validateEventsJsonl` antes de escribir; archivo ausente produce `[]` | PASS |
| REQ-003 Delta correcto | `listChangedEvents` compara mapa `event_id → content_hash`; `savePreference` actualiza en sitio y conserva el ID | PASS |
| REQ-004 Límite post-dedup | Iteración SQL filtrada descarta conocidos antes del límite final; regresión `Oldest` con límite 1 | PASS |
| REQ-005 Idempotencia | Prueba CLI drena `Newest`, `Middle` y luego delta vacío sin repetir | PASS |
| REQ-006 Actualización segura | Delta y estado usan temp + rename, en ese orden; lock con PID recupera procesos muertos; corrupción deja ambos intactos | PASS |
| REQ-007 Privacidad | Filtro `is_private = 0` permanece por defecto; prueba CLI excluye decisión privada; MCP intacto | PASS |
| REQ-008 Recursos y rutas | 64 MiB antes de leer/escribir, máximo 10000 eventos y aliases por symlink/inode rechazados | PASS |

## Escenarios

| Escenario | Evidencia | Estado |
|---|---|---|
| 1 Primera exportación | CLI crea delta y estado desde archivo inexistente | PASS |
| 2 Idempotencia | Última corrida sin pendientes escribe delta vacío | PASS |
| 3 Conocidos antes del límite | Adapter y CLI encuentran evento antiguo detrás de conocidos | PASS |
| 4 Registro modificado | Adapter y CLI reemplazan la versión con mismo ID y hash nuevo | PASS |
| 5 Estado alterado | Hash inválido falla sin modificar salida o estado | PASS |
| 6 Privacidad | Estado y delta contienen solo la decisión pública | PASS |
| 7 Alias y concurrencia | Symlink al estado y lock activo fallan sin escribir | PASS |

## Comandos ejecutados

```text
node --test packages/memory-adapter/tests/*.test.js
→ 42 pass, 0 fail

npm test
→ 6 files, 49 pass

npm run lint
→ PASS

npm run test:install
→ PASS, 10/10 checks

npm run test:hooks
→ PASS, target-safe/idempotent/non-recursive

npm audit --omit=dev
→ found 0 vulnerabilities

git diff --check
→ PASS
```

## Riesgos residuales aceptados

- Un estado llega como máximo a 64 MiB/10000 eventos y requiere rotación explícita; el error indica cómo recuperarse y no se poda silenciosamente.
- Si falla el rename después de escribir el delta, la siguiente corrida puede repetir ese delta, pero no perderlo.
- Filas eliminadas en SQLite permanecen en el estado histórico; borrado y retención siguen fuera de alcance.

## Revisión independiente

El primer pase SDD verify dio `PASS WITH WARNINGS`. Las revisiones RDD detectaron churn de IDs, aliases, concurrencia y límites asimétricos; todos fueron corregidos antes de congelar el candidato final. Las pruebas dirigidas pasaron 42/42 y lint/diff-check permanecieron limpios.
