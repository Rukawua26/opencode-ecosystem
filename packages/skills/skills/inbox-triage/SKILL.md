---
name: inbox-triage
description: Triage inbox notes and suggest where to move them in the Obsidian vault. Use when reviewing the inbox folder, or when asked to classify uncategorized notes.
---

# Inbox Triage Skill

Classify uncategorized notes from the Obsidian inbox (`~/docs/inbox/`) and suggest the correct destination in the vault. This skill helps maintain the "second brain" system by ensuring notes are properly classified each week.

## Vault Folder Taxonomy

| Folder | Purpose | Criteria |
|--------|---------|----------|
| `projects/` | Specific projects (code, repos, apps) | Has tech stack, repo path, entry points, build/run instructions |
| `areas/` | Cross-cutting knowledge | Theory, patterns, concepts that apply across multiple projects |
| `decisions/` | Architecture Decision Records | Explains a specific choice: context → decision → alternatives → consequences |
| `runbooks/` | Operational procedures | Step-by-step instructions for a task (backup, restore, deploy, recover) |
| `opencode/` | OpenCode config documentation | Agents, plugins, MCP servers, profiles, skills, conventions |
| `sources/` | External references | Content from web pages, articles, books — usually imported via `defuddle` |
| `canvases/` | Visual maps | `.canvas` files for visual graphs (≤30 nodes) |
| `inbox/` (stays) | Keep in inbox with `#later` tag | Idea worth keeping but not classifiable yet |
| `inbox/` (delete) | Trash | Duplicate, outdated, or irrelevant |

## Workflow

1. **Read all notes** in `~/docs/inbox/` (excluding `Inbox.md` itself)
2. **For each note**, determine its type:
   - Has `stack:` and repo info? → `projects/`
   - Explains a concept/pattern across multiple projects? → `areas/`
   - Documents a specific architectural decision? → `decisions/` (use ADR format)
   - Step-by-step procedure for a task? → `runbooks/`
   - OpenCode agent/plugin/MCP/profile/skill documentation? → `opencode/`
   - External content from a URL? → `sources/`
   - Visual diagram/map? → `canvases/`
   - Not classifiable yet but worth keeping? → tag `#later`, keep in `inbox/`
   - Duplicate, outdated, or irrelevant? → suggest deletion
3. **Check frontmatter**: ensure `tipo:` matches destination folder
4. **Suggest wikilinks**: after moving, add `relacionado:` links to related notes
5. **Suggest tags**: add `#status/draft|active|done` and `#area/trading|web|infra|config`
6. **Output a table**:

```
| Nota | Destino | Acción |
|------|---------|--------|
| nota1.md | projects/ | mover |
| nota2.md | decisions/ | mover + crear ADR |
| nota3.md | inbox/ | tag #later |
| nota4.md | — | eliminar (duplicado) |
```

## Notes
- Never move or delete files automatically — only suggest. The user confirms.
- New decisions should follow `templates/decision-template.md` (ADR format with ID).
- New projects should follow `templates/project-template.md`.
- New runbooks should follow `templates/runbook-template.md`.
- If a note could fit two folders, choose the most specific one (projects > areas > inbox).