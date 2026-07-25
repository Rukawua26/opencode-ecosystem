<p align="center">
  <img src="https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/assets/hero.svg" alt="OpenCode Ecosystem" width="100%" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-MIT-yellow?style=for-the-badge&logo=opensource" alt="MIT License" />
  <img src="https://img.shields.io/badge/Node.js-22+-green?style=for-the-badge&logo=node.js" alt="Node.js 22+" />
  <img src="https://img.shields.io/badge/CI-activo-brightgreen?style=for-the-badge&logo=githubactions" alt="CI" />
  <img src="https://img.shields.io/npm/v/@rukawua26/opencode-memory-adapter/1.3.0?color=blue&style=for-the-badge" alt="npm v1.3.0" />
</p>

<p align="center">
  <b>Un comando. Cualquier agente. Cualquier SO.</b>
</p>

<p align="center">
  <i>Ecosistema open source para potenciar OpenCode con memoria persistente, SDD, skills, multi-modelo y multiagentes.</i>
</p>

---

## Inicio Rapido

Requiere **Node.js 22+** y **Git**.

### Linux / macOS

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm -useb https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.ps1 | iex
```

---

## Que incluye

| Componente | Descripcion |
|---|---|
| **16+ agentes** | Especializados: backend, frontend, security, devops, etc. |
| **20 skills** | SDD, modes, prompts, debug, security, Obsidian y TDD |
| **8 plugins** | Kanban, guardrails, checkpoints, sandbox, personalities, validator, metrics y auto-memory |
| **4 MCP servers** | memory-adapter, local-model-router, context7 y diagram-generator |
| **Memory adapter** | SQLite + MCP server universal |
| **Multi-modelo** | Routing automatico por fase de trabajo |
| **Perfiles** | work, personal, light |
| **CI/CD** | Tests automaticos, release npm, semantic-release |

---

## Estructura

```
opencode-ecosystem/
├── config/          # opencode.jsonc, agents, plugins, mcp, profiles
├── skills/          # 20 skills exportables
├── packages/        # Paquetes npm (memory-adapter, skills)
├── docs/            # Documentacion, guias, diagramas
├── tools/           # Scripts, scaffolders
├── tests/           # Tests de skills, plugins e install
├── .github/         # CI/CD, dependabot, codeql
└── spec/            # SDD del ecosistema
```

---

## Herramientas

### Doctor

```bash
opencode-doctor
```

Verifica: dependencias, estructura, skills, memory adapter, Ollama, API keys.

### Metrics

```bash
opencode-metrics 7
```

Mide ahorro de tokens en los ultimos 7 dias.

### Scaffolder

```bash
# Crear nuevo skill
bash tools/scripts/create-skill.sh mi-skill

# Crear nuevo plugin
bash tools/scripts/create-plugin.sh mi-plugin
```

---

## API Keys

Las API keys se configuran manualmente por seguridad:

```bash
cp .env.example ~/.config/opencode/.env
# Editar con tus keys
```

---

## Para contribuidores

### Desarrollo local

```bash
git clone https://github.com/Rukawua26/opencode-ecosystem.git
cd opencode-ecosystem
npm ci
npm test
```

### Devcontainer

Abre el repositorio en VS Code con Dev Containers extension. Se configurara automaticamente.

### Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` nueva funcionalidad (triggers minor release)
- `fix:` correccion de bug (triggers patch release)
- `docs:` solo documentacion (no triggers release)
- `chore:` mantenimiento (no triggers release)

---

## Licencia

[MIT](https://opensource.org/licenses/MIT) 2026 Rukawua26
