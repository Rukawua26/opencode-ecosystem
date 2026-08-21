# Verify: Release v1.10.0 y cierre documental

## Estado

PASS local en Linux. La publicacion y validacion Windows nativa quedan pendientes
del workflow bloqueante de `main`.

## Matriz

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 Versiones 1.10.0 | PASS | Root, workspaces, router, lockfiles e instaladores alineados |
| R2 Checkout reproducible | PASS | README y contrato documental validan `git describe --tags --exact-match` |
| R3 Fuente canonica | PASS | MOC, resumen, alias legado y tres runbooks usan `opencode-ecosystem` |
| R4 Verificacion local | PASS | Suites, coverage, install Bash, hooks, audit, packs, doctor y diff pasan |
| R5 Publicacion | PENDING | Requiere push a `main` y dispatch remoto `version=1.10.0` |
| R6 Fallback Ollama | PASS | Deteccion del CLI incompatible, fallback explicito y 45/45 tests del adapter |
| R7 Windows y CodeQL | PENDING | Correcciones locales listas; requiere repetir ambos workflows remotos |

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

## Limitacion local

`pwsh` no esta instalado en la maquina. `npm run test:install:windows` no pudo
iniciar por ausencia del ejecutable; el workflow Windows nativo es obligatorio
antes de crear el tag o publicar npm.

## Hallazgos corregidos

- El workflow ahora rechaza un tag existente si no apunta a `GITHUB_SHA`.
- La release requiere dispatch y version explicitos, acciones fijadas a SHA y
  npm provenance; una version npm existente debe coincidir en `gitHead`.
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

Pendiente de completar con URL de workflow, tag, GitHub Release y versiones npm.
