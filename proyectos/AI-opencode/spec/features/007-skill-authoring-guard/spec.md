# 007-skill-authoring-guard - Spec

## Problema
Las skills actuales cumplen el contrato oficial, pero `sync` y `publish` no
validan una skill nueva antes de copiarla. Un nombre, frontmatter o description
invalido podria llegar al runtime y quedar oculto para el agente.

Fuente: https://opencode.ai/docs/skills/ (verificada 2026-09-11).

## Alcance
- ENTRA: validador stdlib fail-closed, gates pre-sync/pre-publish, integracion
  con verify.sh, regla compacta de autoria y documentacion de uso.
- FUERA: generador de skills, nueva skill de autoria, plugin, daemon, red,
  dependencia YAML y cambios a `permission.skill`.

## Criterios de aceptacion
1. Valida ruta `skills/<name>/SKILL.md`, frontmatter, campos reconocidos,
   nombre/regex/directorio, description, metadata, unicidad y cuerpo no vacio.
2. Rechaza `SKILL_INDEX.md` y descriptions sin trigger documentado.
3. `sync --apply` y `publish --yes` abortan antes de modificar si hay errores.
4. Las cinco skills actuales pasan y `opencode debug skill` las carga una vez.
5. `verify.sh` valida fuente y runtime; ecosistema termina sin drift.
