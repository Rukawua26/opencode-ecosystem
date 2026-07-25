# Diagramas de Arquitectura

## Estructura General

```mermaid
graph TD
    subgraph "OpenCode Ecosystem v1.3"
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

    J[Human] -->|approves| K[Agent]
    K -->|executes| A
    K -->|reads| D1
    K -->|uses| C1
    K -->|queries| D1a

    L[npm registry] <-->|publish| D1
    M[GitHub Releases] <-->|tag v1.3.0| H3
```

## Flujo de Trabajo del Agente

```mermaid
flowchart LR
    A[User Prompt] --> B{Agent Route}
    B -->|Backend| C1[backend agent]
    B -->|Frontend| C2[frontend agent]
    B -->|Security| C3[security agent]
    B -->|DevOps| C4[devops agent]
    B -->|Debug| C5[debug agent]

    C1 --> D[Memory Layer]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D

    D --> E[Structured Context]
    E --> F[Token Metrics]
    F --> G[opencode-metrics]
```

## Flujo SDD (Spec-Driven Development)

```mermaid
flowchart TD
    A[Feature Request] --> B[spec.md]
    B --> C[plan.md]
    C --> D[tasks.md]
    D --> E[implementacion]
    E --> F[verificacion]
    F --> G[merge a main]

    B -->|spec| B1[Alcance]
    B -->|spec| B2[Criterios de aceptacion]
    C -->|plan| C1[Arquitectura]
    C -->|plan| C2[Dependencias]
    D -->|tasks| D1[Tareas atomicas]
    D -->|tasks| D2[Orden de ejecucion]
```

## Diagrama de Seguridad

```mermaid
flowchart TD
    A[Usuario] --> B[OpenCode CLI]
    B --> C[Plugins]
    B --> D[MCP Servers]
    B --> E[Memory Adapter]

    C --> C1[guardrails.js]
    C --> C2[validator.js]
    C --> C3[checkpoints.js]

    C1 -->|anti-loop| C1a[WARN_CONSECUTIVE]
    C1 -->|total calls| C1b[WARN_TOTAL]
    C2 -->|valida| C2a[API Keys]
    C3 -->|backup antes de| C3a[edit/write]

    D --> D1[local-model-router]
    D --> D2[context7]

    E --> E1[SQLite]
    E1 --> E1a[decisions]
    E1 --> E1b[bug_fixes]
    E1 --> E1c[architecture]
    E1 --> E1d[preferences]
```

## Flujo de Release

```mermaid
flowchart LR
    A[PR merged a main] --> B[CI Tests]
    B --> C{Tests pass?}
    C -->|No| D[Fix required]
    C -->|Yes| E[Tag v1.3.0]
    E --> F[Release workflow]
    F --> G[npm publish]
    F --> H[GitHub Release]
    G --> I[@rukawua26/opencode-memory-adapter]
    H --> J[Release notes]
```
