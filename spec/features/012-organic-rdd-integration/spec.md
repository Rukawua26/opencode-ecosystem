# Feature 012: Integracion de Organic RDD en OpenCode Ecosystem

## Problema

El README y la documentacion del ecosistema declaran Organic RDD como componente
activo, pero el repositorio no contiene su implementacion: no hay
`config/plugins/organic-rdd.js`, `config/lib/organic-rdd.js`, comandos
`review-*`, permisos ni tests. La implementacion real y probada vive en
`/home/miguel/opendotfile` (Feature 012: lineage acotado, refuter opcional).
Hay una contradiccion documento/implementacion y una dependencia de dos
repositorios.

## Objetivo

Integrar Organic RDD dentro de `opencode-ecosystem` como componente nucleo, con
instalacion reproducible, perfiles, permisos, comandos y tests en CI, para que
`opendotfile` deje de ser una fuente necesaria.

## Alcance

- Portar `lib/organic-rdd.js` y `plugins/organic-rdd.js` desde opendotfile al
  layout `config/lib/` y `config/plugins/` sin perder ninguna garantia
  verificada (hashes, manifest, project_id, lineage recursivo, scope heredado,
  maximo 2 intentos, `refuter` opcional, gates fail-closed).
- Portar los 8 comandos `review-*` a `config/commands/`.
- Configuracion: los cinco plugins nucleo (`guardrails`, `checkpoints`,
  `validator`, `session-metrics`, `organic-rdd`) en la config principal y los
  tres perfiles; permisos `review_mode_get/review_status/review_validate` en
  allow y mutaciones en ask.
- Declarar `@opencode-ai/plugin` como dependencia explicita e instalable en el
  home de configuracion.
- Portar el hook pre-commit (contenido) con activacion opt-in mediante
  `tools/scripts/install-rdd-hook.sh <repo>`, sin reemplazar hooks existentes.
- Tests: portar suites `organic-rdd.test.js`, `organic-rdd-plugin.test.js` y
  `organic-rdd-gate-hook.test.js` adaptadas al layout; integrarlas en CI.
- Instalador: instalar comandos, RDD y dependencias runtime; verificar carga
  real del plugin.
- Documentacion alineada con la realidad (5 plugins nucleo).

## Fuera De Alcance

- Migracion destructiva de `~/.config/opencode` (solo backup + sync seguro).
- Archivado remoto de opendotfile (Feature 014: solo README historico local).
- Extraccion a paquete npm de Organic RDD.
- Autocorreccion de agentes, event sourcing, firmas remotas, hooks obligatorios.
- Portar cambios SDD locales preexistentes no relacionados.

## Criterios De Aceptacion

- AC1: `config/plugins/organic-rdd.js` y `config/lib/organic-rdd.js` existen y
  pasan `node --check`.
- AC2: Config principal y perfiles cargan exactamente los 5 plugins nucleo y
  definen los permisos review_*.
- AC3: 8 comandos `review-*` presentes en `config/commands/`.
- AC4: Suites RDD portadas pasan en este repo con `node --test`.
- AC5: Suite completa (`npm test`, lint, check-docs, install, hooks, router,
  memory) permanece verde.
- AC6: Instalacion en HOME temporal instala RDD, comandos, lib y el plugin
  carga con `@opencode-ai/plugin` instalado.
- AC7: `tools/scripts/install-rdd-hook.sh <repo>` instala el pre-commit RDD en
  un repo git, respalda un pre-commit previo y no toca `post-commit`.
- AC8: `~/.config/opencode` queda migrado con backup, sin perdida de `.env`,
  memoria, receipts ni plugins extra.
- AC9: README/docs no afirman capacidades ausentes.

## Riesgo

Tier 3: runtime de plugins, instaladores y configuracion central.
