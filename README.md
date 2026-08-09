<p align="center">
  <img src="https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/assets/hero.svg" alt="OpenCode Ecosystem" width="100%" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensource" alt="MIT License" />
  <img src="https://img.shields.io/badge/Node.js-22+-green?style=for-the-badge&logo=node.js" alt="Node.js 22+" />
  <img src="https://img.shields.io/badge/CI-green?style=for-the-badge&logo=githubactions" alt="CI" />
  <img src="https://img.shields.io/badge/Install%20Test-passing-brightgreen?style=for-the-badge" alt="Install Test" />
  <img src="https://img.shields.io/npm/v/@rukawua26/opencode-memory-adapter?color=blue&style=for-the-badge" alt="npm version" />
  <img src="https://img.shields.io/npm/dt/@rukawua26/opencode-memory-adapter?color=cyan&style=for-the-badge" alt="npm downloads" />
  <img src="https://img.shields.io/badge/GitHub%20Pages-online-brightgreen?style=for-the-badge&logo=github&link=https://rukawua26.github.io/opencode-ecosystem/" alt="GitHub Pages" />
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
    K -->|verifies via| P[hypruse MCP tools]
    R[ADR-004 docs/sources/adr-004-hypruse-analysis] -->|validates| P

    L[🌐 npm registry] <-->|publish| D1
    M[📦 GitHub Releases] <-->|tag v1.6.1| H3
```

---

## 🔄 Flujo de Trabajo (SDD + Organic RDD verificado, ADR-004)

```mermaid
graph LR
    Prompt["📝 User Prompt"] --> Agente["🤖 Agente"]
    Agente --> Plan["📋 Plan (SDD): proposal approved"]
    Plan --> Build["🔨 Build: edit atomic (hyprctl.py, README)"]
    Build --> Verify["✅ Verify: hypruse_* tools + webfetch live"]
    Verify --> Review["🔍 Review (Organic RDD tiers)"]
    Review --> Decision{"Decisión"}
    Decision -- "OK / YAGNI" --> Merge["📦 Push (main / feature branch)"]
    Decision -- "Reabrir" --> Plan
    Review -->|Tier 0/1/2/3| T0["📄 docs (0 ceremony)"]
    Review -->|verifier| T1["🧪 code-review + security-review"]
    Review -->|evidence| Receipt["🧾 Receipt: start→capture→verify→finalize"]
    T0 --> Receipt
    T1 --> Receipt
    Receipt --> Merge
    Merge --> npm["🌐 npm registry"]
    Merge --> gh["📦 GitHub Release"]
    subgraph "Ahorro de tokens / YAGNI (hardware: i5-1235U, 8GB)"
        Plan
        Verify
        T0
    end
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

## 📋 Nota técnica — ADR-004 (2026-08-09)

Análisis del paquete `hypruse` 0.9.4 (dispatcher para Hyprland Lua-shim, `pointer` reparado con `cursor.move`, sin parche inventado). Ver `docs/sources/hypruse-analysis.md`.

**Método (Organic RDD / SDD, verificado con pruebas):**

1. **Plan (SDD)** — proposal approved; scope: stock `hypruse` 0.9.4, no local patch.
2. **Build (atómico)** — edit `hyprctl.py`: caso `movecursor` → `hl.dsp.cursor.move({x=, y=})`; clear `.pyc`; restart.
3. **Verify (read-only evidence)** —
   - `hypruse_pointer scroll` → `cursor now at (150,500)` ✅
   - `hypruse_pointer click` → `click ok` ✅
   - `hypruse_hypr focus_window target=0x...eafef0` → `active_window: 0x...eafef0` ✅ (P4 ventana flotante)
   - `hypruse_launch brave --new-tab https://aicl…` → `title: aicall.io – KI für Hotels` ✅ (P3)
   - navegación GoHighLevel → sidebar "Automatización" → URL `…/automation/workflows` ✅
   - `webfetch https://aicall.io` → confirma título real = "apicall.io – KI für Hotels" (valida URL, detecta omnibox hijack)
4. **Review (capas) — Organic RDD tiers:**
   - Tier 0: `docs/sources/hypruse-analysis.md` (referencia, 0 ceremony).
   - Tier 1: `AGENTS.md` (philosophy: i5-1235U, 8GB RAM, YAGNI, ahorro de tokens).
   - Tier 2: `README.md` + `docs/` (config/central).
   - Tier 3: runtime `hyprctl.py` + `opencode.jsonc`.
   - Lentes usados: `verifier` (tools live), `code-review` (diff, `.pyc` limpiado), `security-review` (no permisos nuevos, `pointer` es local-only).
   - Receipt: `review_start → review_capture → review_verify → review_finalize` (no `review_gate` for Tier 0/Tier 2 docs; runtime Tier 3 verificado manualmente).
5. **Autoauditoría de código (3 preguntas):**
   1. ¿Qué hace cada bloque? `_to_lua` traduce legacy dispatchers → `hl.dsp.*`; `movecursor` case mueve cursor (x,y) en coords globales.
   2. ¿Por qué así? El build de Hyprland usa Lua-shim; los legacy dispatchers son syntax error.
   3. ¿Dato inesperado? Un runtime cached/no-reiniciado devuelve `mouse.move` (nil) → se documentó: requiere restart; `.pyc` limpiado.

**Veredicto:** no hay bug en stock; la falla `pointer` era el dispatcher faltante (`movecursor` no mapeado), parche mínimo 4 líneas. `keyboard focus` no es acción válida (enum `type|key`); usar `hypruse_hypr focus_window`. Ahorro de tokens: stock `hypruse` > full binario (`gentle-ai`).


---

## 📜 Licencia

[MIT](https://opensource.org/licenses/MIT) © 2026 Rukawua26

<p align="center">
  <b>Hecho con ❤️ para la comunidad OpenCode</b>
</p>