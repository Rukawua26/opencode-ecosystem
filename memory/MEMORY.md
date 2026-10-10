# MEMORY.md — Índice de memoria técnica (001-ecosystem-lite)

> Flujo: `observations.log` (scribe) → `kairos.sh` cada 30min (scout) → `autodream.sh` en idle (consolidador) → este índice (librarian).
> Sin Docker, sin vector DB, sin CodeMEM pesado. Solo Markdown + Bash. Máquina: i5-1235U, 8GB RAM.

## Topics
- `decisiones.md`, `lecciones.md`, `preferencias.md` (destila `autodream.sh` con dedup; si no hay señal, no escribe)

## Decisiones
- 2026-09-29: memoria-señal (ram-guard a log propio, kairos solo con señal, autodream a 3 fijos sin `inbox-*`) + plantilla `docs/instruccion-perfecta.md`. Base `67dbb55`.
- 2026-09-11: base `noffolo/opencode-ecosystem`, adaptación lite. Ver `~/docs/sources/noffolo-ecosystem-analysis.md`.
- 2026-09-11: DCP 32-40k (no 80k), modelos locales solo 1-3B, qa-gate en warn.

## Raw
- Ver `observations.log` (podar con `node ~/tools/memory_prune.js --dry-run` y luego `--apply` si crece).
