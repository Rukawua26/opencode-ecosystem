# Gentleman AI Stack vs OpenCode Ecosystem

Comparativa funcional y arquitectonica entre ambos enfoques.

---

## Vision General

| Aspecto | Gentleman AI Stack | OpenCode Ecosystem |
|---|---|---|
| **Orquestador** | Multi-IDE (Claude Code, Cursor, OpenCode, etc.) | OpenCode CLI (foco unico) |
| **Package Manager** | Homebrew tap | curl-pipe (sin dependencias) |
| **Memoria** | Engram (Go + SQLite, servidor) | Memory Adapter (Node + SQLite, MCP) |
| **Skills** | Repos publicos, skills custom | Repos locales + 18 skills incluidas |
| **Multi-Modelo** | TUI picker (manual por fase) | JSON config (automatico por fase) |
| **Personalidad** | Frases como Gentleman | SOUL.md + presets (helpful, technical, teacher, etc.) |
| **Instalacion** | TUI interactiva con flags | Script bash + script PowerShell |
| **Filosofia** | Amplio alcance, multi-IDE | Profundidad, ahorrro de tokens, local-first |

---

## Filosofia y Principios

### Gentleman AI Stack
- "Un comando, cualquier agente, cualquier OS"
- Maximizar compatibilidad horizontal (soporta 6+ IDEs)
- TUI rica con menus interactivos
- Multi-agentes async como super-poder central

### OpenCode Ecosystem (nuestro enfoque)
- **Profundidad > Amplitud**: Optimizar OpenCode especificamente en lugar de soportar todos
- **Ahorro de tokens como religion**: cada decision tecnica se evalua por su impacto en tokens
- **Local-first, no cloud**: Funciona offline, sync opcional via Git
- **Sin dependencias externas**: nada de Homebrew, npm install opcional
- **Modularidad pura**: skills, plugins, MCPs totalmente independientes

---

## Memoria Persistente

### Gentleman (Engram)
- Go + SQLite con servidor local
- Búsqueda por "layers" (project info, actions, observations, full details)
- Sync entre companeros via Git (export/import)
- Engram Cloud (futuro): sync en tiempo real

### OpenCode (Memory Adapter)
- Node.js + SQLite via MCP server (universal)
- Tools: save_decision, save_bug_fix, search_memory, get_context
- Búsqueda semántica opcional con Ollama embeddings
- Export a Markdown para Obsidian vault
- Sync via Git, archivo JSON, o notas Markdown
- **Solo guarda informacion estructurada** (no chat completo)

**Ventaja nuestro:** No requiere Go, servidor, ni configuracion adicional. Funciona out-of-the-box con cualquier agente MCP-compatible.

---

## Skills

### Gentleman
- Skills publicas en repositorio
- Skills como subagentes (cada skill = agente especializado)
- Carga basadas en contexto

### OpenCode
- 18 skills preconfiguradas (SDD, debug, security, obsidian, tdd, etc.)
- Skills cargadas por necesidad
- Personalizables sin tocar OpenCode
- Skills custom agregables en cualquier momento

**Ventaja nuestro:** Skills listas para usar, sin descubrir ninguna o escribirlas desde cero.

---

## Multi-Modelo

### Gentleman
- TUI interactiva permite elegir modelo por fase
- Cambio manual entre proveedores
- Sin fallbacks automaticos

### OpenCode
- Configuracion declarativa en `opencode.jsonc`
- Routeo automatico segun fase de trabajo
- **Fallbacks automaticos**: si el modelo primario falla, usa el secundario
- Diferentes modelos por tipo de tarea (razonamiento vs implementacion)

**Ventaja nuestro:** Mas robusto y eficiente en tokens. Sin intervencion manual del usuario.

---

## Instalacion

### Gentleman
```bash
brew install Gentleman-programming/tap/gentleman-ai
```
Requiere:
- Homebrew (solo macOS)
- Go (para Engram)
- Configuracion de TUI

### OpenCode
```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```
Requiere:
- Node.js 18+
- Git

En Windows:
```powershell
iwr -useb https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.ps1 | iex
```

**Ventaja nuestro:** Sin Homebrew, sin Go, funciona identico en Linux/macOS/Windows.

---

## Personalidad del Agente

### Gentleman
- "Habla como yo" (Gentleman Programming, tono argentino)
- Personalidad fija

### OpenCode
- SOUL.md editable por el usuario
- 6 presets built-in (helpful, concise, technical, teacher, pirate, custom)
- Personalidad por sesion via comando `@set_personality`

**Ventaja nuestro:** Mas flexible, configuracion sin re-instalar nada.

---

## Subagentes Async

### Gentleman
- Strength principal: subagentes async via Task tool
- Background execution mientras trabajas

### OpenCode
- Misma capacidad via OpenCode Task tool
- Configurable en `opencode.jsonc`
- Safety guards: max 3 subagentes por feature

Mismo feature. Somos compatibles.

---

## Plugins

### Gentleman
- CLI installer automatico

### OpenCode
- 7 plugins preconfigurados:
  - **kanban.js**: tablero de tareas persistente
  - **guardrails.js**: anti-loop y deteccion de errores
  - **checkpoints.js**: snapshots automaticos antes de edits
  - **sandbox.js**: ejecucion aislada en Docker
  - **personalities.js**: gestion de personalidad del agente
  - **validator.js**: validacion de API keys en startup
  - **session-metrics.js**: metricas de sesion (tools, delegaciones, compactions)
- **auto-memory.js**: captura automatica de decisiones y bugs

**Ventaja nuestro:** Ya tenemos un ecosistema maduro de plugins custom.

---

## MCP Servers

### Gentleman
- Context7 (recomendado, opt-in)
- Notion, Jira, etc.

### OpenCode
- **memory-adapter**: nuestro core innovation
- **local-model-router**: routeo a modelos Ollama locales
- **context7**: disponible (opt-in)
- **diagram-generator**: disponible (opt-in)
- **playwright**: browser automation (opt-in)

5+ MCPs ya configurados vs los ~3 de Gentleman.

---

## Token Economy

### Gentleman
- Subagentes en hoja en blanco: 50-70% ahorro
- Skills cargadas por necesidad
- Compaction

### OpenCode
- Mismas estrategias (subagentes, skills, compaction)
- Mas: multi-modelo por fase (ahorro adicional 20-40%)
- Mas: memoria estructurada (no se carga chat bruto)
- Mas: configuracion declarativa sin TUI overhead

**Ventaja nuestro:** Mas capas de optimizacion, menos intervencion manual.

---

## Testing y CI/CD

### Gentleman
- Documentacion publica, sin CI claro

### OpenCode
- GitHub Actions:
  - Tests automaticos (Vitest + node:test)
  - Validacion de `install.sh` en Ubuntu/macOS/Alpine
  - Release automatico a npm al crear tag
- Dependabot para updates
- Tests de estructura de skills/agents/plugins

**Ventaja nuestro:** Validacion robusta de cada cambio.

---

## Casos de Uso Ideales

### Cuando elegir Gentleman AI Stack
- Si necesitas soportar multiples IDEs/Clientes (Claude Code, Cursor, etc.)
- Si prefieres TUI interactiva con menus
- Si quieres una "comunidad" grande alrededor de un proyecto estrella

### Cuando elegir OpenCode Ecosystem
- Si ya usas OpenCode y quieres profundizarlo al maximo
- Si valoras **ahorro de tokens** sobre amplitud de soporte
- Si prefieres **local-first sin dependencias externas** (Homebrew, Go)
- Si quieres **fallbacks automaticos** de modelos sin intervencion manual
- Si trabajas en **multiples SOs** con la misma fluidez

---

## Conclusion

Ambos enfoques son validos:
- **Gentleman** apuesta por amplitud (multi-IDE, TUI rica)
- **OpenCode Ecosystem** apuesta por profundidad y eficiencia (ahorro tokens, local-first)

Nuestro enfoque es especialmente util para developers que ya usan OpenCode como su agente principal y quieren extraer el maximo provecho sin overhead.

No son competidores: se complementan. Puedes usar Gentleman para tener el TUI de instalacion en macOS y luego aprovechar Memory Adapter y multi-modelo automatico de OpenCode Ecosystem.

---

## Tabla Resumen Rapida

| Feature | Gentleman AI | OpenCode Ecosystem | Ganador |
|---|---|---|---|
| Multi-IDE | Si (6+) | No (OpenCode only) | Gentleman |
| TUI interactiva | Si | No (script) | Gentleman |
| Memory persistente | Engram (Go+) | Memory Adapter (Node) | Empate |
| Fallback de modelos | Manual | Automatico | OpenCode |
| Skills preconfiguradas | No | Si (18+) | OpenCode |
| Plugins preconfigurados | No | Si (8) | OpenCode |
| Instalacion sin Homebrew | No | Si | OpenCode |
| Soporte Windows nativo | Parcial | Si (PowerShell) | OpenCode |
| CI/CD robusto | No claro | Si (Actions + npm) | OpenCode |
| Ahorro de tokens | 50-70% | 75-85% | OpenCode |
| Personalidad custom | Fija | SOUL.md editable | OpenCode |
