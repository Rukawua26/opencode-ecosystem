# Quick Start Guide

## Installation

```bash
# Opcion 1: Curl-pipe (recomendado)
curl -sSL https://raw.githubusercontent.com/Rukawua26/opencode-ecosystem/main/install.sh | bash

# Opcion 2: Git clone
git clone https://github.com/Rukawua26/opencode-ecosystem.git
cd opencode-ecosystem
./install.sh

# Con verbose (debugging)
./install.sh --verbose

# Sin memory adapter
./install.sh --skip-memory
```

## Post-Install

1. **Configurar API keys (manual, por seguridad)**
```bash
cp ~/.config/opencode/.env.example ~/.config/opencode/.env
nano ~/.config/opencode/.env
```

2. **Iniciar OpenCode**
```bash
opencode
```

## Uso del Memory Adapter

El memory adapter carga automaticamente. En cualquier sesion:

- Al inicio de sesion, OpenCode puede usar `get_context` para cargar decisiones, bugs y arquitectura previa
- Cuando tomas una decision, usa `save_decision`
- Cuando arreglas un bug, usa `save_bug_fix`
- Para buscar algo previo, usa `search_memory`

## Uso de Skills

Las skills se cargan por necesidad. Al iniciar OpenCode:

```
> implementa un componente React con SDD
```

OpenCode detecta que pides SDD y carga las skills automaticamente.

## Uso de Multi-Modelo

La fase SDD usa el modelo optimo automaticamente segun `sdd_multi_model` en `opencode.jsonc`:

- specify/plan → Gemini (alto razonamiento)
- tasks/document → gpt-5.4-mini (ligero)
- implement/verify → gpt-5.4 (robusto)

## Perfiles

```bash
# Perfil completo (trabajo)
opencode --profile work

# Perfil ligero (personal)
opencode --profile personal
```

## Backup

```bash
# Backup manual
~/tools/backup-opencode-config.sh

# Auto-backup (cron, cada 5 min)
# Ya configurado si tienes el timer activo
```
