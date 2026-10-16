---
nombre: 20261015-panel-subagentes-nombre
fecha: 2026-10-15
estado: aplicado
afecta: [scripts]
fuente: propio
---

# Panel: nombre real de los subagentes declarados

## Por que
`control/collect.py` extraia los subagentes de `configs/opencode.jsonc` con una
regex que permitia cruzar llaves (`[^}]*?`). Como `agents` envuelve a
`odd-worker`, el contenedor se llevaba la descripcion del primer hijo y el panel
mostraba un subagente llamado `agents` en lugar de `odd-worker`. Evidencia:
`_parse_opencode_subagents` devolvia `agents` + `odd-verifier` (2026-10-15).
El recuento (2) era correcto; el nombre, no.

## Antes
Dos componentes, uno con nombre falso (`agents`).

## Despues
La regex no cruza llaves anidadas: devuelve `odd-worker` y `odd-verifier`.

## Beneficio
El panel deja de atribuir a un componente inexistente; evita confusion al
auditar agentes. Sin cambios de contrato ni de esquema.

## No regresion
- Sigue siendo observacion read-only por regex, sin dependencias.
- Los 2 subagentes y sus descripciones se siguen listando.
- Version anterior recuperable en Git (blob previo de `control/collect.py`).

## Verificacion
- `python3 -c` sobre `_parse_opencode_subagents('.')` -> `odd-worker`,
  `odd-verifier`.
- `python3 -m unittest discover -s control/tests` -> 342 tests OK, 1 skipped.
- `scripts/qa-gate.sh --strict` -> rc 0. `./verify.sh` -> verde.
- `./opencode-ecosystem status` -> `[ok] sin drift`.

## Periodo prudencial
- Estable: el panel lista `odd-worker`/`odd-verifier` tras la siguiente
  recoleccion.
- Rollback: `git checkout <blob>` del fichero y reiniciar el panel.
