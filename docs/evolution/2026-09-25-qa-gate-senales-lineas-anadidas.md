---
nombre: 2026-09-25-qa-gate-senales-lineas-anadidas
fecha: 2026-09-25
estado: en_observacion
afecta: [skills, scripts, docs]
fuente: gentle-ai
---

# QA gate: senales de riesgo solo en lineas anadidas

## Por que

Contra `gentle-ai` `6c7f162f4e59`, el proyecto ya tenia ODD, `assess`, lentes
4R y deteccion de secretos, pero el review de riesgo todavia escaneaba ficheros
completos o solo anti-slop. GentleAI endurecio el analisis de procesos y sinks
peligrosos limitandolo a lineas anadidas. La brecha real no era falta de review,
sino ruido y baja precision: conviene detectar el riesgo introducido por el
candidato sin ejecutar un escanner amplio ni copiar el motor RDD upstream.

## Antes

- `qa-gate.sh` revisaba secrets, logs, TODO/FIXME, catch vacio y ficheros
  sensibles rastreados.
- `risk-lens` dependia de una revision semantica manual sobre el diff.
- Una linea peligrosa nueva podia no distinguirse de una preexistente.
- La semantica de `--strict` cubria secretos/ficheros/catches, pero no habia
  aviso informativo simple y determinista para sinks de alto valor.

## Despues

- `scripts/qa-gate.sh` analiza el staged diff y reporta `path:linea: tipo` solo
  para lineas anadidas en ficheros de produccion.
- El catalogo queda limitado a patrones relevantes del repo: `subprocess` con
  `shell=True`, `os.system`, `eval`, `yaml.load`, TLS desactivada, JWT sin
  verificacion y `chmod 777`.
- Las lineas de contexto, eliminadas, tests y comentarios no se reportan.
- Las senales son informativas: no cambian la semantica de fallo existente de
  `qa-gate.sh`.
- `skills/qa-gate/SKILL.md` y `README.md` documentan la capacidad.
- Como cierre colateral, `plugin_doctor.sh pin` se aplico tras revisar que el
  OpenCode actual `v2.0.16` solo usa hooks conocidos (`config`, `event`).

## Beneficio

- Menos falsos positivos que un barrido de ficheros completos.
- Deteccion determinista de candidatos riesgosos sin anadir dependencia,
  daemon, MCP, SQLite ni proceso permanente.
- Paridad de principio con GentleAI sin adoptar RDD ni el catalogo completo.
- Coste minimo: Python stdlib una vez al ejecutar el gate.

## No regresion

- Se conservan las reglas `warn`/`--strict` anteriores; las nuevas senales solo
  avisan.
- No se imprimen secretos ni contenido de lineas; solo path, linea y etiqueta.
- No se modifico el esquema SQLite, agentes, comandos, permisos ni entrega.
- No se cambio la ruta worker->verifier ni la interpretacion de `assess`.
- Tests del control-plane: previos 154 OK; tras el cambio 159 OK y 1 skip
  esperado del E2E offline opt-in.

## Defecto encontrado al aplicar el cambio

El propio gate bloqueo el commit de este cambio. Reproduccion minima en repo
temporal, tres hallazgos:

1. `catch` vacio: el check escaneaba el diff **completo** (anadidas, eliminadas y
   contexto), no solo las lineas anadidas como ya hacia el escaner de secretos.
   Efecto: borrar un `catch` vacio —el arreglo— bloqueaba igual que anadirlo, y
   una linea de contexto intacta bloqueaba cualquier commit del fichero. Corregido
   elevando `ADDED` y usandolo en los cuatro checks.
2. `catch` vacio en prosa: la documentacion que nombra el patron (con llaves) la
   disparaba como si fuera codigo. No se relajo el regex; se documento el patron
   sin el literal en `skills/qa-gate/SKILL.md`.
3. Fixture de test con forma de clave AWS real: el escaner de secretos, que es otro
   gate y debe poder escanear tambien los tests, bloqueaba siempre. Se uso un valor
   obviamente falso; la asercion de no-impresion sigue cubriendo lo que verifica.

`test_empty_catch_only_blocks_when_it_is_added` fija el contrato: anadir un `catch`
vacio bloquea, borrarlo no.

## Decisiones del humano sobre los limites

1. **Auto-deteccion: se deja como esta.** `scripts/qa-gate.sh` se reporta a si
   mismo: al editar el catalogo, la linea que define `CERT_NONE` se marca como
   `TLS desactivada`. No bloquea (es informativa) y funciona como recordatorio de
   que el fichero contiene los patrones por definicion. No se introduce ninguna
   autoexclusion.
2. **Los checks que bloquean no saltan los tests.** `catch` vacio y secretos
   siguen escaneando `control/tests/`: un secreto en un test es un secreto
   filtrado. El coste aceptable es que un test del gate tenga que ensamblar el
   patron en runtime, y no la excepcion de escanear menos.

Ambas son "no cambiar el contrato", asi que no hay codigo que revertir: si una
revision las revierte, esta seccion es la que dice que fue decision consciente.

## Verificacion

- Dogfood: task #15 (`odd-worker`) -> `done`, receipt `success`; task #16
  (`odd-verifier`) -> primera revision `waiting` por una linea ODD anadida por
  el orquestador, reintento humano y luego `done`/`Sin hallazgos.`;
  `task assess 15` -> `review_state=passed`.
- `python3 -m unittest control.tests.test_qa_gate -v` -> 5/5 OK.
- `python3 -m unittest discover -s control/tests` -> 159/159 OK (1 skipped).
- `python3 -m unittest control.tests.test_playwright_e2e -v` -> 7/7 OK.
- `bash -n scripts/qa-gate.sh` -> exit 0.
- `bash ~/.config/opencode/scripts/qa-gate.sh --strict` -> exit 0 tras sync.
- `python3 validate-skills.py skills` -> 10/10 validas.
- `./opencode-ecosystem sync --apply` y `./opencode-ecosystem status` -> backup
  creado y `[ok] sin drift`.
- `./verify.sh` -> `[ok] verify verde`; `qa-gate.sh --strict` y
  `git diff --check` -> exit 0.
- Primer intento task #14 documentado como incidente: usaba la suite completa
  mientras la propia tarea seguia activa y podia activar el E2E vivo del panel.
  Se repitio sin ampliar el runtime y se corrigio el candidato, no el runner.

## Periodo prudencial

- Duracion: observar varios commits/pre-commits reales o hasta 2026-10-05.
- Estable si no aparecen falsos positivos equivalentes a lineas preexistentes,
  tests/ comentarios reportados o ruido desproporcionado.
- Revertir si el gate bloquea una entrega legitima por una senal informativa o
  filtra contenido sensible. Rollback: restaurar `scripts/qa-gate.sh`,
  `skills/qa-gate/SKILL.md`, `README.md` y eliminar `control/tests/test_qa_gate.py`;
  `sync --apply` y repetir gates.

## Fuente

- `~/docs/sources/gentle-ai-analysis.md`, Revision 2026-09-25, baseline
  `f182ea2018a6..6c7f162f4e59`.
