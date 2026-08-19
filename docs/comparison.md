# Gentle AI vs OpenCode Ecosystem

Comparacion tecnica para decidir que adoptar sin copiar una plataforma completa.

## Baseline

| Proyecto | Version analizada | Fecha |
|---|---|---|
| Gentle AI | `main` `b002e0e7dfd30d7dbf5c3b43cf8be4e0fa7162da`; estable `v2.3.0` | 2026-08-14 |
| OpenCode Ecosystem | `main` desde `70ad924`; release `v1.9.0` | 2026-08-14 |

Filtro de decision: i5-1235U, 8 GB RAM, Ollama local, YAGNI, memoria acotada y
ahorro de tokens medido, no supuesto.

## Enfoque

| Area | Gentle AI | OpenCode Ecosystem |
|---|---|---|
| Alcance | Configurador para multiples agentes e IDE | Distribucion especializada para OpenCode |
| Runtime | Binario Go, TUI y componentes gestionados | Node.js 22+, scripts, plugins y MCP |
| Memoria | Engram, CLI/TUI, sync Git y MCP | Memory Adapter, SQLite nativo, MCP read-only y escritura CLI |
| Perfiles | Orquestadores y modelos por fase | `work`, `personal`, `light` y `default` |
| Skills | 22 skills y registry | 21 skills, agentes especializados y registry index-first |
| Routing | Directo, delegado u SDD opcional | Directo, maximo 3 subagentes, SDD opcional y router Ollama |
| Review | RDD nativo y delivery gates | Organic RDD con receipts ligados al candidato |
| Instalacion | TUI, Go install, Homebrew y binarios | Bash/PowerShell, manifest, dry-run y sync opt-in |
| Releases | Checksums firmados y updater binario | Checkout fijado a commit y CI multiplataforma |

## Fortalezas De Gentle AI

- Experiencia guiada de instalacion y diagnostico.
- Soporte amplio para clientes distintos de OpenCode.
- Perfiles OpenCode generados por fase y gestionados desde TUI.
- Registry de skills para descubrir metadata sin cargar todos los cuerpos.
- Engram ofrece consolidacion de proyectos y export/import para equipos.
- Releases macOS/Linux autenticadas con Minisign.
- Backups comprimidos, deduplicados y podados.

## Fortalezas Nuestras

- Menos procesos y dependencias para una maquina de 8 GB.
- Integracion profunda con OpenCode en vez de adaptadores horizontales.
- Ollama local limitado y apagado automatico tras inactividad.
- Memoria estructurada; no se carga ni guarda el chat completo.
- Plugins pequenos para guardrails, checkpoints, metricas y revision.
- Instalador read-only en dry-run y pruning limitado al manifest previo.
- Limites explicitos de subagentes y lecturas para controlar contexto.
- Configuracion legible y compatible con el esquema oficial de OpenCode.

## Lo Que Adoptamos

1. Doctor de configuracion efectiva y perfiles.
2. Launchers reproducibles `work`, `personal` y `light`.
3. Skill registry index-first sin watchers ni TUI.
4. Routing organico: directo para trabajo acotado, delegacion focalizada y SDD opcional.
5. Backups y ownership verificables antes de retirar archivos.
6. E2E determinista con runtime real y proveedor simulado en una feature posterior.
7. Firmas de release solo si en el futuro distribuimos binarios propios.

## Lo Que No Adoptamos

1. Soporte multi-IDE: aumenta superficie sin beneficiar el uso principal.
2. TUI Bubbletea: scripts y JSON cubren la necesidad actual con menos memoria.
3. Engram como segundo sistema de memoria: duplicaria autoridad y persistencia.
4. Perfiles generados con once agentes por perfil: multiplican config y contexto.
5. Subagentes background no durables y sin aislamiento de filesystem.
6. Judgment Day o revisores duplicados para cambios ordinarios.
7. Updater binario y Minisign mientras no exista un binario propio.
8. La rama `main` externa como dependencia operativa.

## Actualizaciones

La referencia adecuada es la release estable `v2.3.0`, no `main` ni la
prerelease. No se recomienda instalar Gentle AI sobre la configuracion activa:
ambos sistemas administrarian `~/.config/opencode` y podrian disputarse perfiles,
prompts y permisos.

Para reevaluar:

```bash
git ls-remote https://github.com/Gentleman-Programming/gentle-ai.git refs/heads/main
```

Si cambia el SHA, se revisan solo `docs/opencode-profiles.md`, `docs/engram.md`,
`internal/skillregistry/`, `internal/backup/`, `internal/doctor/` y contratos RDD
que puedan reducir complejidad. El detalle de baseline y decisiones se conserva
en `~/docs/sources/gentle-ai-analysis.md`.

## Veredicto

Nuestro ecosistema debe seguir siendo el nucleo. Gentle AI es una referencia
valiosa para UX operativa, registry, backups y contratos, pero no un reemplazo.
Toda adopcion debe demostrar menos tokens, menos fallos o mejor recuperacion sin
aumentar de forma relevante memoria y mantenimiento.
