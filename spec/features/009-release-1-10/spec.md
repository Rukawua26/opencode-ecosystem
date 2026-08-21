# Spec: Release v1.10.0 y cierre documental

## Problema

`main` contiene perfiles reproducibles y el registro index-first de skills, pero
la release publica sigue en `v1.9.0`. Ademas, la base de conocimiento local aun
presenta `opencode-config-backup` como fuente activa y el README exige hashes de
commit autorreferenciales que no pueden prepararse dentro del mismo release.

## Alcance

1. Publicar las capacidades ya verificadas como `v1.10.0`.
2. Usar el tag exacto de release como contrato reproducible de checkout.
3. Declarar `/home/miguel/opencode-ecosystem` como fuente canonica local.
4. Mantener embeddings Ollama opcionales y el fallback textual operativo.
5. Corregir los bloqueos de portabilidad y analisis estatico descubiertos por el
   primer CI remoto del candidato.

## Fuera de alcance

- Cambios en Pbot o VozArt.
- Nuevos backends de embeddings, daemons o dependencias runtime.
- Reescritura del instalador, memory adapter o router local.
- Eliminacion de notas historicas sin conservar un enlace a la fuente canonica.

## Requisitos

- **R1**: root, paquetes publicos, router e instaladores MUST declarar `1.10.0`.
- **R2**: los ejemplos descargados MUST verificar que el checkout coincide con
  el tag exacto antes de ejecutar el instalador.
- **R3**: la documentacion activa MUST usar `opencode-ecosystem`; las rutas de
  backup antiguas MUST quedar marcadas como legado o retiradas de runbooks.
- **R4**: la suite local, contratos documentales, instaladores y auditoria npm
  MUST pasar antes del push.
- **R5**: la publicacion MUST iniciarse mediante `workflow_dispatch` explicito,
  depender de todos los jobs bloqueantes y producir tag, GitHub Release y
  paquetes npm `1.10.0` con provenance.
- **R6**: la ausencia de `ollama embed` MUST degradar a busqueda textual y MUST
  quedar documentada como capacidad opcional, no como fallo de instalacion.
- **R7**: Windows y CodeQL MUST finalizar sin omitir hallazgos; cuando GitHub Code
  Scanning no este disponible, el SARIF MUST conservarse y bloquear severidades
  altas mediante un gate local del workflow.

## Escenarios de aceptacion

### A. Instalacion desde release

Dado el README de `v1.10.0`, cuando se clona y valida el tag exacto, entonces el
instalador se ejecuta desde esa revision y usa `v1.10.0` por defecto.

### B. Fuente canonica

Dada la base de conocimiento local, cuando se consultan proyecto y runbooks,
entonces `opencode-ecosystem` es la fuente activa y el backup antiguo no dirige
operaciones actuales.

### C. Publicacion segura

Dado el candidato verificado en `main`, cuando el humano solicita exactamente
la version `1.10.0`, entonces CI pasa antes de crear el tag y publicar paquetes.

### D. Ollama incompatible

Dado un CLI Ollama sin subcomando `embed`, cuando se usa memoria semantica,
entonces el adapter devuelve resultados por fallback textual sin bloquear MCP.
