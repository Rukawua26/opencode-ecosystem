# Verify: Safe Installer Sync and Public Documentation

## Matriz

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 README publico actual | PASS | Sin hypruse/ADR-004, 61%, FTS5 ni conteos obsoletos; `check-docs` PASS |
| R2 Sync explicito | PASS | `--sync` y `-Sync`; incompatibles con force |
| R3 Preservacion | PASS | Tests conservan `opencode.jsonc`, archivos custom y rutas desconocidas |
| R4 Retirada segura | PASS | Solo poda entradas del manifiesto anterior; crea backup |
| R5 Primera sync | PASS | Actualiza y crea manifiesto sin podar desconocidos |
| R6 Paridad | PASS | Bash PASS local; PowerShell PASS en CI Windows del commit `4e71d59` |
| R7 Eval local | PASS | Comando opt-in fuera de CI; primera medicion 1/3 JSON estricto |
| R8 Mejoras locales | PASS | Guardrails/metrics integrados con 5 tests de comportamiento |
| R9 Scaffolders seguros | PASS | Sandbox temporal, timeout, `allowOnly: false`, skip POSIX en Windows, nombres hostiles/reservados y symlinks; CI remota `123e9ae` PASS |

## Verificaciones Locales

- `npm test`: 84/84 PASS.
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
- `npx vitest run tests/scaffolders.test.js`: 20/20 PASS.
- `npm run test:coverage`: PASS en 6 ejecuciones consecutivas durante la
  reproduccion de la carrera original; el candidato endurecido volvio a pasar la
  suite completa.

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

## CI Remota

El commit `123e9ae` (`fix: isolate scaffolder tests and harden name validation`)
paso todas las checks remotas:

- **CI - Tests** (`31607303590`): ubuntu-latest, macos-latest y windows-latest SUCCESS.
  - macOS: 84 tests Vitest + coverage PASS (carrera eliminada).
  - Windows: 84 tests Vitest + PowerShell install PASS.
  - Ubuntu: 84 tests Vitest + coverage + install + hooks + audit PASS.
- **CodeQL** (`31607303602`): SUCCESS.
- **install-validation** (Alpine): PASS.
- **release**: tag `v1.9.0` idempotente, npm publish idempotente.
- **Pages**: deployment SUCCESS.

Receipt Organic RDD aprobado:
`r_1786502587294_32ff64de-c528-4637-b31e-585d3989f8e7` (Tier 3, 4 lentes PASS).

## Limitaciones

- PowerShell no se ejecuta localmente porque `pwsh` no esta instalado; su coverage
  se confirma via CI Windows.
- macOS detecto originalmente una carrera: `scaffolders.test.js` creaba
  `config/plugins/zz-test-scaffold-plugin.js` mientras `plugins.test.js` lo
  enumeraba para coverage. El candidato actual ejecuta copias reales de los
  scripts en un `mkdtemp` unico y no escribe en el checkout.

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

Una revision posterior del fallo CI encontro ademas que `create-plugin.sh`
interpolaba el nombre dentro de fuente JavaScript. Se sustituyo por `process.argv`,
se restringieron ambos scaffolders a kebab-case y se agregaron casos de traversal,
espacios, guiones bajos y sintaxis ejecutable. Los procesos de test tienen timeout,
validan `status === 1` y el cleanup no oculta fallos del setup. La revision final
tambien cerro nombres reservados JavaScript y symlinks colgantes en el destino.
