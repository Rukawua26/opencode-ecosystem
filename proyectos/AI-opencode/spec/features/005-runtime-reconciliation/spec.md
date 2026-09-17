# 005-runtime-reconciliation - Spec

## Problema
`AGENTS.md` declara agentes, plugins, MCP y comandos que no existen en la
instalacion activa. Ademas, `plugin_doctor.sh` usa una ruta fija distinta del
binario real (`/usr/bin/opencode`) y las specs 001/002 conservan tareas ya
diferidas o completadas. Esto consume contexto y puede inducir acciones contra
herramientas inexistentes.

## Alcance
- ENTRA: deteccion fiable del binario y pin, doctor completo desde `verify.sh`,
  reconciliacion compacta de `AGENTS.md`, correccion del flujo publish/sync en
  README y correccion documental de specs 001/002.
- FUERA: instalar plugins/agentes/MCP, conectar Ollama, cambiar `opencode.jsonc`,
  ejecutar publish/sync o reiniciar OpenCode.

## Criterios de aceptacion
1. `plugin_doctor.sh` detecta `1.18.29`, nunca pinea `?` y falla sin binario.
2. `verify.sh` ejecuta el doctor completo y queda verde.
3. `AGENTS.md` solo declara runtime existente; piso fijo total <=3400 tokens.
4. Specs 001/002 reflejan MCP diferidos y P5/P6 completados por spec 003.
5. `opencode debug config` es valido y el ecosistema queda sin drift.
