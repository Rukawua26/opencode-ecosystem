# OpenCode Ecosystem

> Ecosistema open source para potenciar OpenCode con memoria persistente, SDD, skills, multi-modelo y multiagentes.

Version documentada: **v1.9.0**.

## Componentes

- **Memory Adapter** — SQLite + MCP server para memoria persistente entre sesiones
- **Skills** — 21 skills exportables (SDD, debug, security, prompts, etc.)
- **Agentes** — 16+ agentes especializados (trading, backend, frontend, design, android)
- **Multi-modelo** — Routing automatico entre modelos cloud y locales (Ollama)
- **Obsidian** — Catalogo determinista de proyectos e ingestión de fuentes con preview y escritura create-only
- **SDD** — Spec-Driven Development con plantillas y workflows
- **Organic RDD** — review Tier 0-3 con receipts ligados al hash del candidato
- **Instalador seguro** — preserva customizaciones por defecto y crea rollback con `--force`

## Instalacion

Instalacion completa:

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```

El instalador usa la release `v1.9.0` por defecto. Define `INSTALL_TAG` solo para instalar otra release explicitamente.

Paquetes individuales:

```bash
# Memory Adapter
npm install @rukawua26/opencode-memory-adapter

# Skills
npm install @rukawua26/opencode-skills
```

## Comandos

- `memory-adapter` — CLI para gestionar memoria
- `opencode` — CLI para interactuar con el ecosistema
- `python3 ~/docs/scripts/discover_projects.py --dry-run` — Previsualizar el catálogo del vault
- `python3 ~/docs/scripts/discover_projects.py --apply` — Crear notas faltantes y regenerar el grafo

## Modelos locales

- Código: `qwen2.5-coder:3b`
- Chat y síntesis: `llama3.2:latest`
- Razonamiento: `llama3.2:latest`
- Contexto: `4096` tokens; retención: `1m`

## Verificacion

- Vitest: 67 tests
- Router MCP: 23 tests
- Memory adapter: 43 tests
- Instaladores: Linux, macOS, Alpine y Windows
- CI: lint, coverage, contratos, hooks y Organic RDD

## Enlaces

- [Guia Rapida](guides/quick-start.md)
- [Arquitectura](architecture/overview.md)
- [Token Economy](token-economy/measurement.md)
- [Guia SDD](guides/sdd-step-by-step.md)
- [GitHub](https://github.com/Rukawua26/opencode-ecosystem)
- [npm](https://www.npmjs.com/org/rukawua26)
