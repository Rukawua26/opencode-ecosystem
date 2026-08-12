# Verify: Dry Run and Structured Doctor

## Matriz

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 Preview sin efectos | PASS local | HOME limpio inexistente permanece ausente; snapshots normal/force/sync identicos |
| R2 Decisiones compartidas | PASS | Funciones existentes emiten create/update/preserve/backup/remove antes de mutar |
| R3 Fuente remota | PASS | Script detached reporta clone/tag, no crea HOME/TMP ni infiere pruning |
| R4 Doctor JSON | PASS | 9 tests; schema v1, IDs estables, un unico JSON y exits 0/1/2 |
| R5 Manifiesto honesto | PASS | Missing, empty, duplicate, protected, unsafe, noncanonical y symlinks cubiertos |
| R6 Read-only y compatibilidad | PASS local | Humano preservado; JSON 18/18; Bash y PowerShell 7.5.3 portable PASS |

## Verificaciones Locales

- `npm test`: 93/93 PASS en 11 archivos.
- `npm run test:coverage`: PASS; 93.61% statements, 77.48% branches,
  100% functions y 96.63% lines sobre modulos instrumentados.
- `npm run test:router`: 23/23 PASS.
- `node --test packages/memory-adapter/tests/*.test.js`: 43/43 PASS.
- `npm run test:install`: PASS.
- `pwsh -NoProfile -File tests/install.test.ps1`: PASS con PowerShell 7.5.3
  portable en Linux; Windows nativo queda cubierto por CI.
- `npm run test:hooks`: PASS.
- `npm run lint`: PASS.
- `npm run check-docs`: PASS.
- `npm audit --audit-level=high`: 0 vulnerabilidades.
- `bash -n install.sh tests/install.test.sh`: PASS.
- `git diff --check`: PASS.
- `node tools/scripts/doctor.js --json`: exit 0, 18/18 requeridos,
  manifest valido con 85/85 presentes.

## Casos Dry Run

- HOME limpio: no crea ninguna ruta.
- Script detached: no crea temporales ni ejecuta clone.
- Normal: reporta `preserve` y conserva bytes/metadatos.
- Force: reporta backups y actualizaciones sin aplicarlos.
- Sync: reporta backup y retirada de stale conocido sin modificar manifest,
  archivos o backups.
- Symlink de archivo y componente intermedio: falla cerrado sin tocar targets.
- Node compile cache: deshabilitado solo durante preview para garantizar TMP
  inmutable incluso con Node 26.

## Doctor

- Mantiene salida humana y checks opcionales no bloqueantes.
- `--json` emite `schemaVersion`, `ok`, `checks`, `summary` y `manifest`.
- Rutas e issues se ordenan de forma determinista.
- No sigue traversal ni symlinks, incluidos symlinks colgantes.
- Un manifest vacio es invalido.
- `modified.status` es `unknown`: el manifest actual no contiene hashes y el
  doctor no inventa integridad de contenido.
- `GEMINI_API_KEY` y `GOOGLE_API_KEY` se reconocen sin exponer valores.

## Hallazgos Corregidos Durante Implementacion

1. Node 26 creaba `node-compile-cache` al consultar versiones durante dry-run.
   Se aislo con `NODE_DISABLE_COMPILE_CACHE=1` solo para preview.
2. PowerShell usaba `npm ci` sin comprobar `npm`; ahora lo valida junto a Node y Git.
3. `exit 0` en PowerShell dry-run podia terminar la suite llamante; se sustituyo
   por `return` para finalizar solo el instalador.
4. `existsSync` no detectaba symlinks colgantes; doctor usa `lstat` seguro.
5. Node/npm podian crear compile cache durante doctor; los wrappers publicos
   deshabilitan ese cache y una regresion exige HOME/TMP inmutables.
6. El test PowerShell dependia de `RUNNER_TEMP`/`TEMP`; ahora usa
   `System.IO.Path.GetTempPath()` como fallback reproducible.
7. La validacion PowerShell codificaba `\` como separador; ahora usa
   `DirectorySeparatorChar` y `Join-Path`, permitiendo validacion local en pwsh Core.
8. Las aserciones de backups PowerShell tambien se normalizaron a `/` para ser
   reproducibles en Windows, Linux y macOS.

## Limitaciones

- La validacion PowerShell local usa una distribucion portable temporal 7.5.3
  bajo `/tmp`; Windows nativo se confirma en CI.
- El doctor no puede detectar contenido modificado hasta que una feature futura
  introduzca hashes con una migracion explicita del manifest.
- Dry-run detached difiere el plan detallado porque no descarga fuentes en preview.

## Organic RDD

- Tier: 3.
- Receipt final aprobado: `r_1786560907263_02eef608-2e6b-49c8-9155-1f73adc482fe`.
- Lentes: code-review, verifier, security-review y architecture-review PASS.
- Gate: `receipt_approved` (PASS).
- Los subagentes de review abortaron por indisponibilidad del servicio; las cuatro
  lentes se ejecutaron manualmente con diff, pruebas adversariales y evidencia
  determinista registrada en el receipt.
- Receipts anteriores: `r_1786553788313_1ffa79de-fc72-4f93-b3c5-e2da5c1662ba`
  y `r_1786553977754_c0316406-c526-42f9-a9ad-f28e71ffbdbb` (closure documental).

## Sync Local

- `bash install.sh --sync --dry-run`: safe; propuso preserve de `opencode.jsonc`
  y backup de rutas gestionadas, sin retiros.
- `bash install.sh --sync`: aplicado correctamente.
- `opencode.jsonc` SHA-256 antes y despues identico:
  `a53b0ffa1ed20be4745755bbb110402d42553abdbd1a8538455a68ba3916cb73`.
- `opencode-doctor --json` instalado: schema v1, required 18/18, manifest 85/85.

## CI Remota

- PR #35 fusionado a `main` como squash `c1bc8f6`.
- **CI - Tests** (`31634445060`): ubuntu-latest, macos-latest y windows-latest SUCCESS.
  - macOS: 93 tests Vitest + coverage + install test PASS (find -printf reemplazado).
  - Windows: 93 tests Vitest + PowerShell install PASS (LOCALAPPDATA y shell:true).
  - Ubuntu: 93 tests Vitest + coverage + install + hooks + audit PASS.
- **CodeQL** (`31634445104`): SUCCESS.
- **install-validation**: PASS.
- **Pages**: deployment SUCCESS.
- Fix aplicado: `find -printf` BSD no portable reemplazado por snapshot Bash;
  `commandWorks` usa `shell:true` en Windows; fixture crea `plugins-data` bajo
  ambas rutas `HOME/.local/share` y `LOCALAPPDATA/opencode`.
