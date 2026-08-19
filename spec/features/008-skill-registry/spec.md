# Spec: Skill Registry Index-First

## Problema

OpenCode descubre skills por archivos `SKILL.md`, pero no existe un inventario
local pequeno para buscar triggers sin leer el contenido completo de todas las
skills. Eso aumenta lecturas repetidas y dificulta detectar metadata invalida o
nombres duplicados.

## Alcance

- Crear un indice determinista de metadata de skills instaladas.
- Escanear solo raices OpenCode conocidas y no seguir symlinks.
- Ofrecer refresh explicito, status, JSON y busqueda local.
- Instalar el comando `opencode-skills` sin dependencias runtime nuevas.

## Fuera De Alcance

- Cargar automaticamente el indice en cada prompt.
- Instalar skills remotas o ejecutar contenido de skills.
- TUI, embeddings o watchers persistentes.

## Requisitos

### R1 - Indice minimo

El indice MUST contener solo nombre, descripcion, ruta y raiz. MUST ordenar
entradas y duplicados de forma determinista.

### R2 - Seguridad

El scanner MUST ignorar symlinks, archivos fuera de las raices y frontmatter
invalido. MUST NOT leer `.env` ni archivos distintos de `SKILL.md`.

### R3 - Escritura explicita

Solo `--refresh` MUST escribir el indice. `--status`, `--json` y `--search` MUST
ser read-only.

### R4 - Busqueda acotada

La busqueda MUST usar metadata del indice y no cargar cuerpos de skills.

## Escenarios De Aceptacion

### Escenario A - Refresh

Given skills validas en varias raices
When se ejecuta `opencode-skills --refresh`
Then escribe un JSON ordenado y reporta duplicados.

### Escenario B - Status read-only

Given un indice existente
When se ejecuta status o search
Then no cambia ningun archivo.

### Escenario C - Symlink

Given un `SKILL.md` alcanzable solo por symlink
When se refresca
Then no se sigue ni se indexa.
