# Plan 014

1. CLI bash `tools/scripts/opencode-ecosystem.sh` con subcomandos.
   Reutiliza `install.sh` (sync), `opencode-doctor.sh` (status), manifest y
   categorias de archivos. Sin dependencias nuevas.
2. `status`: mapeo explicito categoria→par de directorios (agents, commands,
   plugins, plugins.disabled, lib, mcp-src, profiles, skills, tools, config);
   compara con `cmp`; reporta opencode.jsonc como drift informativo (protegido).
   Con `git status`/ahead-behind para el repo. `--json` para salida estructurada.
3. `sync`: envuelve `install.sh --sync --skip-memory [--dry-run]`.
4. `config-apply`: backup con timestamp + copia de config/opencode.jsonc y de
   perfiles; dry-run previo.
5. `capture`: whitelist de categorias publicas; dry-run lista; `--apply` copia.
   Rechaza siempre `.env`, `node_modules`, backups, receipts, DB, logs.
6. `publish`: secretos (grep sk-/ghp_/claves), `npm test`, `npm run lint`,
   `npm run check-docs`, `bash -n`, shellcheck del script; commit+push con
   `--message`; `--yes` para no interactivo; `--wait-ci` opcional.
7. Instalacion en install.sh (bin + verify).
8. Tests `tests/ecosystem-cli.test.sh` en HOME temporal.
9. Docs README + AGENTS (flujo oficial) y verify.md.

Rechazado: watcher permanente, publish automatico, merge JSONC, sync inverso
automatico, subida de privados.