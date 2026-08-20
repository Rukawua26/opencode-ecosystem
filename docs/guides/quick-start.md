# Quick Start Guide

## Requisitos

- **Node.js 22+** (`node -v` para verificar)
- **Git** (`git --version` para verificar)
- **npm** (incluido con Node.js)

## Instalacion

Usa el [Quick Start canonico](../../README.md#quick-start), que clona y valida
el tag exacto antes de ejecutar Bash o PowerShell. Esta guia no duplica comandos
de descarga para evitar que una ruta secundaria quede apuntando a `main`.

### Opciones de instalacion

```bash
# Con verbose (debugging)
./install.sh --verbose

# Sin memory adapter
./install.sh --skip-memory

# Previsualizar una sincronizacion sin escribir
./install.sh --sync --dry-run
```

## Post-Install

### 1. Configurar API keys

Las API keys se configuran **manualmente** por seguridad. Nunca las subas a git.

```bash
cp ~/.config/opencode/.env.example ~/.config/opencode/.env
nano ~/.config/opencode/.env
```

Agrega al menos una:
- `OPENAI_API_KEY` - para modelos GPT
- `ANTHROPIC_API_KEY` - para modelos Claude
- `GEMINI_API_KEY` - para modelos Gemini

### 2. Verificar instalacion

```bash
opencode-doctor
```

### 3. Iniciar OpenCode

```bash
opencode
```

## Memoria Persistente

El memory adapter se carga automaticamente. MCP solo expone lecturas:

| Herramienta | Uso |
|---|---|
| `get_context` | Cargar decisiones, bugs y arquitectura previa |
| `search_memory` | Buscar en toda la memoria |
| `export_project` | Exportar datos de un proyecto |

Las escrituras persistentes requieren el CLI local `memory-adapter` y una accion
humana explicita.

## Skills

Las skills se cargan por necesidad. Ejemplos:

```
> implementa un componente React con SDD
> depura este error de TypeScript
> revisa la seguridad de este endpoint
```

## Perfiles

```bash
# Perfil completo (trabajo)
opencode-work

# Perfil ligero (personal)
opencode-personal

# Perfil minimo (PCs limitadas)
opencode-light
```

## Backup

El instalador conserva hasta 10 backups de rutas gestionadas en
`~/.local/share/opencode/install-backups/`. Los secretos y personalizaciones
privadas requieren un backup separado y nunca deben entrar al repositorio.

## Solucion de problemas

### "command not found: opencode"
Reinicia la terminal o ejecuta:
```bash
export PATH="$HOME/.opencode/bin:$PATH"
```

### "out of memory"
Usa el perfil `light` y cierra otras aplicaciones.

### "EACCES permission denied"
No uses `sudo` con install.sh. Si ya lo hiciste:
```bash
rm -rf ~/.config/opencode
./install.sh
```
