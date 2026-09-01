# Verify 014

## AC1 — status read-only con drift real: PASS
`opencode-ecosystem status` reporta por categoria (agents, commands, plugins,
plugins.disabled, lib, mcp, tools, profiles, skills) missing/modified/extra,
estado del repo y doctor. `--json` produce estructura estable. Test: snapshot
de HOME antes/despues identico; detecta modified y missing. Normaliza el
placeholder `__OPENCODE_DIR__` de perfiles (template vs ruta expandida) y solo
compara el subset desplegado de tools.

## AC2 — sync controlado: PASS
`sync` (dry-run por defecto) delega en `install.sh --sync --skip-memory`;
`--apply` aplica y ejecuta doctor post-sync. Backups gestionados por el
instalador.

## AC3 — config-apply con backup: PASS
Backup timestamp (`opencode.jsonc.bak-<ts>`) antes de reemplazar. Test verifica
que `--dry-run` no escribe y que `--apply` respalda y reemplaza.

## AC4 — capture whitelist: PASS
Solo agents/commands/plugins/plugins.disabled/lib/skills. Test: `--dry-run` no
escribe, `--apply` copia, y `.env`/`node_modules` jamas aparecen.

## AC5 — publish seguro: PASS
Secret scan (sk-/ghp_/gho_/npm_/AKIA/PRIVATE KEY/api-key=) ANTES de validar;
rechaza y no deja nada stageado/commiteado. Luego `npm test`, `lint`,
`check-docs`, `bash -n`. `--yes` para no interactivo; `--wait-ci` opcional.

## AC6 — Suites y CI
- tests/ecosystem-cli.test.sh: 7/7 PASS.
- install.test.sh: nuevos asserts (spec.md command + bin opencode-ecosystem + help) PASS.
- Vitest, RDD, router, hooks, shellcheck, lint, check-docs verdes.
- CI y CodeQL tras push.

## Errores corregidos durante la iteracion
1. `--repo` solo se parseaba antes del subcomando -> parseo global.
2. Comparador usaba listas planas: skills/mcp/profiles son arboles -> `tree_files`.
3. `list_files` renombrado dejo 2 usos colgados en capture/config-apply.
4. `[[ ]]` finales con `set -e` retornaban 1 -> convertidos a `if`.
5. `help` exigia repo -> validacion solo para comandos que lo necesitan.
6. Comandos SDD personales (8) no estaban en el repo: capturados en
   config/commands para que el ecosistema sea la fuente real.
7. Perfiles: diff solo por placeholder -> normalizacion al comparar.

## Decisiones
- Los 8 comandos SDD del runtime se integraron a la distribucion (sin
  secretos ni rutas personales).
- context-stats.js/memory-edges.js siguen como extras personales (informados
  como drift esperado).
- Timer: se documenta cron opt-in; no se instala watcher.
