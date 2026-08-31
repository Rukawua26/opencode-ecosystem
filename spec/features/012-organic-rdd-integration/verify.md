# Verify — Feature 012: Integracion Organic RDD en Ecosystem

## Criterios de Aceptacion

| ID | Resultado | Evidencia |
|----|-----------|-----------|
| AC1 | PASS | `config/lib/organic-rdd.js` + `config/plugins/organic-rdd.js`; `node --check` OK |
| AC2 | PASS | config principal y 3 perfiles: 5 plugins nucleo + bloque `permission` review_* |
| AC3 | PASS | 8 comandos `review-*` en `config/commands/` |
| AC4 | PASS | `node --test tests/organic-rdd*.test.js` → 98 pass / 0 fail |
| AC5 | PASS | vitest 122/122 (14 files), lint exit 0, check-docs OK, router 23/23, memory 45/45 |
| AC6 | PASS | HOME temporal: 23/23 checks, plugin import OK, smoke `review_start`+`refuter` PASS |
| AC7 | PASS | `tests/hooks.test.sh` cubre instalacion, backup de pre-commit, post-commit intacto e idempotencia |
| AC8 | PASS | `--sync --skip-memory`: 23/23, `opencode.jsonc`/`.env` preservados, extras conservados, backup en `~/.config/opencode.pre-ecosystem-unification.20260830-190509` |
| AC9 | PASS | README actualizado (comandos RDD, hook opt-in, limitacion --no-verify); check-docs OK |

## Decisiones Adoptadas Durante Implementacion

- `@opencode-ai/plugin@1.18.14` anadido a `dependencies` del repo y runtime mnimo
  `config/package.json` + lock instalado via `npm ci` en `~/.config/opencode`.
- Vitest excluye `tests/organic-rdd*.test.js` (son node:test puros).
- Hook opt-in es script standalone (coherente con `install-hooks.sh`), no flag del instalador.
- `.env` activo estaba vacio desde el incidente del 06-08 (no borrado por esta feature);
  restaurado desde backup del 29-07 con `cp -a` sin leer contenido (perms 600).
- Correcciones de lint (prefer-const, unused catch, no-unsafe-finally en liberacion de
  lock) aplicadas en AMBAS fuentes (ecosystem y opendotfile) para mantener paridad:
  `cmp` confirma contenido identico.

## Comandos Ejecutados

- `node --test tests/organic-rdd.test.js tests/organic-rdd-plugin.test.js tests/organic-rdd-gate-hook.test.js` → 98/98
- `npm test` → 122/122 (14 archivos)
- `npm run lint` → exit 0 (0 errores)
- `npm run check-docs` → OK
- `npm run test:router` → 23/23
- `node --test packages/memory-adapter/tests/*.test.js` → 45/45
- `npm run test:install` → PASS
- `npm run test:hooks` → PASS (incluye RDD hook)
- `node --test tests/workflow-static-analysis.test.mjs` → 24/24
- `bash tests/release-tag.test.sh` → PASS
- `shellcheck --severity=warning` → limpio
- Instalacion HOME temporal: 23/23 + smoke funcional RDD
- Runtime activo: `opencode debug config` OK; smoke `start/refuter/validate` PASS

## Revision Independiente (Code Reviewer, 2 rondas)

- Ronda 1: 5 findings (staged vs worktree, fail-open sin node/lib, `npm ci`
  sobre manifiestos de usuario, PS1 sin verificacion RDD, deteccion floja del
  hook). Todos corregidos y con test de regresion:
  - hook bloquea divergencia indice/worktree (`hooks/pre-commit`, test dedicado);
  - hook fail-closed (exit 2) sin libreria o node;
  - `--no-save` para manifiestos de usuario en `install.sh` y `install.ps1`;
  - asserts RDD + import smoke en `install.ps1`;
  - `install-rdd-hook.sh` identifica por cabecera/cmp y respalda hooks compuestos.
- Ronda 2: 1 finding (divergencia bloqueaba con modo disabled); corregido:
  la comprobacion se omite si `current_mode === "disabled"` (test dedicado).
- Ronda final: `No findings.`

## Suites Finales

- RDD node:test: 101/101
- Vitest: 122/122 (14 archivos)
- Router: 23/23 | Memory: 45/45 | Workflow static: 24/24
- lint: 0 errores | check-docs: OK | shellcheck: OK | install: PASS | hooks: PASS | release-tag: PASS

## Reality-Check

REALITY-CHECK: AUTO-APPROVED
Reason: RDD integrado en ecosystem con paridad funcional demostrada, revision independiente sin findings tras 3 rondas, suite completa verde, runtime migrado con backup y sin perdida de secretos/memoria/custom plugins.
Findings: 0 CRITICAL / 0 HIGH / 0 WARN

## Pendientes (features siguientes)

- Feature 014 remota: archivar el repo remoto de opendotfile (hecho localmente: banner en README).
- `docs/` diagrams pueden mencionar comandos RDD en una revision posterior.

## Publicacion Final

- opencode-ecosystem: commit `f446f57` publicado en `origin/main` (https://github.com/Rukawua26/opencode-ecosystem).
- opendotfile: commits locales (incluidos 2 adelantados) publicados; commit final `fed22af` en `origin/main`; repositorio remoto **archivado** (`gh repo view` → `archived=true`).
- Ambos repositorios locales: arbol limpio y sincronizado con origin.
- Runtime activo: plugin `organic-rdd.js` carga correctamente tras el reinicio.
- Pendiente externo: validacion `tests/install.test.ps1` en Windows con `pwsh` (no disponible en esta maquina).

## Correcciones Post-Publicacion (31-08-2026)

La CI de `main` salio roja tras el commit de unificacion; correcciones aplicadas:

1. **Windows (CRLF)**: `tests/sdd-phase-common.test.js` normaliza `\r\n` -> `\n`
   en lecturas antes de las aserciones y compara el pack npm por contenido
   normalizado (agnostic al autocrlf del checkout).
2. **macOS (node 22)**:
   - tests: fixtures canonizados con `realpathSync` (`/var` -> `/private/var`);
   - libreria: `processIdentity()` es ahora cross-platform (Linux `/proc`,
     Windows PowerShell `StartTime`, resto `ps -o lstart=`); la recuperacion de
     locks abandonados ya no depende de `/proc`.
3. **CodeQL**: `js/file-system-race` (sev 7.7) en dos tests eliminado
   reescribiendo el patron read+stat con un unico descriptor
   (`openSync`/`fstatSync`/`readFileSync(fd)`), sin TOCTOU real.
4. **Consistencia de plugins**: los opcionales (`auto-memory`, `kanban`,
   `personalities`, `sandbox` + helpers) se movieron de `config/plugins/` a
   `config/plugins.disabled/` porque OpenCode auto-descubre todo el contenido
   de `plugins/`; los instaladores copian el directorio deshabilitado y la
   activacion es opt-in. README y `~/AGENTS.md` alineados; runtime activo
   actualizado (5 nucleo + extras personales).

Suites locales tras los fixes: Vitest 123/123, RDD 101/101, install PASS,
hooks PASS, lint/check-docs/shellcheck OK.
