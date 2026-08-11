# Verify: Ecosystem Hardening (Feature 004)

## Matriz de Cumplimiento

| Req ID | Requisito (MUST/SHOULD) | Estado | Evidencia |
|---|---|---|---|
| R1 | Router MCP inicia desde instalacion limpia | PASS | `test:install` verifica SDK instalado e importable; `npm run test:router` 23/23 |
| R2 | Sandbox no usa shell:true ni interpola entrada | PASS | `sandbox-helpers.js` exporta `buildDockerArgs` (array, no string); test vitest 16/16; lint 0 warnings |
| R3 | Checkpoints excluye .env y credenciales | PASS | `checkpoints-helpers.js` exporta `SKIP_PATTERNS` con 16 patrones; test vitest 13/13 |
| R4 | CI bloquea releases ante fallos | PASS | `test.yml` sin `continue-on-error`; `semantic-release.yml` ejecuta test+router+check-docs antes de release |
| R5 | Instalador respalda antes de sobrescribir y pin a tag | PASS | `install.sh` `INSTALL_TAG=v1.8.0`, `copy_if_ok` no sobrescribe sin `--force`, `npm ci` bloqueante |
| R6 | Embeddings incluyen content de decisiones | PASS | `adapter.js:232` embebe `title+content+rationale+tags`; `adapter.js:251` embebe todos los campos de bugs |
| R7 | Busqueda semantica devuelve filas sin embedding | PASS | `adapter.js:320-336` usa `LEFT JOIN` + fallback `LIKE`; `adapter.js:338-355` igual para bugs |
| R8 | Doctor verifica SDK del router | PASS | `doctor.js` check `router package.json`, `router SDK`, `router local-model-router.js` |
| R9 | Sin claims FTS5 en documentacion | PASS | `check-docs.js` valida 7 archivos; encontrado 0 menciones de FTS5 |
| R10 | Workflows de release no duplicados | PASS | `release.yml` eliminado; solo `semantic-release.yml` publica |
| R11 | Dependabot sin --admin | PASS | `dependabot-automerge.yml` usa `--squash --delete-branch` sin `--admin` |
| R12 | MCP server version dinamica | PASS | `mcp-server.js:8` `readAdapterVersion()` lee `package.json`; `local-model-router.js:12` igual |
| R13 | Export Obsidian sin colisiones | PASS | `adapter.js:654` append `-<id>` al nombre de archivo |
| R14 | Tests reales de sandbox y checkpoints | PASS | `sandbox.test.js` 16 tests; `checkpoints.test.js` 13 tests; `plugins.test.js` excluye `*-helpers.js` |
| R15 | API keys opcional en doctor | PASS | `doctor.js:97` `optional("at least one provider key")` |

## Resultados de Tests

| Suite | Tests | Pass | Fail |
|---|---|---|---|
| Vitest (todos) | 67 | 67 | 0 |
| Router (node:test) | 23 | 23 | 0 |
| Memory-adapter (node:test) | 42 | 42 | 0 |
| Install test | 1 | 1 | 0 |
| Check-docs | 1 | 1 | 0 |
| Lint | 1 | 1 | 0 |
| **Total** | **135** | **135** | **0** |

## Cobertura de Archivos Modificados

### Ronda 1 (auditoria inicial)
- `config/mcp/package.json` + `package-lock.json` — SDK declarado
- `config/mcp/local-model-router.js` — version dinamica
- `config/mcp/local-model-router.test.js` — rutas relativas
- `config/plugins/sandbox.js` — sin shell:true
- `config/plugins/checkpoints.js` — excluye .env
- `install.sh` / `install.ps1` — tag pinning, MCP deps
- `vitest.config.js` — include/exclude
- `.github/workflows/` — CI bloqueante, release unificado, dependabot sin --admin
- `packages/memory-adapter/src/adapter.js` — embeddings de content + LEFT JOIN
- `packages/memory-adapter/src/mcp-server.js` — version dinamica
- `tools/scripts/doctor.js` — router SDK check
- `tools/scripts/check-docs.js` — nuevo
- `README.md` / `README.es.md` / `docs/architecture/` / `assets/hero.svg` — sin FTS5

### Ronda 2 (pendientes)
- `config/mcp/local-model-router.js` — fix `pathToFileURL` → `fileURLToPath`
- `config/mcp/local-model-router.test.js` — asertar version + `readFileSync` import
- `config/plugins/sandbox-helpers.js` — nuevo, helperstesteables, regex corregido
- `config/plugins/checkpoints-helpers.js` — nuevo, helpers testeables
- `config/plugins/sandbox.js` — reimporta de helpers, sin rama `sg`
- `config/plugins/checkpoints.js` — reimporta de helpers
- `install.sh` — `copy_if_ok` + `copy_dir_if_ok` + `npm ci` bloqueante + SDK import check
- `install.ps1` — `Copy-IfOk` + `Copy-DirIfOk` + `npm ci` bloqueante
- `.github/workflows/test.yml` — `npm ci --prefix config/mcp` + sin check-docs duplicado
- `.github/workflows/semantic-release.yml` — `npm ci --prefix config/mcp`
- `tests/plugins/sandbox.test.js` — 16 tests nuevos
- `tests/plugins/checkpoints.test.js` — 13 tests nuevos
- `tests/plugins/plugins.test.js` — excluye `*-helpers.js`
- `packages/memory-adapter/README.md` — documentar fallback textual
- `tools/scripts/doctor.js` — API keys opcional
- `spec/features/004-ecosystem-hardening/tasks.md` — estado actualizado
- `spec/features/004-ecosystem-hardening/verify.md` — esta matriz

## Ambiente

- Node.js v22.x
- Ollama local (opcional, para embeddings)
- i5-1235U, 8GB RAM, local-first
- Sin FTS5, sin daemons nuevos, sin dependencias adicionales
