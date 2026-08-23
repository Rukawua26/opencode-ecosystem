# Verify: Release v1.10.0 y cierre documental

## Estado

PASS completo. Verificacion local, Windows, CodeQL, tag, GitHub Release y los dos
paquetes npm finalizaron correctamente.

## Matriz

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 Versiones 1.10.0 | PASS | Root, workspaces, router, lockfiles e instaladores alineados |
| R2 Checkout reproducible | PASS | README y contrato documental validan `git describe --tags --exact-match` |
| R3 Fuente canonica | PASS | MOC, resumen, alias legado y tres runbooks usan `opencode-ecosystem` |
| R4 Verificacion local | PASS | Suites, coverage, install Bash, hooks, audit, packs, doctor y diff pasan |
| R5 Publicacion | PASS | Recovery run `32585511443`; tag, GitHub Release y dos paquetes npm verificados |
| R6 Fallback Ollama | PASS | Deteccion del CLI incompatible, fallback explicito y 45/45 tests del adapter |
| R7 Windows y CodeQL | PASS | CI `32585330953` y CodeQL `32585330966` sobre `ae4a911`; recovery Windows verde |

## Evidencia local

- `npm test`: 106/106 PASS.
- `npm run test:coverage`: PASS; 93.91% statements, 76.12% branches,
  100% functions y 96.8% lines.
- `npm run test:router`: 23/23 PASS.
- Memory adapter: 45/45 PASS, incluida deteccion de CLI sin `embed` y fallback a texto.
- `npm run test:install`: PASS.
- `npm run test:hooks`: PASS.
- `npm run test:release`: PASS para tag anotado coincidente y conflicto.
- `npm run lint` y `npm run check-docs`: PASS.
- `npm audit --audit-level=high`: 0 vulnerabilidades.
- `npm pack --dry-run`: memory adapter 7 archivos; skills 35 archivos.
- `bash install.sh --sync --dry-run`: PASS y sin escrituras.
- `node tools/scripts/doctor.js --json`: `ok: true`, 18 checks requeridos.
- `git diff --check` y `bash -n`: PASS.

## Cobertura remota

`pwsh` no esta instalado en la maquina, por lo que Windows se valido en el runner
nativo `windows-latest`. El job paso tanto en CI de `main` como en el recovery
antes de publicar npm.

## Hallazgos corregidos

- El workflow rechaza un tag existente si no apunta al `RELEASE_SHA` validado
  antes de ejecutar el candidato.
- La release requiere dispatch y version explicitos, acciones fijadas a SHA y
  publicacion npm sin lifecycle scripts ni provenance no soportado; toda version
  npm debe coincidir en `gitHead` e integridad despues de publicarse o durante
  un reintento. El preflight exige CodeQL exitoso para el SHA exacto.
- Los tests de release ejercitan modo nuevo, tag ya existente, retry sin tag,
  retry exacto y retry conflictivo. La recuperacion es forward-only: npm no se
  reemplaza; un artefacto incorrecto se depreca y se corrige con otra version.
- El recovery publicado resolvio Node `22.23.2` y npm `10.9.8`, confirmado en
  logs y metadata npm. El workflow posterior fija esos valores para que futuros
  reintentos reproduzcan la misma normalizacion y `dist.integrity`.
- Las guias secundarias enlazan al Quick Start canonico y ya no ejecutan `main`,
  documentan flags inexistentes ni atribuyen escrituras al MCP read-only.
- Los tests Bash y PowerShell usan directorios temporales unicos para evitar
  carreras cuando varios verificadores se ejecutan en paralelo.
- El comando publico instala `opencode-memory-adapter@1.10.0` y el contrato
  documental impide reintroducir el pin `1.9.0`.
- Un proceso aislado con un CLI Ollama sin `embed` verifica la deteccion real,
  ademas del test funcional de fallback textual.
- CodeQL conserva SARIF cuando Code Scanning no esta disponible, resuelve reglas
  driver/extension y falla cerrado ante metadata desconocida o severidad alta.
- Lectura de estado y locks usa descriptores estables; locks obsoletos requieren
  limpieza explicita para evitar dos recuperaciones concurrentes.
- Metricas rechaza symlinks, exige archivo regular y aplica permisos `0600`.

## Publicacion remota

- Commit del workflow de recovery: `ae4a911cc5eaaee15f6a1206fed00c3077ffb0e1`.
- CI de `main`: <https://github.com/Rukawua26/opencode-ecosystem/actions/runs/32585330953>.
- CodeQL del commit publicado `aa119ef`: <https://github.com/Rukawua26/opencode-ecosystem/actions/runs/32512238886>.
- CodeQL del workflow de recovery `ae4a911`: <https://github.com/Rukawua26/opencode-ecosystem/actions/runs/32585330966>.
- Recovery exitoso: <https://github.com/Rukawua26/opencode-ecosystem/actions/runs/32585511443>.
- `v1.10.0` permanece en `aa119ef0db12fa168cabe468ad7c5c1fab86eeba`.
- GitHub Release: <https://github.com/Rukawua26/opencode-ecosystem/releases/tag/v1.10.0>.
- `@rukawua26/opencode-memory-adapter@1.10.0`: publicado con `gitHead=aa119ef0db12fa168cabe468ad7c5c1fab86eeba`.
- `@rukawua26/opencode-skills@1.10.0`: publicado con `gitHead=aa119ef0db12fa168cabe468ad7c5c1fab86eeba`.
