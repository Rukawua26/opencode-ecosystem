# Quick Start Guide

## Requisitos

- **Node.js 22+** (`node -v` para verificar)
- **Git** (`git --version` para verificar)
- **npm** (incluido con Node.js)

## Instalacion

### Linux / macOS (recomendado)

```bash
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm -useb https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.ps1 | iex
```

### Git clone (manual)

```bash
git clone https://github.com/Rukawua26/opencode-ecosystem.git
cd opencode-ecosystem
./install.sh
```

### Opciones de instalacion

```bash
# Con verbose (debugging)
./install.sh --verbose

# Sin memory adapter
./install.sh --skip-memory

# Perfil ligero (para PCs con poca RAM)
./install.sh --profile light
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

El memory adapter se carga automaticamente. Herramientas disponibles:

| Herramienta | Uso |
|---|---|
| `get_context` | Cargar decisiones, bugs y arquitectura previa |
| `save_decision` | Guardar una decision tecnica |
| `save_bug_fix` | Guardar un fix y leccion aprendida |
| `save_architecture` | Guardar info de componentes |
| `search_memory` | Buscar en toda la memoria |
| `export_project` | Exportar datos de un proyecto |

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
opencode --profile work

# Perfil ligero (personal)
opencode --profile personal

# Perfil minimo (PCs limitadas)
opencode --profile light
```

## Backup

```bash
# Backup manual
~/tools/backup-opencode-config.sh

# Auto-backup (cron, cada 5 min)
# Ya configurado si tienes el timer activo
```

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
