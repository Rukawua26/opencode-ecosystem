# Verifier sin duplicar el prompt del worker (verifier-sin-duplicar-prompt)

## Objetivo
Eliminar la duplicacion medida del prompt de `odd-worker` dentro del prompt de
`odd-verifier`, conservando la referencia ODD y los checks de seguridad.

## Problema y por que
Medido en la cola real (`~/.local/share/opencode-control/control.db`, read-only,
2026-10): el verifier promedia ~977 chars y en **5/5 pares** encadenados contiene
literalmente el prompt completo del worker (~600 chars, ~150-250 tokens por
cadena). Esa informacion ya existe en el documento ODD (`odd/tasks/<feature>.md`)
que el verifier recibe por ruta. La duplicacion es coste repetido de tokens de
salida/entrada sin valor de seguridad.

## Alcance
### Incluye
- `control/runner.py`: con `feature` (doc ODD presente) el prompt del verifier
  ya no incluye `Tarea original: <prompt>`; instruye localizar la tarea en el
  documento. Sin `feature` (sin doc), conserva el texto original (unica
  referencia del verifier).
- `control/tests/test_leases.py`: `test_verifier_inherits_contract` actualiza la
  asercion a la nueva semantica; nuevo `test_verifier_keeps_original_task_without_doc`
  como red del caso borde.

### Excluye
- Prompt del worker (ya referencia el documento). Contexto de sistema de los
  agentes, paralelismo (2 workers) y jobs en background: no justificados por la
  medicion. Migracion de esquema SQLite, skills nuevas, commit/push.

## Restricciones
- Python stdlib; sin dependencias. i5-1235U/8GB.
- Contrato `RESULT/SUMMARY/QUESTION`, fail-closed y encadenamiento worker->verifier
  intactos. No romper: respectar `Documento ODD` y formato del prompt para el
  verifier en contexto fresco.

## TDD
- Modo: off. Fuente: default (tests ya existentes en `control/tests`).
- Runner: `python3 -m unittest control.tests.test_leases` + suite completa.

## Tareas
- [x] T1 - Medir duplicacion real en la cola (5/5 pares, ~600 chars, evidencia).
- [x] T2 - Cambio condicional en `_run_verification` (runner.py) + typo `terea`->`tarea`.
- [x] T3 - Tests de contrato (con/sin documento ODD) verdes.
- [x] T4 - Suite completa 234 OK, status sin drift, qa-gate exit 0, verify.sh verde.
- [x] T5 - Observacion (cerrada 2026-10-12 con delegacion real post-cambio).

## Decisiones aceptadas
- 2026-10: solo se elimina la duplicacion; se conserva ruta ODD + ID de worker.
- 2026-10: sin paralelismo ni background (no hay evidencia de bloqueo real).

## Evidencia
- Medicion cola real: 5/5 pares con duplicacion; ahorro medido ~600 chars por
  verificacion (~150-250 tok). Media worker 602 chars, verifier 977 chars.
- `python3 -m unittest control.tests.test_leases` -> 12/12 OK.
- `python3 -m unittest discover -s control/tests` -> 234 OK (1 skipped).
- `./opencode-ecosystem status` -> `[ok] sin drift`; `qa-gate --strict` exit 0;
  `./verify.sh` -> `[ok] verify verde`.

## Progreso
- Estado: cerrada (2026-10-12).
- Ultima tarea: T5 observado. Delegaccion real post-cambio: verificador #17
  (parent #14, feature gentle-ai-parity-lite) ejecutada 2026-10-11T19:02,
  despues del commit 8469039, con `RESULT: success`, rc=0 y nota
  "Sin hallazgos.". El verificador localizo la tarea desde el documento ODD;
  sin el bloque duplicado del prompt el ciclo completo funciono. Los prompts se
  purgan al terminar, asi que no hay texto para medir de nuevo; el cierre es
  por comportamiento observado, no por re-medicion.
- Se vigilara si aparece imprecision en futuras delegaciones; en ese caso se
  revierte solo el bloque de `_run_verification`.
- Bloqueos: ninguno.
