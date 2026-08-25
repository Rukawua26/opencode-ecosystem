# Feature 010: Analisis estatico de workflows y scripts en CI

## Objetivo

Blindar la CI con analisis estatico ejecutable (`actionlint` y `shellcheck`)
para que los contratos de workflows dejen de depender solo de guards regex y
los scripts Bash del repo no regresen a patrones inseguros.

## Criterios de aceptacion

- AC1: El job `test` (ubuntu) de `.github/workflows/test.yml` ejecuta
  `actionlint` sobre todos los workflows con salida limpia.
- AC2: El mismo job ejecuta `shellcheck --severity=warning` sobre
  `install.sh`, `tools/scripts/*.sh` y `tests/*.sh` sin hallazgos.
- AC3: La version de `actionlint` esta pineada (`ACTIONLINT_VERSION`) y su
  tarball se verifica contra el `checksums.txt` oficial antes de usarse.
- AC4: `tools/scripts/check-workflow.js` valida estructuralmente el workflow
  parseado (matriz con ubuntu, gates exactos, comandos e invariantes); un test
  ejecutable con mutaciones (`tests/workflow-static-analysis.test.mjs`)
  demuestra que las mutaciones rechazables se rechazan.
- AC5: Las suites locales existentes (`lint`, `check-docs`, `test:release`,
  `npm test`, `test:install`) permanecen verdes.

## Decisiones

- **Descarga directa con checksum en lugar de action de terceros**: la action
  `rhysd/actionlint-action` referenciada en el plan original no existe; la
  alternativa `reviewdog/action-actionlint` anade el framework reviewdog como
  dependencia extra. Se elige descargar el binario oficial pineado a version
  y verificarlo contra `checksums.txt`: mismas garantias de integridad, cero
  dependencias nuevas (solo `curl`, `sha256sum`, `tar` preinstalados).
- **Severidad warning**: `shellcheck --severity=warning` bloquea errores y
  warnings reales; los hallazgos info/style actuales (SC2015 x5 en la seccion
  verify de install.sh, SC2012/SC2129 en tests) quedan aceptados y
  documentados para evitar churn sin valor.
- **Alcance de shellcheck**: solo archivos que se ejecutan en maquinas de
  usuarios/releases (`install.sh`, `tools/scripts/*.sh`, `tests/*.sh`);
  los hooks locales fuera del repo quedan fuera de alcance.

## Correcciones de linea base (hallazgos shellcheck reales)

- `.github/workflows/test.yml`: patrones `A && B || C` reescritos como
  `if` explicitos en el gate CodeQL del preflight y en la verificacion
  post-publicacion npm (SC2015); variable `attempt` sin uso eliminada
  (SC2034).
- `.github/workflows/dependabot-automerge.yml`: `PR_REF` asignado y nunca
  usado, eliminado (SC2034).
- `install.sh`: `rm -rf` con guard `"${var:?}"` (SC2115), `local` dividido
  de su asignacion (SC2155) y raiz de backups
  `~/.local/share/opencode/install-backups` endurecida: se valida con
  `assert_no_symlink_components` **antes** de `mkdir -p` (en `backup_sync_file`)
  y antes de enumerar/enumerar-borrar (en `retain_install_backups`); cada
  nombre de backup se rechaza si contiene `/`, de modo que ningun borrado ni
  respaldo sale de la raiz.
- `tests/install.test.sh`: variables muertas `current` y `stats` eliminadas;
  test nuevo que prueba que la retencion de backups falla cerrado ante un
  root con symlink sin tocar el destino externo.
- `tests/release-workflow.test.sh`: directiva `disable=SC2154` documentando
  la variable proveniente de `source` dinamico.

## Correcciones tras revision (lentes FAIL, ronda 1)

- Los pasos de analisis estatico se restringen a `matrix.os ==
  'ubuntu-latest'`: el binario descargado es `linux_amd64` y no existe en
  macOS.
- Guards endurecidos con lineas completas ancladas en `check-docs.js`:
  rechazan `|| true`, versiones hardcodeadas en la URL, perdida de la
  condicion ubuntu-only y debilitacion del comando shellcheck (probes de
  mutacion verificados).
- Retencion de backups validada tambien antes de `mkdir -p` en
  `backup_sync_file`, no solo en `retain_install_backups`: el sync falla cerrado
  ante un root con symlink sin escribir ningun respaldo tras el enlace
  (test incluido).
- Guards anti-bypass: ningun paso de analisis estatico puede llevar
  `continue-on-error` (probes de mutacion verificados).
- Los guards regex alcanzaban su limite contra YAML valido con otro orden de
  claves, matriz sin ubuntu o `continue-on-error` a nivel job. La validacion
  pasa a ser estructural: `check-workflow.js` parsea el YAML y exige los
  invariantes exactos; `tests/workflow-static-analysis.test.mjs` ejecuta
  mutaciones (nivel job, nivel step en cualquier orden de claves, matriz,
  comandos debilitados, checksum ausente) y exige rechazo. Dependencia
  anadida: `yaml` (devDependency, pura JS).
- Ronda final de revision: `continue-on-error` se rechaza por **presencia**
  (cualquier valor, incluidas expresiones `${{ ... }}`), `matrix.exclude` esta
  prohibido por completo, el script de actionlint se exige **canonico**
  (`set -euo pipefail`, `mktemp -d` privado, descarga, verificacion sha256
  antes de extraer, ejecucion) y cualquier alteracion de una sola linea lo
  invalida. Los pasos invocadores (`npm run check-docs` incondicional,
  `npm run test:release` con gate ubuntu) quedan dentro del contrato.
  Mutations: 24/24 rechazadas. `continue-on-error` prohibido en **todos**
  los pasos del job, no solo los protegidos (ningun test puede silenciarse).
  Igualmente, `shell` esta prohibido en todos los pasos y `if` solo admite
  el gate ubuntu en cualquier paso: ningun test puede saltarse ni ejecutarse
  bajo un shell que suprima fallos.
- Ronda de cierre: `runs-on` debe ser `${{ matrix.os }}`; `container`
  prohibido en el job de analisis (un contenedor podria sustituir
  `curl`/`sha256sum`/`tar`/`shellcheck`); la matriz es **exacta**
  (`os: [ubuntu-latest, macos-latest]`, `node-version: [22]`, sin
  `exclude`/`include`) para que la cobertura macOS no pueda eliminarse.
- **Modelo de amenaza**: el contrato es anti-regresion. Previene mutaciones
  accidentales y subrepticias (PRs, copy-paste, cambios de formato) de cada
  nivel de meta-configuracion alcanzado: contenido, gates, env, shell,
  orden, triggers, matriz y prefijo confiable. Quien pueda hacer push al
  repositorio puede borrar el propio checker; la barrera para ese adversario
  es la revision humana, no este mecanismo. Se acepta explicitamente este
  limite: blindar contra ese actor requeriria un check externo al repo
  (fuera de alcance del plan de GitHub actual).
- **Orden de confianza**: actionlint (binario verificado con checksum) y
  shellcheck (binario del runner) corren **antes** de `npm ci`, porque no
  ejecutan codigo del repo; ninguna mutacion de `install`/`lifecycle scripts`
  puede precederlos. `npm ci` usa `--ignore-scripts` solo en los contextos
  ya existentes.
- Prohibiciones estructurales: `if`/`defaults`/`env`/`continue-on-error`/
  `timeout-minutes` a nivel job y workflow; `shell`/`working-directory`/
  `continue-on-error`/`timeout-minutes` en pasos protegidos; triggers de
  forma **exacta** (push/PR con branches exactas `main`+`develop`, sin
  `paths`/`paths-ignore` ni triggers extra); `env` exacta en pasos
  protegidos (actionlint solo `ACTIONLINT_VERSION`); nombres de paso
  protegidos sin duplicados.
- **Prefijo confiable exacto**: steps[0..2] son obligatoriamente checkout
  pineado al SHA aprobado (`actions/checkout@3d3c42e…`, `ref` al
  `source_sha` del preflight, `persist-credentials: false`), actionlint y
  shellcheck. Ningun paso con `run` puede insertarse antes de los
  analizadores; cualquier codigo del repo se ejecuta solo despues.
  `workflow_dispatch` declara exactamente `version` (required) y
  `release_sha` (opcional).
- **Alcance del analisis por plataforma**: actionlint/shellcheck corren en
  el leg ubuntu sobre el checkout del commit aprobado por el preflight; el
  contenido analizado es identico al de macOS/Windows (mismo `source_sha`).
  Esos legs ejecutan `npm ci` sin analisis previo, pero no liberan
  artefactos y el job `release` espera a que todos los legs pasen.

## Fuera de alcance

- Proteccion de tags `refs/tags/v*` en GitHub: requiere plan Pro o repo
  publico (API responde 403). Decision: deteccion-only mediante las
  verificaciones exactas de tag antes/despues de cada operacion irreversible,
  ya implementadas en la feature 009.
- Entrada en CHANGELOG: diferida a la proxima release.
