# Verify: Ecosystem Hardening (Feature 004)

## Matriz de Cumplimiento

| Req ID | Requisito (MUST/SHOULD) | Estado | Evidencia |
|---|---|---|---|
| R1 | Router MCP inicia desde instalacion limpia | PASS | `test:install` verifica SDK instalado e importable; `npm run test:router` 23/23 |
| R2 | Sandbox no usa shell:true ni interpola entrada | PASS | `sandbox-helpers.js` exporta `buildDockerArgs` (array, no string); 8 tests; lint 0 warnings |
| R3 | Checkpoints excluye .env y credenciales | PASS | Patron unico cubre Unix, Windows, `.env-*`, claves y certificados; 8 tests |
| R4 | CI bloquea releases ante fallos | PASS | `test.yml` unifica tests y release; el job de publicacion depende de Linux/macOS, Windows y Alpine |
| R5 | Instalador respalda antes de sobrescribir y pin a tag | PASS | `INSTALL_TAG=v1.9.0`; reinstalacion preserva customizaciones y `--force` prueba backup antes de reemplazar |
| R6 | Embeddings incluyen content de decisiones | PASS | `adapter.js:232` embebe `title+content+rationale+tags`; `adapter.js:251` embebe todos los campos de bugs |
| R7 | Busqueda semantica devuelve filas sin embedding | PASS | `LEFT JOIN` + fallback textual normalizado; queries vacias no invocan embeddings ni contaminan ranking |
| R8 | Doctor verifica SDK del router | PASS | `doctor.js` check `router package.json`, `router SDK`, `router local-model-router.js` |
| R9 | Sin claims FTS5 en documentacion | PASS | `check-docs.js` valida 7 archivos; encontrado 0 menciones de FTS5 |
| R10 | Workflows de release no duplicados | PASS | `test.yml` es el unico pipeline de test/tag/publicacion; workflows redundantes eliminados |
| R11 | Dependabot sin --admin | PASS | `dependabot-automerge.yml` usa `--squash --delete-branch` sin `--admin` |
| R12 | MCP server version dinamica | PASS | `mcp-server.js:8` `readAdapterVersion()` lee `package.json`; `local-model-router.js:12` igual |
| R13 | Export Obsidian sin colisiones | PASS | `adapter.js:654` append `-<id>` al nombre de archivo |
| R14 | Tests reales de sandbox y checkpoints | PASS | `sandbox.test.js` 8 tests; `checkpoints.test.js` 8 tests; `plugins.test.js` excluye `*-helpers.js` |
| R15 | API keys opcional en doctor | PASS | `doctor.js:97` `optional("at least one provider key")` |

## Resultados de Tests

| Suite | Tests | Pass | Fail |
|---|---|---|---|
| Vitest (todos) | 67 | 67 | 0 |
| Router (node:test) | 23 | 23 | 0 |
| Memory-adapter (node:test) | 43 | 43 | 0 |
| Install test | 1 | 1 | 0 |
| Hook safety | 1 | 1 | 0 |
| Check-docs | 1 | 1 | 0 |
| Lint | 1 | 1 | 0 |
| **Total** | **137** | **137** | **0** |

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
- `.github/workflows/test.yml` — pipeline unico con CI multiplataforma y release dependiente de todos los jobs
- `tests/plugins/sandbox.test.js` — 8 tests de validacion y aislamiento
- `tests/plugins/checkpoints.test.js` — 8 tests de secretos multiplataforma
- `tests/plugins/plugins.test.js` — excluye `*-helpers.js`
- `packages/memory-adapter/README.md` — documentar fallback textual
- `tools/scripts/doctor.js` — API keys opcional
- `spec/features/004-ecosystem-hardening/tasks.md` — estado actualizado
- `spec/features/004-ecosystem-hardening/verify.md` — esta matriz

### Ronda 3 (hallazgos de review)
- `sandbox-helpers.js` — mensajes consistentes en ingles
- `adapter.js` — query normalizada, fallback case-insensitive y sin ranking para whitespace
- `checkpoints-helpers.js` — `.env` y variantes cubiertas en Unix y Windows
- `install.sh` / `install.ps1` — perfiles, skills, herramientas y memoria preservados sin `--force`
- `tests/install.test.sh` — prueba preservacion y backup antes de reemplazo
- Eliminado `npm install` del memory-adapter: usa solo built-ins y `dependencies` esta vacio

## Organic RDD

- Tier: 3
- Receipt final: `r_1786487919411_b0f983e3-4f79-419a-b0ed-ff443b9cd2b3`
- Candidate: `e383a986ba4c241f95a77dfefe75baa368e43a2aae44f69370bd8c356b5f53d2`
- Lentes: code-review PASS, verifier PASS, security-review PASS, architecture-review PASS
- Gate: `receipt_approved` (PASS)

## Release v1.9.0

- Versiones alineadas: root, memory-adapter, skills y local-model-router `1.9.0`.
- Pipeline unico: Linux/macOS + Windows + Alpine; el job de release depende de todos.
- Coverage: provider oficial `@vitest/coverage-v8`, 100% sobre los modulos instrumentados (14 statements).
- Supply chain: `npm audit` reporta 0 vulnerabilidades; semantic-release y 421 paquetes transitivos fueron retirados.
- Empaquetado: `npm pack --dry-run` valido para memory-adapter (7 archivos) y skills (34 archivos).
- Windows: `tests/install.test.ps1` cubre instalacion limpia, SDK, preservacion y rollback `-Force`; PASS en CI.
- RDD release: `r_1786490161597_285f9806-14a4-480d-adf8-29f18d536270`, gate PASS.
- RDD fixes multiplataforma: `r_1786491497562_caa492ad-8ac6-4966-855e-f989c2865148` y `r_1786491675801_1ef12edd-6918-4729-b2c7-75d39ce06687`, gates PASS.
- CI remoto: [run 31547474673](https://github.com/Rukawua26/opencode-ecosystem/actions/runs/31547474673) PASS en Linux, macOS, Windows y Alpine; CodeQL PASS.
- Release: [`v1.9.0`](https://github.com/Rukawua26/opencode-ecosystem/releases/tag/v1.9.0) publicada el 2026-08-11.
- npm: `@rukawua26/opencode-memory-adapter@1.9.0` y `@rukawua26/opencode-skills@1.9.0` publicados y verificados en registry.

## Ambiente

- Node.js v22.x
- Ollama local (opcional, para embeddings)
- i5-1235U, 8GB RAM, local-first
- Sin FTS5, sin daemons nuevos, sin dependencias adicionales
