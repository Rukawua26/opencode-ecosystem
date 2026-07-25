<p align="center">
  <img src="https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/assets/hero.svg" alt="OpenCode Ecosystem" width="100%" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensource" alt="MIT License" />
  <img src="https://img.shields.io/badge/Node.js-22+-green?style=for-the-badge&logo=node.js" alt="Node.js 22+" />
  <img src="https://img.shields.io/badge/CI-green?style=for-the-badge&logo=githubactions" alt="CI" />
  <img src="https://img.shields.io/badge/Install%20Test-passing-brightgreen?style=for-the-badge" alt="Install Test" />
  <img src="https://img.shields.io/npm/v/@rukawua26/opencode-memory-adapter/1.3.0?color=blue&style=for-the-badge" alt="npm v1.3.0" />
  <img src="https://img.shields.io/npm/dt/@rukawua26/opencode-memory-adapter?color=cyan&style=for-the-badge" alt="npm downloads" />
  <img src="https://img.shields.io/github/stars/Rukawua26/opencode-ecosystem?style=for-the-badge&color=ff6b6b" alt="GitHub stars" />
</p>

<p align="center">
  <b>Un comando. Cualquier agente. Cualquier OS.</b>
</p>

<p align="center">
  <i>Ecosistema open source para potenciar OpenCode con memoria persistente, SDD, skills, multi-modelo y multiagentes.</i>
</p>

---

## 🚀 Quick Start

Requiere **Node.js 22+** y **Git**.

### Linux / macOS

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```

Con verbose (debugging):

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash -s -- --verbose
```

### Windows (PowerShell)

```powershell
irm -useb https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.ps1 | iex
```

O descargando directamente:

```powershell
git clone https://github.com/Rukawua26/opencode-ecosystem.git
cd opencode-ecosystem
.\install.ps1
```

---

## 🏗️ Arquitectura

```mermaid
graph TD
    subgraph "🎯 OpenCode Ecosystem v1.3"
        A[CLI Install] --> B[config/]
        A --> C[skills/]
        A --> D[packages/]
        A --> E[docs/]
        A --> F[tools/]
        A --> G[tests/]
        A --> H[.github/]
        A --> I[spec/]

        B --> B1[opencode.jsonc]
        B --> B2[agents]
        B --> B3[plugins]
        B --> B4[mcp]
        B --> B5[profiles]

        C --> C1[20 Skills]
        C --> C2[modes]
        C --> C3[prompts]
        C --> C4[debug]
        C --> C5[security]

        D --> D1[memory-adapter]
        D1 --> D1a[SQLite + FTS5]
        D1 --> D1b[MCP Server]
        D1 --> D1c[CLI + Context7]

        H --> H1[CI/CD Tests]
        H --> H2[Install Validation]
        H --> H3[Release to npm]
    end

    J[🧠 Human] -->|approves| K[Agent]
    K -->|executes| A
    K -->|reads| D1
    K -->|uses| C1
    K -->|queries| D1a

    L[🌐 npm registry] <-->|publish| D1
    M[📦 GitHub Releases] <-->|tag v1.3.0| H3
```

---

## 🔄 Flujo de Trabajo

```mermaid
flowchart LR
    A[📝 User Prompt] --> B{Agent Route}
    B -->|Backend| C1[backend agent]
    B -->|Frontend| C2[frontend agent]
    B -->|Security| C3[security agent]
    B -->|DevOps| C4[devops agent]
    B -->|Debug| C5[debug agent]

    C1 --> D[💾 Memory Layer]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D

    D --> E[🧩 Structured Context]
    E --> F[📊 Token Metrics]
    F --> G[📈 opencode-metrics]
```

---

## 🧰 Herramientas

### 🩺 Doctor — Verificar salud del ecosistema

```bash
# Ejecutar desde el repo
node tools/scripts/doctor.js

# O desde cualquier lugar (instalado por install.sh)
opencode-doctor
```

El comando `doctor` verifica:
- Dependencias (Node.js, npm, git)
- Estructura de directorios de OpenCode
- Skills instalados
- Memory Adapter y MCP
- Servidor Ollama local
- API Keys configuradas

### 📊 Medir ahorro de tokens

```bash
# Resumen de los últimos 7 días
opencode-metrics 7
```

Repite el comando después de una semana y compara tokens por mensaje, compactaciones, fallos y modelos. Consulta `docs/token-economy/measurement.md`.

---

## 📦 Qué incluye

| Componente | Descripción |
|---|---|
| **16+ agentes** | Especializados: backend, frontend, security, devops, etc. |
| **20 skills** | SDD, modes, prompts, debug, security, Obsidian y TDD |
| **8 plugins** | Kanban, guardrails, checkpoints, sandbox, personalities, validator, metrics y auto-memory |
| **4 MCP servers** | memory-adapter, local-model-router, context7 y diagram-generator |
| **Memory adapter** | SQLite + MCP server universal (OpenCode, Claude Code, Cursor, etc.) |
| **Multi-modelo** | Routing automático de modelo por fase de trabajo |
| **Perfiles** | work, personal, light |
| **CI/CD** | Tests automáticos, validación de install.sh, release a npm |

---

## 📂 Estructura

```
opencode-ecosystem/
├── config/          # opencode.jsonc, agents, plugins, mcp, profiles
├── skills/          # 20 skills exportables
├── packages/        # Paquetes npm (memory-adapter)
│   └── memory-adapter/
│       ├── src/        # Adapter, MCP server, CLI
│       ├── tests/      # 22 tests passing
│       └── package.json  # @rukawua26/opencode-memory-adapter@1.3.0
├── docs/            # Arquitectura, guías, token-economy
├── tools/           # Repo map builder, scripts
├── tests/           # Tests de skills e install.sh
├── .github/         # CI/CD workflows
└── spec/            # SDD del propio ecosistema
```

---

## 🔐 API Keys

Las API keys se configuran manualmente por seguridad:

```bash
cp .env.example ~/.config/opencode/.env
# Editar con tus keys
```

---

## 📊 Stats

<p align="center">
  <img src="https://github-readers-stats.vercel.app/api?username=Rukawua26&repo=opencode-ecosystem&theme=tokyonight&hide_border=true" alt="GitHub Stats" />
</p>

---

## 📜 Licencia

[MIT](https://opensource.org/licenses/MIT) © 2026 Rukawua26

<p align="center">
  <b>Hecho con ❤️ para la comunidad OpenCode</b>
</p>