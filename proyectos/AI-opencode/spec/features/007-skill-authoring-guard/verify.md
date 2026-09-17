# 007-skill-authoring-guard — verify.md (2026-09-11)

## Evidencia
1. **Validador**: 15/15 fixtures adversas en `/tmp` (frontmatter ausente/sin cerrar,
   nombre inválido, mismatch carpeta, description vacía/>1024/sin trigger, campo
   desconocido, metadata no string→string, cuerpo vacío, duplicados, stray/nested,
   SKILL_INDEX, rutas vacías/inexistentes).
2. **Gates aislados** (HOME falso): sync inválido aborta sin crear `~/.config`;
   publish inválido no reemplaza la fuente; sync válido + status verde.
3. **Gates reales**: `sync --apply` y `publish --yes` imprimen `[ok] 5 skills valid`.
4. **Runtime**: `opencode debug skill` lista las 5 una sola vez desde `skills/`
   + `customize-opencode` integrada.
5. **Integridad**: `verify.sh` verde (valida fuente y runtime), `status sin drift`,
   doctores sanos, timers activos.

## Archivos
- Nuevo: `~/opencode-ecosystem/validate-skills.py` (stdlib, sin red ni YAML).
- Gates pre-mutación en `sync`/`publish`; validación acumulativa en `verify.sh`.
- Política compacta en `AGENTS.md` + sección de autoría en README.

## Acción humana
- Reiniciar la sesión OpenCode para cargar definiciones vigentes.
