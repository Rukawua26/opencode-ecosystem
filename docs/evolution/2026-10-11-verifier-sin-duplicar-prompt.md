---
nombre: 2026-10-11-verifier-sin-duplicar-prompt
fecha: 2026-10-11
estado: en_observacion
afecta: [control]
fuente: propio
---

# Verifier sin duplicar el prompt del worker

## Por que
Medido en la cola real de tareas del plano de control: el prompt de `odd-verifier`
duplicaba literalmente el prompt completo de `odd-worker` en 5/5 pares encadenados
(~600 chars, ~150-250 tokens por cadena). Esa informacion ya estaba en el documento
ODD que el verifier recibe por ruta.

## Antes
`runner.py` construia el verifier con `Tarea original: {task['prompt']}` siempre,
aunque hubiera documento ODD.

## Despues
Con `feature` (doc ODD) el verifier localiza la tarea en el documento (sin texto
duplicado). Sin `feature` conserva el texto original (es la unica referencia).

## Beneficio
~600 chars menos de prompt por cadena de verificacion. No cambia el contrato ni
las comprobaciones: solo quita redundancia medida.

## No regresion
- Contrato `RESULT/SUMMARY/QUESTION`, fail-closed y encadenamiento worker->verifier
  intactos. Sin `feature` se comporta igual que antes.
- Tests: `test_verifier_inherits_contract` (nueva semantica) y
  `test_verifier_keeps_original_task_without_doc` (caso borde).
- Rollback: revertir solo el bloque condicional en `control/runner.py`.

## Verificacion
- Suite `python3 -m unittest discover -s control/tests` -> 234 OK (1 skipped).
- `./opencode-ecosystem status` -> `[ok] sin drift`.
- `scripts/qa-gate.sh --strict` exit 0. `./verify.sh` -> `[ok] verify verde`.
- Medicion antes: media verifier 977 chars con duplicacion; despues, la cadena
  nueva solo recibe documento+checks.

## Periodo prudencial
- 7 dias sobre delegaciones reales. Estable si el verifier localiza bien la tarea;
  revertir si hay imprecision o perdida de hallazgos concretos.
