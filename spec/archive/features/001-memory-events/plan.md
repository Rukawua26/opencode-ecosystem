# Plan — Memory Event Projection

## Decisión

Implementar una proyección JavaScript sobre las tablas existentes. SQLite sigue siendo la fuente de verdad; no hay migración ni doble escritura.

## Archivos

| Archivo | Cambio |
|---|---|
| `packages/memory-adapter/src/memory-events.js` | Serialización canónica, tags, proyección, hash y validación JSONL |
| `packages/memory-adapter/src/adapter.js` | Consultas SQL filtradas, `listEvents`, export y validación |
| `packages/memory-adapter/src/mcp-server.js` | Tools read-only `list_events` y `export_events` |
| `packages/memory-adapter/src/cli.js` | Comandos `export-events` y `verify-events` |
| `packages/memory-adapter/tests/*.test.js` | Escenarios de aceptación y regresión |
| `packages/memory-adapter/README.md` | Contrato y ejemplos |
| `docs/architecture/memory-events.mmd` | Grafo de la proyección |

## Diseño

1. Cada tabla se consulta con SQL específico y columnas explícitas.
2. Los registros se proyectan a un objeto común.
3. Los tags de texto se normalizan como arrays `[name, value]`.
4. El hash se calcula con `node:crypto`; no se añaden dependencias.
5. Los resultados se ordenan globalmente por fecha descendente y se recortan al límite.
6. MCP nunca habilita `includePrivate`.

## Alternativas rechazadas

- **Tabla `memory_events`:** duplica datos y exige migración/doble escritura.
- **Vista SQL compleja:** acopla formatos heterogéneos y hash a SQLite.
- **Firmas Nostr:** gestión de claves sin necesidad local demostrada.
- **Filtrado completo en JS:** cargaría más filas y consumiría RAM/tokens.

## Riesgos

- Tags históricos inconsistentes: normalización tolerante y determinista.
- Fechas inválidas: validación antes de SQL.
- Exports grandes: límite máximo y escritura explícita por CLI.
- Privacidad: exclusión por defecto y MCP sin override.

## Verificación

- `node --test packages/memory-adapter/tests/*.test.js`
- `npm test` para regresión del monorepo.
- `npm run lint`.
- Matriz requisito → evidencia en `verify.md`.
