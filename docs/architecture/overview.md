# OpenCode Ecosystem Architecture

## Overview

```
                    ┌──────────────────────────────────────────┐
                    │            OpenCode CLI                   │
                    │         (Orquestador principal)            │
                    └──────────┬───────────────────────┬────────┘
                               │                       │
                    ┌──────────▼──────┐    ┌──────────▼────────┐
                    │     Plugins     │    │      Agents        │
                    │  (kanban,        │    │  (backend,         │
                    │   guardrails,    │    │   frontend,        │
                    │   checkpoints,   │    │   security,        │
                    │   sandbox, etc.) │    │   devops, etc.)    │
                    └──────────────────┘    └────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                 │
    ┌─────────▼──────┐  ┌──────▼───────┐  ┌──────▼──────┐
    │  MCP Servers   │  │    Skills     │  │  Profiles  │
    │               │  │               │  │             │
    │ memory-adapter │  │ sdd-specify   │  │ work        │
    │ local-router   │  │ sdd-plan      │  │ personal    │
    │ context7       │  │ sdd-tasks     │  │ light       │
    │ diagram-gen    │  │ sdd-implement │  │             │
    │               │  │ debug-bugs    │  │             │
    │               │  │ security      │  │             │
    │               │  │ tdd-workflow  │  │             │
    │               │  │ ...           │  │             │
    └───────┬────────┘  └───────────────┘  └─────────────┘
            │
    ┌───────▼────────┐
    │   SQLite DB    │
    │  (memory.db)   │
    │                │
    │ decisions      │
    │ bug_fixes      │
    │ architecture   │
    │ preferences    │
    │ session_history│
    └────────────────┘
```

## Data Flow

```
User Input → OpenCode (orchestrator) → Subagent (leaf context)
                    │                          │
                    │                          ├──→ Skill (loaded on demand)
                    │                          ├──→ Agent (specialized)
                    │                          └──→ MCP Server (tools)
                    │
                    └──→ Memory Adapter (SQLite)
                              │
                              ├── save_decision
                              ├── save_bug_fix
                              ├── get_context
                              └── search_memory
```

## Multi-Model Routing

```
┌─────────────┐    specify    ┌─────────────────────┐
│             │ ─────────────► │ google/gemini-flash  │ (razonamiento)
│   SDD       │                └─────────────────────┘
│   Flow      │    plan
│             │ ─────────────► │ google/gemini-flash  │ (razonamiento)
│             │                └─────────────────────┘
│             │    tasks
│             │ ─────────────► │ openai/gpt-5.4-mini  │ (ligero)
│             │                └─────────────────────┘
│             │    implement
│             │ ─────────────► │ openai/gpt-5.4       │ (robusto)
│             │                └─────────────────────┘
│             │    verify
│             │ ─────────────► │ openai/gpt-5.4       │ (bugs)
│             │                └─────────────────────┘
│             │    document
│             │ ─────────────► │ openai/gpt-5.4-mini  │ (ligero)
└─────────────┘                └─────────────────────┘
```

## Token Economy

| Estrategia | Ahorro estimado |
|---|---|
| Subagentes en hoja en blanco | 50-70% |
| Memoria estructurada (no chat) | 30-40% |
| Skills cargadas por necesidad | 20-30% |
| Multi-modelo (ligero para tareas simples) | 20-40% |
| Compaction con prune | 15-25% |
