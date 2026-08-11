# @rukawua26/opencode-memory-adapter

Universal memory adapter with SQLite + MCP server. Works with any AI coding agent that supports MCP: OpenCode, Claude Code, Cursor, Codex, VS Code Copilot, etc.

## Installation

```bash
npm install -g @rukawua26/opencode-memory-adapter
```

Or via ecosystem install:

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```

## MCP Configuration

Add to your agent's MCP config:

### OpenCode (`~/.config/opencode/opencode.jsonc`)
```jsonc
{
  "mcp": {
    "memory-adapter": {
      "type": "local",
      "command": ["node", "~/.config/opencode/mcp/memory-adapter/src/mcp-server.js"],
      "enabled": true
    }
  }
}
```

### Claude Code (`.claude/settings.json`)
```json
{
  "mcpServers": {
    "memory-adapter": {
      "command": "node",
      "args": ["~/.config/opencode/mcp/memory-adapter/src/mcp-server.js"]
    }
  }
}
```

### Cursor (`.cursor/settings.json`)
```json
{
  "mcpServers": {
    "memory-adapter": {
      "command": "node",
      "args": ["~/.config/opencode/mcp/memory-adapter/src/mcp-server.js"]
    }
  }
}
```

## MCP Tools (read-only)

| Tool | Description |
|---|---|
| `search_memory` | Search past decisions, bugs, architecture (text-based `LIKE`) |
| `search_memory_semantic` | Search using semantic embeddings when Ollama is available; falls back to text search when Ollama is absent or a row has no embedding |
| `get_context` | Get recent context for a project (use at session start) |
| `get_history` | Get session history log |
| `export_project` | Return shareable, non-private decisions as JSON |
| `list_events` | List canonical non-private events filtered by kind/date/limit |
| `export_events` | Return canonical non-private events as hash-verified JSONL |

MCP is intentionally read-only. Persistent writes require an explicit local
CLI command so model output cannot poison future sessions without approval.
The server binds reads to `OPENCODE_PROJECT_ROOT` (or its startup directory)
and derives a path-specific project identity, preventing cross-project reads.

## CLI Commands

```bash
# Initialize database
memory-adapter init

# Save an approved decision
memory-adapter save-decision --title "Use SQLite" --content "Local-first storage"

# Save an approved bug fix
memory-adapter save-bug --title "Timeout" --description "Request timed out" --fix "Add timeout handling"

# Export to JSON
memory-adapter export --path /path/to/project

# Export canonical events (private decisions excluded by default)
memory-adapter export-events --path /path/to/project --kind decision --limit 50 --out memory-events.jsonl

# Export only new or changed events and update a verified local state
memory-adapter export-events --path /path/to/project --state memory-events.state.jsonl --out memory-events.delta.jsonl

# Verify every JSONL event hash
memory-adapter verify-events --file memory-events.jsonl

# Import from JSON (replaces the target project's existing memory)
memory-adapter import --file memory-export.json

# Safe sync outside the repository (non-private decisions only)
memory-adapter sync --path /path/to/project

# Explicit team export with operational records
memory-adapter export --path /path/to/project --include-operational --out ./memory-export.json

# Export to Obsidian Markdown
memory-adapter export-obsidian --out ./docs/decisions

# Check status
memory-adapter status
```

## Canonical memory events

The event projection reuses the current SQLite tables; it does not create a journal table or duplicate writes.

```json
{
  "event_id": "decision:project:42",
  "kind": "decision",
  "project": "project",
  "created_at": "2026-08-10 12:00:00",
  "tags": [["feature", "001"], ["receipt", "r1"]],
  "content": { "title": "Decision", "content": "Approved" },
  "content_hash": "sha256-as-lowercase-hex"
}
```

Supported kinds are `decision`, `bugfix`, `architecture`, `preference`, and `operational`. References to SDD and Organic RDD use existing tags:

MCP defaults to `decision`, `bugfix`, and `architecture`. Preference values and operational history require an explicit `kind` because they may contain local configuration or file paths. Private decisions are never available through MCP.

```bash
memory-adapter save-decision \
  --title "Adopt event projection" \
  --content "No duplicated journal" \
  --tags "feature:001,file:src/adapter.js,commit:abc123,test:node-test,lens:verifier,receipt:r1"
```

The hash verifies content integrity, not author identity. The implementation intentionally has no relays, networking, public keys, Schnorr signatures, or new runtime dependencies.

### Incremental exports

`--state` adapts nak's `only-missing` behavior to local memory. The state is a cumulative, hash-verified JSONL file; `--out` receives only events that are new or whose canonical content changed. Known events are discarded before the final limit, so repeated limited runs continue draining older pending events instead of getting stuck behind recent known rows.

The command validates the complete state before touching either file, atomically replaces the delta first, and then atomically replaces the state. It resolves symlinks/hardlinks, takes an exclusive `<state>.lock`, recovers locks owned by dead processes, and rejects aliases between `--state` and `--out`. State files are bounded to 64 MiB and 10000 events on both read and write; rotate or replace the state explicitly instead of silently pruning history. A state is a reconciliation cache, not the source of truth, so resetting it safely causes one full re-export. Without `--state`, `export-events` keeps its original full-snapshot behavior.

Preference updates preserve their existing row ID. The next incremental export therefore replaces the previous state entry instead of accumulating dead versions of the same preference.

## Philosophy

- **Structured memory, not chat dumps**: Only saves decisions, bugs, architecture, preferences
- **Token efficient**: AI loads context on-demand via search, not everything at once
- **Local-first**: SQLite database on your machine, no cloud required
- **Privacy aware**: `isPrivate` flag for decisions that may contain secrets
- **Universal**: Any MCP-compatible agent can use it

## License

MIT
