# OpenCode Ecosystem

> Un comando. Cualquier agente. Cualquier OS.
> Ecosistema open source para potenciar OpenCode con memoria persistente, SDD, skills, multi-modelo y multiagentes.

## Filosofia

- **Reutilizar > stdlib > dependencia instalada > codigo nuevo > no existir** (YAGNI)
- **Ahorro de tokens**: subagentes arrancan en hoja en blanco, memoria estructura (no chat bruto)
- **Human in the loop**: el humano aprueba, el agente ejecuta
- **Local-first**: todo funciona offline, sync opcional via git
- **Modularidad**: plugins, skills, agentes y MCPs independientes

## Quick Start

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```

Con verbose:

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash -s -- --verbose
```

## Que incluye

| Componente | Descripcion |
|---|---|
| **16+ agentes** | Especializados: backend, frontend, security, devops, etc. |
| **17+ skills** | SDD, debug-bugs, security-review, obsidian, tdd, etc. |
| **7 plugins** | Kanban, guardrails, checkpoints, sandbox, personalities, validator, session-metrics |
| **3 MCP servers** | local-model-router (Ollama), context7, diagram-generator |
| **Memory adapter** | SQLite + MCP server universal (OpenCode, Claude Code, Cursor, etc.) |
| **Multi-modelo** | Routeo automatico de modelo por fase de trabajo |
| **Perfiles** | work, personal, light |
| **CI/CD** | Tests automaticos, validacion de install.sh, release a npm |

## Estructura

```
opencode-ecosystem/
├── config/          # opencode.jsonc, agents, plugins, mcp, profiles
├── skills/          # 17+ skills exportables
├── packages/        # Paquetes npm (memory-adapter)
├── docs/            # Arquitectura, guias, token-economy
├── tools/           # Repo map builder, scripts
├── tests/           # Tests de skills e install.sh
├── .github/         # CI/CD workflows
└── spec/            # SDD del propio ecosistema
```

## Instalacion manual

```bash
git clone https://github.com/Rukawua26/opencode-ecosystem.git
cd opencode-ecosystem
./install.sh
```

## API Keys

Las API keys se configuran manualmente por seguridad:

```bash
cp .env.example ~/.config/opencode/.env
# Editar con tus keys
```

## Licencia

MIT
