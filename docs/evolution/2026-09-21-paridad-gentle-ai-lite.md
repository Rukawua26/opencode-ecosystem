---
nombre: 2026-09-21-paridad-gentle-ai-lite
fecha: 2026-09-21
estado: aplicado
afecta: [skills, configs, scripts, docs]
fuente: gentle-ai
---

# Paridad conceptual gentle-ai v3.4 (lite)

## Por que
gentle-ai avanzo de `eae8fadd5ece` (v3.1.0, baseline nuestro) a `d45bc428f515`
(main 2026-09-21) y publico `v3.2.1`-`v3.4.0`: delegacion ODD obligatoria,
review assess con `next_transition`, fail-closed en errores de review y RDD
activado por defecto. Nuestro contrato ODD tenia la forma pero no el endurecimiento:
SUMMARY/QUESTION podian faltar, la continuacion no era verificable y no habia
recibo por tarea.

## Antes
- `RESULT: success` sin `SUMMARY` cerraba en `done`.
- `RESULT: blocked` sin `QUESTION` quedaba `waiting` indistinguible.
- No existia `NEXT_TRANSITION`; la regla "ejecuta verbatim" era solo documental.
- Sin recibo `receipt` por tarea completada.
- Skill no obligaba a delegar: el padre podia implementar trabajo sustancial inline.

## Despues
- Runner fail-closed: `success` sin `SUMMARY` o `blocked` sin `QUESTION` =
  error de contrato (reintento, nunca `done`).
- `NEXT_TRANSITION: <comando>` en la salida del agente se ejecuta verbatim por
  bash antes de cerrar; si falla, `error_kind=transition` y la tarea no queda
  `done`. La transicion viaja en stdout acotado (sin columna SQLite).
- Recibo `receipt` con estado `success` y nota `task #N <summary> [verifier pending]`
  por cada tarea `done`.
- Skill item 7: delegacion obligatoria para trabajo ODD sustancial; el inline
  queda para cambios pequenos sin documento.
- Prompts de `odd-worker`/`odd-verifier` declaran el contrato completo.
- Test nuevo: `opencode` ausente falla explicito como `infra` (guard de runtime).

## Beneficio
- Paridad conceptual con v3.4 sin adoptar su maquinaria (RDD nativo, Engram,
  telemetria, TUI, Go, worktrees candidatos).
- Cero dependencias, cero procesos nuevos, cero migracion SQLite, cero tokens
  extra al arranque (solo texto de prompts existentes).

## No regresion
- 108/108 tests previos + 8 nuevos = 116/116 verdes.
- `sync --apply` sin drift; runtime actualizado.
- `verify.sh` verde; `qa-gate.sh --strict` exit 0.
- Estados/errores previos intactos: provider no consume intento, verification_command
  determinista, scrub de sensibles, purga de payloads.

## Verificacion
- `python3 -m unittest discover -s control/tests` → 116/116 OK.
- `python3 validate-skills.py skills` → `[ok] 10 skills valid`.
- `./opencode-ecosystem sync --apply && ./opencode-ecosystem status` → `[ok] sin drift`.
- `./verify.sh` → verde; `./scripts/qa-gate.sh --strict` → exit 0.
- Documento ODD: `odd/tasks/gentle-ai-parity-lite.md` con RED/verde y evidencia.

## Periodo prudencial
- Duracion: hasta 2026-10-05 o 2 features sustanciales delegadas con dogfood real.
- Estable si: ninguna tarea sustancial queda `done` sin SUMMARY visible; bloqueos
  llevan siempre QUESTION; NEXT_TRANSITION solo aparece en comandos revisables.
- Revertir si: contrato estricto genera falsos `contract` en trabajo legitimo —
  rollback = revertir `runner.py` a pre-feature y quitar los items 7/8 endurecidos.
- Base reversible: estado previo en Git (commit `2c711e0`); specs anteriores se
  conservan como historial.

## Fuente
- `~/docs/sources/gentle-ai-analysis.md` (seccion Revision 2026-09-21, baseline
  `eae8fadd5ece..d45bc428f515`, established `v3.4.0`).
