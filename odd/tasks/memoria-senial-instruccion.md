# Memoria-señal + instruccion perfecta

## Objetivo

Menos ruido en `observations.log`, memoria que destila a 3 ficheros fijos
con dedup, y plantilla de instruccion reutilizable. Paridad lite con
gentle-ai, sin su peso (sin Engram/vector, TUI, multi-runtime, telemetria).

## Problema y por que

- `observations.log` (153 lineas el 2026-09-29) dominado por cabeceras
  `### kairos` vacias cada 30 min y lineas `ram-guard` cada 5 min.
  Quien lo sufre: el scout/consolidador y cualquier sesion que lea memoria.
- `autodream.sh` movia `head -200` a `inbox-FECHA.md`: acumula, no destila.
- Sin plantilla de instruccion, cada peticion define contexto/rol/formato
  a su manera y gasta tokens.

## Alcance

### Incluye

- `scripts/ram-guard-lite.sh`: log propio `ram-guard.log`.
- `memory/kairos.sh`: solo escribe si hay señal en el staged diff.
- `memory/autodream.sh`: destila a `decisiones.md / lecciones.md /
  preferencias.md` con `grep -Fqx`; si no hay señal, no escribe.
- `docs/instruccion-perfecta.md`: plantilla de 7 campos.
- Doc de evolucion con rollback.

### Excluye

- Migrar `control/db.py`, skills nuevas, tocar `configs/cron-jobs.json`,
  `scripts/hygiene.sh`, commits/push/PR, vector DB, dependencias nuevas.

## Restricciones

- Python stdlib solamente; bash existente en memoria.
- i5-1235U/8GB: cero procesos permanentes ni polling agresivo.
- Espanol en docs; sin acentos en contenido de skills (no se tocan skills).

## No romper

- Tests `control/tests`, `validate-skills.py skills`, `./verify.sh`,
  `qa-gate.sh --strict`, `status sin drift` antes y despues del sync.

## Tareas

- [x] T1 - `ram-guard-lite.sh`: redirigir echo a `ram-guard.log`.
- [x] T2 - `kairos.sh`: guarda fail-closed (sin señal -> exit 0 sin escribir).
- [x] T3 - `autodream.sh`: 3 ficheros fijos con dedup, sin `inbox-*`.
- [x] T4 - `docs/instruccion-perfecta.md` (7 campos + ejemplo lleno).
- [x] T5 - Evolution doc + verificacion completa + sync.
- [ ] T6 - Observacion 7 dias: log sin ruido, topics sin `inbox-*`,
      plantilla usada en 3 tareas reales, 1 decision nueva.

## Verificacion

- `bash -n` en los 3 scripts.
- `python3 -m unittest discover -s control/tests`.
- `python3 validate-skills.py skills`.
- `./opencode-ecosystem status` -> `[ok] sin drift` (antes y despues).
- `./verify.sh` verde y `scripts/qa-gate.sh --strict` exit 0.
