# Feature 002 — Incremental Memory Event Export

## Objetivo

Exportar únicamente eventos nuevos o modificados respecto a un estado JSONL local, sin depender de fechas manuales, duplicar SQLite ni añadir servicios o dependencias.

## Requisitos

### REQ-001 — Compatibilidad

`export-events` MUST conservar el snapshot completo y su salida actual cuando no recibe `--state`.

### REQ-002 — Estado verificable

Con `--state`, el sistema MUST aceptar un archivo JSONL acumulado, MUST validar cada hash antes de usarlo y MUST tratar un archivo inexistente como estado vacío.

### REQ-003 — Delta correcto

El sistema MUST exportar un evento si su `event_id` no existe en el estado o si el mismo `event_id` tiene un `content_hash` diferente.

Las actualizaciones de preferencias MUST conservar su ID persistente para que una nueva versión reemplace a la anterior en el estado.

### REQ-004 — Límite después de deduplicar

El sistema MUST aplicar proyecto, kind, fecha y privacidad en SQLite, pero MUST aplicar el límite final después de descartar eventos sin cambios. Eventos conocidos recientes MUST NOT ocultar eventos antiguos todavía no exportados.

### REQ-005 — Idempotencia

Cuando una ejecución no deje eventos pendientes dentro del filtro y límite solicitados, repetirla sin cambios MUST producir un delta vacío. Si quedan más pendientes que el límite, ejecuciones sucesivas MUST drenarlos sin repetir los ya exportados.

### REQ-006 — Actualización segura

El sistema MUST reemplazar primero el delta de forma atómica y MUST reemplazar el estado de forma atómica solo después de una salida exitosa. Un estado inválido MUST NOT modificar la salida ni el estado. Ejecuciones concurrentes sobre el mismo estado MUST ser rechazadas mediante un lock local y un lock cuyo PID ya no exista MUST recuperarse automáticamente.

### REQ-007 — Privacidad

Las decisiones privadas MUST seguir excluidas por defecto. La nueva opción MUST permanecer solo en CLI local y MUST NOT ampliar el contrato MCP.

### REQ-008 — Límites de recursos

El estado MUST conservar como máximo 10000 eventos verificados y MUST rechazarse antes de leer o escribir si supera 64 MiB. El sistema MUST rechazar que `--state` y `--out` designen el mismo archivo por ruta, symlink o hardlink.

## Escenarios de aceptación

### Escenario 1 — Primera exportación

Given un estado inexistente y memoria con eventos públicos
When se ejecuta `export-events --state state.jsonl`
Then el delta contiene los eventos y el estado queda creado con los mismos eventos.

### Escenario 2 — Segunda exportación idempotente

Given un estado actualizado y memoria sin cambios
When se repite la exportación
Then el delta queda vacío y el estado permanece válido.

### Escenario 3 — Conocidos antes del límite

Given eventos recientes ya conocidos y un evento antiguo ausente
When se exporta con `--limit 1`
Then el delta contiene el evento antiguo ausente.

### Escenario 4 — Registro modificado

Given un evento cuyo `event_id` ya existe en el estado
When cambia su contenido y se exporta de nuevo
Then el delta contiene la nueva versión y el estado reemplaza la anterior.

La actualización MUST realizarse mediante la API pública `savePreference`, no mediante SQL directo de prueba.

### Escenario 5 — Estado alterado

Given un estado con contenido modificado sin recalcular el hash
When se intenta exportar
Then el comando falla y no modifica ningún archivo.

### Escenario 6 — Privacidad

Given una decisión pública y otra privada
When se ejecuta exportación incremental sin `--include-private`
Then solo la pública aparece en delta y estado.

### Escenario 7 — Alias y concurrencia

Given una salida que es alias del estado o un lock activo para ese estado
When se intenta exportar
Then el comando falla sin modificar delta ni estado.

## Fuera de alcance

- Relays, WebSockets o NIP-77 de red.
- Tabla journal o migración SQLite.
- Importación JSONL inversa a las tablas fuente.
- Sincronización automática o proceso residente.
- Selección arbitraria de campos o lenguaje `jq`.
- Retención o borrado automático del estado.
