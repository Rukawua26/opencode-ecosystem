# Verify: Safe Installer Sync and Public Documentation

## Matriz

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 README publico actual | PASS | Sin hypruse/ADR-004, 61%, FTS5 ni conteos obsoletos; `check-docs` PASS |
| R2 Sync explicito | PASS | `--sync` y `-Sync`; incompatibles con force |
| R3 Preservacion | PASS | Tests conservan `opencode.jsonc`, archivos custom y rutas desconocidas |
| R4 Retirada segura | PASS | Solo poda entradas del manifiesto anterior; crea backup |
| R5 Primera sync | PASS | Actualiza y crea manifiesto sin podar desconocidos |
| R6 Paridad | PARTIAL | Bash PASS local; PowerShell queda en CI Windows por ausencia de `pwsh` local |
| R7 Eval local | PASS | Comando opt-in fuera de CI; primera medicion 1/3 JSON estricto |
| R8 Mejoras locales | PASS | Guardrails/metrics integrados con 5 tests de comportamiento |

## Verificaciones Locales

- `npm test`: 72/72 PASS.
- `npm run test:coverage`: PASS; 93.61% statements, 77.48% branches, 100% functions, 96.63% lines sobre modulos instrumentados.
- `npm run test:router`: 23/23 PASS.
- `node --test packages/memory-adapter/tests/*.test.js`: 43/43 PASS.
- `npm run test:install`: PASS tras corregir traversal, `set -e`, rutas fuente y symlinks intermedios.
- `npm run test:hooks`: PASS.
- `npm run lint`: PASS.
- `npm run check-docs`: PASS.
- `npm audit --audit-level=high`: 0 vulnerabilidades.
- `bash -n install.sh tests/install.test.sh`: PASS.
- `git diff --check`: PASS.

## Eval Local

Primera ejecucion de `npm run eval:local-structure`:

- Total: 3.
- JSON y esquema validos: 1.
- Fallos: 2.
- `qwen2.5-coder:3b`: fallo por fences Markdown.
- `llama3.2:latest` chat: fallo por fences Markdown.
- `llama3.2:latest` reasoning: PASS.

Esta medicion evalua un caso por rol y no permite inferir calidad general ni
comparar con modelos cloud. Sirve como baseline reproducible para ampliar un
dataset solo cuando exista una necesidad concreta.

## Limitaciones

- PowerShell no se ejecuta localmente porque `pwsh` no esta instalado.
- La verificacion remota de README y CI requiere commit/push posterior.

## Hallazgos De Primera Revision

El primer receipt fue bloqueado y no se reutiliza. La revision detecto y se
corrigio:

- traversal Bash que podia resolver fuera de las raices gestionadas;
- retorno no cero de `preserve_manifest_prefix` bajo `set -e`;
- seguimiento de symlinks en componentes intermedios;
- rutas relativas corruptas por directorios fuente con `/` final;
- consumo de deltas metricos por eventos assistant incompletos.

La revision de resiliencia posterior agrego fallo cerrado ante backup PowerShell,
normalizacion CRLF, proteccion estructural de config/manifiesto, retencion de 10
backups y restauracion documentada. El test de retencion detecto y corrigio un
off-by-one Bash antes del candidato final.

La verificacion final detecto `find -printf` no portable a macOS; se reemplazo
por glob Bash y el test de retencion dejo de depender de extensiones GNU.
