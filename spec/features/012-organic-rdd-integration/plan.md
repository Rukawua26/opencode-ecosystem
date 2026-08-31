# Plan

## Decisiones

- Copia autorizada desde opendotfile (contenido ya verificado con 183/183
  tests y revision independiente sin findings), adaptando solo imports del
  layout (`tests -> config/lib`, `tests -> config/plugins`).
- Tests con `node --test` (mismo estilo que memory-adapter/router), integrados
  en CI linux/mac/windows.
- `@opencode-ai/plugin` pasa a `dependencies` del repo y se instala en
  `~/.config/opencode/node_modules` durante el install (carga real de plugins).
- Hook RDD en `hooks/pre-commit`; instalacion opt-in con `--with-rdd-hook`;
  conserva y respalda hooks existentes, nunca toca `post-commit`.
- `opencode.jsonc` principal y perfiles declaran los 5 plugins nucleo; los
  plugins opcionales (`personalities`, `kanban`, `sandbox`, `auto-memory`)
  quedan fuera del default pero siguen distribuidos en `config/plugins/`.
- Migration del runtime: `--sync` no suficiente para `opencode.jsonc` (se
  preserva siempre); se actualiza manualmente tras backup en la sesion.

## Archivos

### Portados (desde opendotfile)

- `config/lib/organic-rdd.js` <- `opendotfile/lib/organic-rdd.js`
- `config/plugins/organic-rdd.js` <- `opendotfile/plugins/organic-rdd.js`
- `config/commands/review-*.md` (8) <- `opendotfile/commands/review-*.md`
- `hooks/pre-commit` <- `opendotfile/hooks/pre-commit`
- `tests/organic-rdd.test.js`, `tests/organic-rdd-plugin.test.js`,
  `tests/organic-rdd-gate-hook.test.js` (imports adaptados)

### Modificados

- `config/opencode.jsonc`, `config/profiles/{work,personal,light}/opencode.jsonc`
- `package.json`, `package-lock.json` (dependencia plugin)
- `install.sh` (+ comandos, runtime deps, `--with-rdd-hook`, verify plugin)
- `tests/install.test.sh` (aserciones nuevas)
- `.github/workflows/test.yml` (pasos RDD)
- `README.md`, `docs/README.md` (alinear componentes)

## Verificacion

- `node --check config/lib/organic-rdd.js config/plugins/organic-rdd.js`
- `node --test tests/organic-rdd.test.js tests/organic-rdd-plugin.test.js tests/organic-rdd-gate-hook.test.js`
- `npm test`, `npm run lint`, `npm run check-docs`, `npm run test:router`,
  `node --test packages/memory-adapter/tests/*.test.js`
- `npm run test:install` (HOME temporal)
- Migracion del runtime activo con backup y smoke de carga del plugin.

## Rollback

Restaurar archivos desde Git y el backup `~/.config/opencode.rdd-sync.*`;
no hay migracion de datos ni commits implicados.
