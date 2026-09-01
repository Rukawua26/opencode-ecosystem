# Feature 014: Ecosystem As Source Of Truth

## Problema

`opencode-ecosystem` es la fuente canonica pero no existe un flujo operativo
reproducible para: ver el estado de sincronizacion, aplicar actualizaciones,
recuperar cambios manuales o publicar. El usuario puede editar directamente
`~/.config/opencode`, crear drift silencioso y publicar errores o secretos.

## Alcance

IN:

- CLI `opencode-ecosystem` con subcomandos `status`, `sync`, `config-apply`,
  `capture` y `publish`.
- `status`: read-only, sin efectos secundarios; reporta drift por categoria,
  estado del repo y salud del runtime (doctor).
- `sync`: reutiliza `install.sh --sync` (dry-run por defecto, `--apply` para
  aplicar), con backup y doctor post-sync.
- `config-apply`: reemplazo explicito de `opencode.jsonc` y perfiles con backup.
- `capture`: copia inversa runtime→repo SOLO de archivos publicos gestionados
  (whitelist), con dry-run y rechazo de privados.
- `publish`: validaciones (tests, lint, check-docs, shellcheck, secretos),
  commit y push explicitos (`--yes` para no interactivo).
- Instalacion del binario en `~/.opencode/bin/opencode-ecosystem`.
- Tests bash del CLI.
- Timer/deteccion periodica: se documenta un cron opt-in de `status` (no se
  instala un watcher).

OUT:

- Sincronizacion bidireccional automatica.
- Commit/push automatico sin confirmacion.
- Reemplazo automatico de `opencode.jsonc`.
- Merge automatico de JSONC.
- Publicacion de `.env`, memoria, receipts, logs o backups.
- Activacion de plugins opt-in.

## Criterios de aceptacion

- AC1: `opencode-ecosystem status` es read-only (sin escrituras) y reporta
  drift real (modificados, faltantes, extra) por categoria.
- AC2: `opencode-ecosystem sync` (dry-run) no modifica nada; `--apply` actualiza
  el runtime y deja el doctor en verde.
- AC3: `config-apply` respalda antes de reemplazar y nunca borra el original.
- AC4: `capture` rechaza archivos privados/protegidos y solo copia la whitelist.
- AC5: `publish` falla si hay secretos, repo sucio en paths no gestionados o
  validaciones fallidas; requiere `--yes` o confirmacion.
- AC6: CI verde y commit unico de cierre.