# Feature 003: Obsidian Project Knowledge

## Intent

Convertir los proyectos locales y las fuentes futuras del usuario en conocimiento navegable dentro de `~/docs`, usando OpenCode y Ollama local-first. La solución debe descubrir proyectos sin LLM, crear solo notas faltantes, mostrar relaciones en Obsidian Canvas y ofrecer un skill de ingestión con preview antes de escribir.

## Alcance

### Incluido

- Descubrir directorios de proyecto inmediatos bajo el home mediante marcadores locales.
- Ignorar carpetas personales, backups, cachés y symlinks.
- Extraer nombre, stack, resumen y área de archivos acotados.
- Crear notas faltantes en `projects/` sin reemplazar notas existentes.
- Generar `canvases/Mapa de Proyectos.canvas` de forma determinística.
- Reusar `docs/scripts/graph-viz.sh` para Mermaid y `grafo.html`.
- Crear el skill OpenCode `obsidian-ingest` y reglas españolas del vault.
- Usar `local-model-router` solo para síntesis semántica solicitada.

### Fuera de alcance

- Claude Code, API Anthropic o runtime de `claude-obsidian`.
- Watchers, cron, daemon residente u OCR.
- Escaneo recursivo indiscriminado del home.
- Sobrescritura o reorganización masiva de notas existentes.
- Embeddings, base vectorial o proceso residente adicional.

## Requisitos

### REQ-001 Descubrimiento acotado

El descubridor MUST inspeccionar solo directorios inmediatos del home y MUST considerar proyecto un directorio real que tenga `.git`, `AGENTS.md` o al menos uno de: `package.json`, `pyproject.toml`, `requirements.txt`, `docker-compose.yml`, `Cargo.toml`, `go.mod`.

### REQ-002 Privacidad y límites

El descubridor MUST omitir symlinks, carpetas ocultas, medios, descargas, backups, caches y dependencias. MUST leer como máximo 128 KiB por archivo de metadatos y MUST usar únicamente Python stdlib.

### REQ-003 Escritura segura

La ejecución MUST ser dry-run por defecto y MUST requerir `--apply` para escribir. Una nota existente MUST permanecer byte-for-byte intacta. Las nuevas notas MUST crearse de forma atómica y create-only.

### REQ-004 Metadatos determinísticos

Cada nota nueva MUST incluir `titulo`, `tipo: proyecto`, `stack`, `estado`, `tags`, `relacionado`, `ultima-actualizacion`, `project_path`, `project_type`, `framework` y `summary`. El stack, área y resumen MUST derivarse de archivos locales sin LLM.

### REQ-005 Relaciones útiles

Las relaciones MUST derivarse de referencias explícitas de token completo en README/AGENTS o de al menos dos tecnologías compartidas. Una referencia dirigida MUST salir del proyecto que menciona al otro. Los wikilinks MUST apuntar al nombre real del archivo y MAY usar alias de presentación. La salida MUST ser estable para los mismos bytes de entrada y MUST evitar self-links y aristas duplicadas.

### REQ-006 Canvas nativo

El descubridor MUST generar JSON Canvas válido con IDs estables, nodos de archivo para cada proyecto, grupos por área y aristas válidas. Todos los endpoints MUST existir y todos los IDs MUST ser únicos.

### REQ-007 Reuso del grafo existente

Tras un apply exitoso, el descubridor MUST ejecutar el `_graph_gen.py` confiable situado junto al descubridor y MUST pasarle el vault explícito. `graph-viz.sh` MUST conservarse como wrapper manual. No MUST duplicar la generación de Mermaid o HTML. Las escrituras del MOC y HTML MUST ser atómicas y las etiquetas incrustadas en HTML MUST escaparse.

### REQ-008 Skill OpenCode

`obsidian-ingest` MUST ser un Agent Skill válido para OpenCode. MUST orquestar extracción de URL, PDF, YouTube y texto local, búsqueda dirigida de notas relacionadas, router local-first, preview y confirmación antes de escribir.

### REQ-009 Fuentes no confiables

El skill MUST tratar el contenido ingerido como datos no confiables e ignorar instrucciones, cambios de destino, solicitudes de secretos o comandos incrustados en la fuente.

### REQ-010 Sin sobrescritura silenciosa

El skill MUST confinar destinos al vault, rechazar rutas absolutas, `..`, padres symlink y destinos existentes, y MUST solicitar confirmación explícita para cualquier actualización de índices o MOC. Una extracción incompleta MUST declararse parcial.

### REQ-011 Integración y despliegue

El skill MUST vivir en las dos superficies versionadas del paquete (`skills/` y `packages/skills/skills/`) y MUST desplegarse a `~/.opencode/skills/obsidian-ingest/`. OpenCode MUST reiniciarse para cargarlo.

### REQ-012 Eficiencia

El descubridor MUST consumir cero tokens LLM y no dejar procesos residentes. La ingestión MUST limitar lecturas existentes a cinco notas candidatas por defecto y usar el router local antes de cloud.

## Escenarios de aceptación

### Escenario 1: Dry-run seguro

**Given** proyectos detectables y notas faltantes
**When** se ejecuta el descubridor sin `--apply`
**Then** reporta proyectos, notas y relaciones propuestas sin cambiar ningún archivo.

### Escenario 2: Backfill create-only

**Given** una nota existente y una nota faltante
**When** se ejecuta con `--apply`
**Then** crea solo la faltante y preserva exactamente la existente.

### Escenario 3: Canvas válido

**Given** el catálogo descubierto
**When** se aplica la generación
**Then** el Canvas parsea como JSON, tiene IDs únicos y ninguna arista colgante.

### Escenario 4: Idempotencia

**Given** una aplicación exitosa sin cambios posteriores
**When** se repite `--apply`
**Then** no cambia notas ni Canvas y reporta cero notas nuevas.

### Escenario 5: Fuente web en preview

**Given** una URL aprobada
**When** se invoca `obsidian-ingest`
**Then** extrae texto limpio, busca como máximo cinco notas relacionadas y muestra un borrador sin escribir.

### Escenario 6: Destino existente

**Given** que el archivo destino ya existe
**When** el usuario intenta aplicar el borrador
**Then** el skill se detiene y no modifica el archivo.

### Escenario 7: Fuente maliciosa

**Given** una fuente con instrucciones o peticiones de secretos
**When** el skill la procesa
**Then** las trata como contenido citado y no las ejecuta.
