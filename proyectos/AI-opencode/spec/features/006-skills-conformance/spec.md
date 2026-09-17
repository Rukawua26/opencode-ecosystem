# 006-skills-conformance - Spec

## Problema
Las cinco skills cargan en OpenCode 1.18.29, pero usan la ruta global singular
`skill/` en lugar de la ruta publica documentada `skills/`, sus descripciones
no siempre incluyen triggers y tres cuerpos contradicen el runtime o las reglas
actuales. `SKILL_INDEX.md` duplica el descubrimiento nativo y puede divergir.

Fuente oficial: https://opencode.ai/docs/skills/ (actualizada 2026-09-10).

## Alcance
- ENTRA: corregir frontmatter/cuerpos de las cinco skills, eliminar el indice
  manual, migrar el ecosistema y runtime a `skills/`, y validar descubrimiento.
- FUERA: skills nuevas, plugins, agentes, MCP, metadatos opcionales y una
  allowlist `permission.skill` que podria ocultar skills futuras o integradas.

## Criterios de aceptacion
1. Cada skill usa `skills/<name>/SKILL.md`, nombre valido y coincidente.
2. Cada description indica que hace y cuando activarla (1-1024 caracteres).
3. `opencode debug skill` lista exactamente las cinco propias una sola vez,
   mas las skills integradas de OpenCode.
4. No existe `SKILL_INDEX.md` ni una instruccion para leerlo al iniciar.
5. `status` queda sin drift y `verify.sh` verde.
