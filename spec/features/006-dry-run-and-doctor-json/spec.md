# Spec: Dry Run and Structured Doctor

## Problema

El instalador puede preservar y sincronizar de forma segura, pero el usuario no
puede conocer sus operaciones antes de aplicarlas. `opencode-doctor` solo emite
texto humano y no valida el manifiesto gestionado, lo que dificulta CI y
diagnosticos reproducibles.

## Alcance

- Anadir `--dry-run` a Bash y `-DryRun` a PowerShell.
- Reutilizar las decisiones actuales de install, force y sync sin mutar estado.
- Anadir `opencode-doctor --json` con esquema versionado.
- Validar estructura, seguridad y presencia de entradas del manifiesto.
- Mantener sin cambios los modos humanos y de instalacion existentes.

## Fuera de Alcance

- `state.json`, hashes de contenido o migraciones de manifiesto.
- Detectar archivos modificados sin una baseline de hashes.
- Skill registry, uninstall, TUI o soporte para otros agentes.
- Arrancar Ollama, ejecutar modelos o reparar automaticamente la instalacion.
- E2E de OpenCode real, reservado para una feature posterior.

## Requisitos

### R1 - Preview sin efectos

Los instaladores MUST aceptar dry-run y MUST NOT crear, modificar o eliminar
archivos, directorios, backups, manifests o dependencias. MUST NOT clonar,
ejecutar `npm ci`, importar runtime instalado ni arrancar servicios.

### R2 - Decisiones compartidas

El preview MUST atravesar las mismas comprobaciones de existencia, preservacion,
force, sync, rutas protegidas y symlinks que la ejecucion real. MUST reportar
operaciones con verbos estables: `create`, `update`, `preserve`, `backup`,
`remove`, `install-dependencies` y `defer-verification`.

### R3 - Fuente remota

Si el instalador no dispone de la distribucion local, dry-run MUST reportar el
tag y repositorio que clonaria, MUST NOT crear temporales y MUST NOT inferir
pruning sin conocer el manifiesto deseado.

### R4 - Doctor JSON

`opencode-doctor --json` MUST emitir un solo documento JSON con
`schemaVersion`, `ok`, `checks`, `summary` y `manifest`. Los checks MUST tener
IDs, secciones, estados y obligatoriedad estables.

### R5 - Manifiesto honesto

El doctor MUST detectar manifest ausente, entradas vacias, duplicadas,
protegidas, no canonicas, inseguras, faltantes y symlinks. MUST ordenar rutas e
issues. MUST reportar modificacion como `unknown` porque el formato actual no
contiene hashes.

### R6 - Read-only y compatibilidad

El doctor MUST ser read-only en ambos formatos. La salida humana y sus exit codes
actuales MUST conservarse. Una opcion desconocida MUST terminar con codigo 2.
Las rutas MUST respetar `HOME`/`USERPROFILE` y `LOCALAPPDATA` en Windows.

## Escenarios de Aceptacion

### Escenario A - Instalacion limpia en preview

Given un HOME vacio y una distribucion local
When se ejecuta dry-run
Then reporta creaciones y dependencias previstas y HOME queda byte-a-byte igual.

### Escenario B - Sync con stale conocido

Given un manifiesto previo con un archivo stale
When se ejecuta sync dry-run
Then reporta backup y remove, pero conserva archivo, backup y manifiesto intactos.

### Escenario C - Symlink inseguro

Given un destino gestionado que atraviesa un symlink
When se ejecuta sync dry-run
Then falla cerrado sin modificar el target.

### Escenario D - Doctor valido

Given una instalacion completa con manifiesto valido
When se ejecuta doctor JSON
Then produce JSON parseable, `ok: true` y exit 0.

### Escenario E - Doctor con manifest manipulado

Given un manifest con traversal, duplicados o archivos faltantes
When se ejecuta doctor JSON
Then no sigue rutas inseguras, reporta issues deterministas y termina con exit 1.
