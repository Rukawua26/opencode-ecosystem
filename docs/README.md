# OpenCode Ecosystem

> Ecosistema open source para potenciar OpenCode con memoria persistente, SDD, skills, multi-modelo y multiagentes.

Version documentada: **v1.9.0**.

## Componentes

- **Memory Adapter** — SQLite + MCP server para memoria persistente entre sesiones
- **Skills** — 21 skills exportables (SDD, debug, security, prompts, etc.)
- **Agentes** — 16 agentes especializados en producto, arquitectura, codigo, seguridad y revision
- **Multi-modelo** — Routing automatico entre modelos cloud y locales (Ollama)
- **Obsidian** — Catalogo determinista de proyectos e ingestión de fuentes con preview y escritura create-only
- **SDD** — Spec-Driven Development con plantillas y workflows
- **Organic RDD** — review Tier 0-3 con receipts ligados al hash del candidato
- **Instalador seguro** — preserva customizaciones por defecto y crea rollback con `--force`
- **Sync opt-in** — actualiza archivos gestionados, respalda reemplazos y poda solo rutas conocidas

## Instalacion

Instalacion completa:

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```

El instalador usa la release `v1.9.0` por defecto. Define `INSTALL_TAG` solo para instalar otra release explicitamente.

Para sincronizar una instalacion existente con `main` sin reemplazar
`opencode.jsonc`, ejecuta `install.sh --sync` o `install.ps1 -Sync`. La primera
sincronizacion crea el manifiesto sin borrar archivos desconocidos.

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

## Modelos locales

- Código: `qwen2.5-coder:3b`
- Chat y síntesis: `llama3.2:latest`
- Razonamiento: `llama3.2:latest`
- Contexto: `4096` tokens; retención: `1m`

## Verificacion

- Vitest: 72 tests
- Router MCP: 23 tests
- Memory adapter: 43 tests
- Instaladores: Linux, macOS, Alpine y Windows
- CI: lint, coverage, contratos, hooks e instaladores multiplataforma
- Eval local opt-in: `npm run eval:local-structure` (fuera de CI)

## Enlaces

- [Guia Rapida](guides/quick-start.md)
- [Arquitectura](architecture/overview.md)
- [Token Economy](token-economy/measurement.md)
- [Guia SDD](guides/sdd-step-by-step.md)
- [GitHub](https://github.com/Rukawua26/opencode-ecosystem)
- [npm](https://www.npmjs.com/org/rukawua26)
