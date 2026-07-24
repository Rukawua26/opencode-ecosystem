# opencode-memory-adapter

Universal memory adapter with SQLite + MCP server. Works with any AI coding agent that supports MCP: OpenCode, Claude Code, Cursor, Codex, VS Code Copilot, etc.

## Installation

```bash
npm install -g opencode-memory-adapter
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

## Tools

| Tool | Description |
|---|---|
| `save_decision` | Save architectural/technical decisions |
| `save_bug_fix` | Save bugs and their fixes for future reference |
| `save_architecture` | Save architectural component info |
| `save_preference` | Save project preferences |
| `save_session_action` | Log session actions to history |
| `search_memory` | Search past decisions, bugs, architecture (text-based) |
| `search_memory_semantic` | Search using semantic embeddings (requires Ollama) |
| `get_context` | Get recent context for a project (use at session start) |
| `get_history` | Get session history log |
| `export_project` | Export all memory for sharing/syncing |
| `import_project` | Import memory from exported JSON |
| `export_to_obsidian` | Export decisions/bugs to Markdown for Obsidian vault |

## CLI Commands

```bash
# Initialize database
memory-adapter init

# Export to JSON
memory-adapter export --project MyProject --path /path/to/project

# Import from JSON
memory-adapter import --file memory-export.json

# Sync with git
memory-adapter sync --project MyProject --path /path/to/project

# Export to Obsidian Markdown
memory-adapter export-obsidian --project MyProject --out ./docs/decisions

# Check status
memory-adapter status --project MyProject
```

## Philosophy

- **Structured memory, not chat dumps**: Only saves decisions, bugs, architecture, preferences
- **Token efficient**: AI loads context on-demand via search, not everything at once
- **Local-first**: SQLite database on your machine, no cloud required
- **Privacy aware**: `isPrivate` flag for decisions that may contain secrets
- **Universal**: Any MCP-compatible agent can use it

## License

MIT
