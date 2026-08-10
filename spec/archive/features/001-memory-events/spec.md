# Feature 001 — Memory Event Projection

## Objetivo

Exponer la memoria existente como eventos canónicos filtrables y exportables sin duplicar datos, migrar SQLite ni añadir red, claves o dependencias.

## Requisitos

### REQ-001 — Compatibilidad

El sistema MUST conservar las tablas y APIs actuales de `memory-adapter`.

### REQ-002 — Proyección canónica

El sistema MUST proyectar decisiones, bugs, arquitectura, preferencias e historial como eventos con `event_id`, `kind`, `project`, `created_at`, `tags`, `content` y `content_hash`.

### REQ-003 — Integridad

El sistema MUST calcular SHA-256 sobre una serialización JSON canónica que excluya `content_hash`.

### REQ-004 — Filtros

El sistema MUST filtrar en SQLite por proyecto, kind, rango temporal y límite antes de proyectar resultados.

### REQ-005 — Privacidad

Las decisiones privadas MUST quedar excluidas por defecto y MAY incluirse solo con opción explícita por CLI/API local. MCP MUST permanecer read-only y no exponerlas.

### REQ-006 — JSONL

El sistema MUST exportar un evento por línea y MUST detectar líneas inválidas o hashes alterados.

### REQ-007 — Referencias RDD

Los tags existentes MAY representar referencias `feature`, `file`, `commit`, `test`, `lens` y `receipt` sin modificar el esquema.

### REQ-008 — Límites

El sistema MUST imponer un límite seguro y MUST rechazar rangos temporales inválidos.

## Escenarios de aceptación

### Escenario 1 — Hash determinista

Given una decisión persistida
When se proyecta dos veces
Then ambos eventos tienen el mismo `event_id` y `content_hash`.

### Escenario 2 — Filtro por kind y fecha

Given memoria con decisiones y bugs
When se consultan eventos `decision` dentro de un rango
Then solo se proyectan decisiones del rango y nunca más que el límite.

### Escenario 3 — Privacidad

Given una decisión privada y una pública
When MCP lista o exporta eventos
Then solo devuelve la pública.

### Escenario 4 — Referencias RDD

Given tags `feature:001,receipt:r1,lens:verifier`
When se proyecta el registro
Then los tags canónicos conservan esas relaciones.

### Escenario 5 — JSONL alterado

Given un JSONL exportado correctamente
When se modifica el contenido sin recalcular el hash
Then la validación falla con la línea afectada.

## Fuera de alcance

- Relays o WebSockets.
- Firmas Schnorr/secp256k1.
- Identidad pública.
- Tabla journal nueva.
- Sincronización automática.
- Borrado o retención automática.
