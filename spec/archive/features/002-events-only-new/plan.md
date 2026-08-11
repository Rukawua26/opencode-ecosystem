# Plan — Incremental Memory Event Export

## Decisión

Adaptar `nak --only-missing` como reconciliación local entre la proyección actual y un JSONL acumulado. SQLite permanece como fuente de verdad y el estado solo registra qué versiones ya fueron exportadas.

## Archivos

| Archivo | Cambio |
|---|---|
| `packages/memory-adapter/src/memory-events.js` | Serializar y combinar estados por `event_id` |
| `packages/memory-adapter/src/adapter.js` | Listar eventos nuevos/modificados antes del límite final |
| `packages/memory-adapter/src/cli.js` | Opción `--state`, salida delta y reemplazo atómico |
| `packages/memory-adapter/tests/adapter.test.js` | Regresiones de límite y actualización por hash |
| `packages/memory-adapter/tests/cli.test.js` | Roundtrip, corrupción, privacidad y archivos |
| `packages/memory-adapter/tests/memory-events.test.js` | Merge y serialización determinista del estado |
| `packages/memory-adapter/README.md` | Contrato y ejemplos incrementales |
| `README.md` | Resumen de snapshots y deltas verificables |
| `docs/architecture/memory-events.mmd` | Rama incremental del grafo |
| `spec/features/002-events-only-new/*` | Requisitos, plan, tareas y evidencia |

## Diseño

1. El CLI valida el estado existente con `parseEventJsonl`; un archivo ausente equivale a `[]`.
2. El adapter crea un mapa `event_id → content_hash` y recorre filas ya filtradas por SQL.
3. Cada kind conserva como máximo `limit` candidatos cambiados; el merge global ordena y recorta al límite.
4. `savePreference` actualiza la fila existente para mantener estable el ID; comparar también el hash detecta la nueva versión.
5. Delta y estado se reemplazan atómicamente, en ese orden, bajo un lock exclusivo con PID para recuperar locks de procesos muertos.
6. Rutas existentes se comparan por dispositivo/inode además de su ruta canónica para rechazar symlinks y hardlinks.
7. El tamaño del estado se valida simétricamente antes de leerlo y escribirlo; sin `--state`, `exportEventsJsonl` usa exactamente el camino de snapshot existente.

## Alternativas rechazadas

- **Filtrar después del `LIMIT` actual:** eventos conocidos recientes ocultarían pendientes antiguos.
- **`NOT IN` solo por ID:** perdería actualizaciones de filas mutables con el mismo `event_id`.
- **Nueva tabla/watermark SQLite:** añade persistencia y migración para un estado que ya cabe en JSONL.
- **`--since` automático:** los límites temporales pueden solaparse o perder eventos con timestamps heredados.
- **Importar JSONL:** exige una proyección inversa y una segunda semántica de escritura.

## Riesgos y mitigaciones

- Estado corrupto: validar todo antes de escribir.
- Interrupción durante escritura: temp en el mismo directorio + rename atómico para ambos archivos.
- Salida y estado iguales: ruta canónica + dispositivo/inode.
- Estado grande: 64 MiB antes de leer y máximo de 10000 eventos, con error de rotación accionable y sin poda silenciosa.
- Ejecuciones concurrentes: lock exclusivo local; un lock existente falla sin escribir.
- Scan sin cambios: iteración SQLite, no carga completa en RAM.
- Privacidad: conservar filtros previos y no exponer la opción por MCP.

## Verificación

- `node --test packages/memory-adapter/tests/*.test.js`
- `npm test`
- `npm run lint`
- `npm run test:install`
- `npm run test:hooks`
- `npm audit --omit=dev`
- Matriz REQ-001..REQ-008 en `verify.md`.
