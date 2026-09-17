# 002-gentle-opencode-alignment — Spec

## Problema
`gentle-ai` v2.7.0 (`main df21d32b`, baseline previa `1863432`) trae patrones OpenCode que nos faltan: routing por evidencia, deny-list de seguridad y skill discovery index-first. Sin ellos, cada sesión elige esfuerzo a ojo, secretos sin deny explícito en `edit`/`bash`, y las skills se descubren por lectura directa.

## Alcance
- ENTRA (Lote 1): P1 routing prompt en AGENTS.md, P2 deny-list en `opencode.jsonc` (schema 1.18 verificado), P3 `SKILL_INDEX.md` (retirado posteriormente por spec 006 al confirmar descubrimiento nativo).
- ENTRA (Lote 2, posterior): P5 backups con poda keep-5, P6 store-reset lite.
- FUERA: Engram, binario/TUI Go, Minisign, GGA, themes/personas, background launcher, multi-perfil generado, judgment-day, telemetría. P4 (merge work-unit-commits) condicional.

## Criterios de aceptación
1. `opencode debug config` muestra bloque `permission` con denies sin romper arranque.
2. Deny real: `read`/`edit` sobre `~/.ssh/*` denegado; `bash ssh *` pide aprobación.
3. En la entrega 002, `SKILL_INDEX.md` era el indice por defecto; spec 006 lo reemplaza por descubrimiento nativo para evitar duplicacion.
4. `ecosystem status` sin drift tras sync; nota `gentle-ai-analysis.md` actualizada a `df21d32b` al cerrar.
