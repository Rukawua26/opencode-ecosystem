# Stack tecnico

- OpenCode es el entorno de trabajo; `~/opencode-ecosystem` es la fuente de verdad. Tras cambios en el ecosistema se ejecuta `opencode-ecosystem sync --apply`; para cambios directos en `~/.config/opencode`, `opencode-ecosystem publish --yes`, con `status` antes y despues. (AGENTS.md, OpenCode CLI)
- Al crear o modificar skills, se editan primero en `~/opencode-ecosystem/skills` y se validan con `python3 ~/opencode-ecosystem/validate-skills.py ~/opencode-ecosystem/skills` antes de sincronizar. (AGENTS.md, OpenCode CLI)
- Los scripts Bash usan `set -u`, muestran preview por defecto y solo borran al recibir `--apply` o `--confirm`. (~/opencode-ecosystem/scripts/hygiene.sh:1-4,44-63)
- Python 3 y su libreria estandar se usan para verificacion, evitando dependencias nuevas cuando la stdlib basta. (spec/features/012-spec-constitution/spec.md:22-25; AGENTS.md, Code Minimalism)
- La configuracion se guarda en JSON o JSONC; la configuracion principal de OpenCode es `~/.config/opencode/opencode.jsonc`. (AGENTS.md, OpenCode CLI y Cron)
- La maquina objetivo es un i5-1235U con 8 GB RAM; estos recursos limitan el tamano de modelos y la RAM de las sesiones. (spec/features/012-spec-constitution/spec.md:24-25; AGENTS.md, Autoauditoria de Problema y Solucion)
