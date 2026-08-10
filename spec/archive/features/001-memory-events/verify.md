# Verify — Memory Event Projection (verificación independiente)

Fecha: 2026-08-10 · Verificador: SDD verify (independiente del implementador)

## Resultado

**PASS** — Los 8 requisitos y los 5 escenarios de aceptación se cumplen. Las 9
tareas de `tasks.md` están marcadas `[x]`. No hay migración de esquema, no hay
dependencias runtime nuevas, no hay relays/firmas/tabla journal.

## Matriz de cumplimiento REQ-001..REQ-008

| Requisito | Evidencia | Estado |
|---|---|---|
| REQ-001 Compatibilidad | `git diff` vacío para `schema.sql` y `package.json` (deps `{}` intactas); APIs previas (search/getContext/getHistory/export/import) intactas; suites completas verdes | COMPLIANT |
| REQ-002 Proyección canónica | `toMemoryEvent` proyecta 5 fuentes con `event_id/kind/project/created_at/tags/content/content_hash`; verificado en runtime para `decision,bugfix,architecture,preference,operational` | COMPLIANT |
| REQ-003 Integridad | SHA-256 sobre `canonicalJson` (claves ordenadas recursivamente, `content_hash` excluido vía destructuring); doble proyección produce hash idéntico (`ee9a640c…`, `event_id` igual) | COMPLIANT |
| REQ-004 Filtros | `listEvents` filtra en SQLite (`project_id = ?`, `is_private = 0`, `created_at >= since`, `created_at <= until`, `ORDER BY … LIMIT ?`) antes de `toMemoryEvent`; el sort/merge global posterior solo recorta la unión | COMPLIANT |
| REQ-005 Privacidad | Default `includePrivate=false` + condición SQL; MCP `list_events`/`export_events` no exponen `includePrivate` y lo rechazan como argumento desconocido (verificado: `Unknown argument: includePrivate`); MCP sin tools de escritura; CLI permite opt-in local explícito `--include-private` | COMPLIANT |
| REQ-006 JSONL | Un evento por línea + salto final; `parseEventJsonl` valida cada línea y falla con número de línea (`invalid: JSONL line 1: invalid: event hash mismatch`); CLI `verify-events` exit 1 ante alteración | COMPLIANT |
| REQ-007 Referencias RDD | `normalizeEventTags` produce pares `[name, value]`; `feature:001,receipt:r1,lens:verifier,file:…` conservados sin tocar el esquema (test + runtime) | COMPLIANT |
| REQ-008 Límites | `eventLimit`: default 50, entero positivo obligatorio (0/-5 → error), tope 1000; MCP exige entero positivo y limita a 50; fechas no parseables, calendarios imposibles y rangos `since > until` rechazados | COMPLIANT |

## Escenarios de aceptación

| Escenario | Verificación | Estado |
|---|---|---|
| 1 Hash determinista | Doble `listEvents` → `JSON.stringify` idéntico, mismo `event_id` y `content_hash` | PASS |
| 2 Filtro kind/fecha/límite | Solo `decision`, dentro del rango, ≤ límite (runtime: 1 evento con `limit:1`) | PASS |
| 3 Privacidad MCP | MCP lista/exporta solo la pública; `includePrivate` rechazado | PASS |
| 4 Referencias RDD | Tags canónicos conservan `feature/receipt/lens/file/commit/test` | PASS |
| 5 JSONL alterado | Validación falla indicando la línea afectada | PASS |

## Comandos ejecutados (evidencia)

```text
node --test packages/memory-adapter/tests/*.test.js
→ tests 32, pass 32, fail 0

npm test
→ Test Files 6 passed, Tests 49 passed

npm run lint
→ pass (sin salida)

npm run build --workspace packages/memory-adapter
→ "No build step needed - native Node.js" (no-op documentado; sin TS que compilar)

npm run test:install && npm run test:hooks
→ PASS; instalación 10/10, hook target-safe/idempotente/no recursivo

npm audit --omit=dev
→ found 0 vulnerabilities
```

Verificación de runtime independiente (`/tmp/opencode/verify-001.mjs`):
- Determinismo: `E1 deterministic: true`, hash `ee9a640c…`, `event_id: decision:proj:1`
- Tamper: `invalid: JSONL line 1: invalid: event hash mismatch`
- Filtro+rango+límite: `Filtered count: 1`, `Invalid range rejected: invalid: since must be before until`, `Invalid limit rejected: invalid: limit must be a positive integer`
- Campos canónicos en las 5 fuentes: `All have canonical fields: true`

Verificación MCP (`/tmp/opencode/verify-001-mcp.mjs`):
- `includePrivate` → `Error: Unknown argument: includePrivate`
- `limit: 9999` → clamp a 50
- Export MCP solo devuelve la pública

CLI end-to-end (DB temporal):
- `export-events` → JSONL canónico con tags `[["feature","001"],["receipt","r1"],["lens","verifier"]]`
- `verify-events` → `[OK] Verified 1 events`
- Tras alterar contenido → `[ERROR] invalid: JSONL line 1: invalid: event hash mismatch`, exit 1

## Hallazgos corregidos

**A. Fechas y zonas horarias.** Se validan calendarios imposibles; timestamps SQLite
sin zona se interpretan como UTC, offsets explícitos se normalizan a UTC y un
`until` de solo fecha incluye el día completo. Todos los casos tienen tests.

**B. Límite MCP.** MCP convertía `limit: 0` a 1 mientras el adapter lo rechazaba.
Ahora ambos exigen un entero positivo; MCP mantiene únicamente el tope de 50.

**C. Defaults MCP sensibles.** La proyección completa incluía preferencias e
historial operacional por defecto. MCP limita ahora el default a decisiones,
bugs y arquitectura; preferencias/operaciones requieren `kind` explícito.

**D. Imports heredados.** Filas importadas sin `created_at` podían romper toda
la proyección. El import normaliza timestamps y asigna UTC actual cuando faltan.
Las bases antiguas que ya contienen `NULL` se proyectan con el sentinel
`1970-01-01 00:00:00` sin modificar la fila original.

**E. Cambio asociado `checkOllama()`.** El probe ahora ejecuta
`ollama embed --help` (no solo `ollama list`), evitando activar embeddings sin
soporte real. Verificado en código; coherente con el hallazgo del verify previo.

## Riesgos residuales

- El hash garantiza integridad de contenido, no autoría; firmas fuera de alcance.
- Sin retención/borrado automático (fuera de alcance por diseño).
- No hay prueba de carga con millones de filas; el límite 1000/50 mitiga el coste.

## Cumplimiento de tareas

`tasks.md`: 9 de 9 marcadas `[x]`, 0 pendientes. Archivos tocados: solo los
declarados en `plan.md` + 1 línea en `README.md` raíz. Sin cambios en
`schema.sql` ni `package.json`.
