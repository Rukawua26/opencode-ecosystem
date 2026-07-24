# Tech Stack

## Core
- **OpenCode CLI** — orquestador principal
- **Node.js 18+** — runtime de plugins, skills y MCP servers
- **SQLite** — almacenamiento del memory adapter (via `node:sqlite`)

## Modelo
- **OpenAI GPT 5.4** — implementacion, verificacion
- **OpenAI GPT 5.4-mini** — tareas ligeras, exploracion, titulos
- **Google Gemini 2.5 Flash** — especificacion, planificacion (alto razonamiento)
- **Ollama (local)** — modelos locales via MCP router

## MCP Servers
- **memory-adapter** — SQLite + MCP server universal
- **local-model-router** — routeo de modelos locales (Ollama)
- **context7** — docs de librerias (opt-in)
- **diagram-generator** — diagramas Mermaid/Draw.io (opt-in)

## Plugins
- **personalities** — SOUL.md + presets
- **guardrails** — anti-loop, deteccion de errores
- **checkpoints** — snapshots automaticos
- **kanban** — tablero de tareas
- **sandbox** — ejecucion aislada en Docker
- **validator** — validacion de API keys
- **session-metrics** — metricas de sesion

## Testing
- **Vitest** — tests de skills y plugins (formato describe/it)
- **node:test** — tests del memory adapter
- **bash** — tests de install.sh

## CI/CD
- **GitHub Actions** — tests, install validation, release a npm
- **Dependabot** — actualizacion de dependencias
