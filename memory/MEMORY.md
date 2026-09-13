# MEMORY.md — Índice de memoria técnica (001-ecosystem-lite)

> Flujo: `observations.log` (scribe) → `kairos.sh` cada 30min (scout) → `autodream.sh` en idle (consolidador) → este índice (librarian).
> Sin Docker, sin vector DB, sin CodeMEM pesado. Solo Markdown + Bash. Máquina: i5-1235U, 8GB RAM.

## Topics
- (vacío — `autodream.sh` creará `topics/*.md` al consolidar)

## Decisiones
- 2026-09-11: base `noffolo/opencode-ecosystem`, adaptación lite. Ver `~/docs/sources/noffolo-ecosystem-analysis.md`.
- 2026-09-11: DCP 32-40k (no 80k), modelos locales solo 1-3B, qa-gate en warn.

## Raw
- Ver `observations.log` (podar con `node ~/tools/memory_prune.js --dry-run` y luego `--apply` si crece).
