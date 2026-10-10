---
nombre: 2026-09-29-memoria-senial-instruccion
fecha: 2026-09-29
estado: aplicado
afecta: [scripts, memoria, docs]
fuente: propio
---

# Memoria-señal + instruccion perfecta

## Por que

`observations.log` con 153 lineas dominado por ruido: cabeceras `### kairos`
vacias cada 30 min y `ram-guard: libre X%` cada 5 min. `autodream.sh` movia
`head -200` a `inbox-FECHA.md` sin destilar. Sin plantilla, cada peticion al
agente define contexto y formato a su manera.

## Antes

- `scripts/ram-guard-lite.sh:7` anexaba a `observations.log`.
- `memory/kairos.sh` escribia cabecera siempre, aun sin señal en el staged diff.
- `memory/autodream.sh:10-16` creaba `topics/inbox-YYYY-MM-DD.md`.
- Sin `docs/instruccion-perfecta.md`.

## Despues

- `ram-guard-lite.sh` escribe a `ram-guard.log` propio; logica `pkill` intacta.
- `kairos.sh` captura `SIGNAL` y hace `exit 0` sin escribir si esta vacia;
  un solo `git diff --staged` para señal + `--stat` solo cuando hay señal.
- `autodream.sh` destila a `decisiones.md / lecciones.md / preferencias.md`
  con dedup `grep -Fqx`; ignora vacias, cabeceras kairos y restos ram-guard;
  conserva truncado del log a 50 lineas.
- Nuevo `docs/instruccion-perfecta.md` (7 campos + ejemplo lleno).

## Beneficio

Menos lineas basura por dia (~48 cabeceras kairos + ~288 ram-guard dejan de
entrar al log), topics acotados a 3 ficheros, instrucciones con formato fijo
(menos idas y vueltas, menos tokens).

## No regresion

- Base reversible: commit `67dbb55` (arbol limpio antes del cambio).
- `ram-guard` sigue matando `ollama run` huerfanos bajo 15%; solo cambia el
  destino del log. Schedules de `configs/cron-jobs.json` intactos.
- `kairos` mantiene el mismo patron de señal; `autodream` mantiene
  `mkdir -p`, truncado a 50 y ejecucion solo en idle sin red ni modelos.
- `topics/` y `observations.log` siguen sin sincronizarse.

## Verificacion

- `bash -n` en los 3 scripts.
- Sandbox con `HOME` falso: kairos sin staged diff no escribe (log 153->153);
  autodream clasifica `Se decide/se decide/Acuerdo`, `Leccion/FIX/ERROR/Error`,
  `Prefiero/siempre`, ignora resto y no duplica en 2a pasada.
- Correcciones aplicadas tras sandbox: `*se decide` -> `*[Ss]e decide*`;
  suma `*FIX*` y `*ERROR*` (el `case` es sensible a mayusculas).
- Matiz de despliegue: `sync --apply` NO propaga `memory/*.sh` existentes
  (`opencode-ecosystem:66-68`, por diseño); se copiaron a mano fuente->runtime
  y se verifico `diff` 3/3 igual. `status` no compara `memory/` (`:29-40`).
- `python3 -m unittest discover -s control/tests` -> 182 tests OK (1 skipped).
- `python3 validate-skills.py skills` -> 11 valid.
- `./opencode-ecosystem status` -> `[ok] sin drift` (antes y despues).
- `./verify.sh` verde y `scripts/qa-gate.sh --strict` exit 0.

## Periodo prudencial

- 7 dias. Estable si: log sin `ram-guard` ni cabeceras vacias, `topics/` sin
  `inbox-*`, plantilla usada en 3 tareas reales, 1 decision nueva.
- Revertir si: vuelve el ruido, `topics/` crece por dia o la plantilla no se usa.
- Rollback: revertir los 3 scripts desde `67dbb55`, `sync --apply`,
  `status sin drift`, `verify.sh` verde.

## Fuente (si aplica)

Paridad conceptual lite con `~/docs/sources/gentle-ai-analysis.md`
(trigger-rules, ODD-only, riesgo en lineas anadidas). Dejado fuera a
proposito: Engram/vector, TUI, multi-runtime, telemetria, registry
persistente, RDD con autoridad.
