# Plan: Skill Registry Index-First

## Enfoque

1. Implementar un CLI Node con solo stdlib.
2. Escanear `~/.config/opencode/skills`, `~/opencode-custom/skills` y
   `~/.opencode/skills` de forma recursiva sin symlinks.
3. Parsear solo el frontmatter inicial de `SKILL.md`.
4. Guardar un indice versionado en `~/.config/opencode/.skills-index.json` solo
   bajo `--refresh`.
5. Instalar un wrapper global y cubrir determinismo, duplicados y read-only.

## Archivos

| Archivo | Cambio |
|---|---|
| `tools/scripts/skills.js` | Scanner y CLI |
| `tools/scripts/opencode-skills.sh` | Wrapper global |
| `install.sh`, `install.ps1` | Instalacion gestionada |
| `tests/skills-registry.test.js` | Contratos del registry |
| `README.md`, `docs/README.md` | Uso y limites |

## Verificacion

- `npm test`
- `npm run lint`
- `npm run check-docs`
- `git diff --check`
- Organic RDD Tier 2 por tooling instalado.
