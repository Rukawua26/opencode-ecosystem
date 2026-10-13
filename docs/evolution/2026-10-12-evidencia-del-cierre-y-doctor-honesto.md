---
nombre: 2026-10-12-evidencia-del-cierre-y-doctor-honesto
fecha: 2026-10-12
estado: en_observacion
afecta: [skills, scripts, docs, reglas]
fuente: propio
---

# Evidencia del cierre y plugin_doctor honesto

## Por que
El panel sabia que `verify.sh` existia, pero no su resultado: el cierre imprimia
un veredicto por check y lo olvidaba al terminar. Podia marcar `runtime sano`
con el cierre en rojo y no tenia forma de explicar por que fallo. En paralelo,
`~/tools/plugin_doctor.sh` globaaba `"$PLUGINS_DIR"/*.js` y afirmaba
"todos los hooks encontrados en el binario" sin haber visto el plugin real
`uso/tui.tsx` que vive en un subdirectorio.

## Antes
- `./verify.sh`: salida efimera. Ningun registro consultable.
- `plugin_doctor.sh`: 0 plugins vistos, "sano" vacuamente cierto.
- El panel no distinguia runtime de cierre.

## Despues
- `verify.sh` escribe un informe privado, acotado y atomico en
  `~/.local/share/opencode-control/verify-last.json` (0600). Solo al ejecutarse.
  Marcador `state=running` al empezar: si el cierre muere, el panel no presenta
  un informe viejo como si fuera actual.
- Por check: nombre, alcance, resultado, detalle fijo y rc. **Nunca** stdout ni
  stderr de los hijos.
- `control/verify_report.py` lee con allowlist estricta, sanea ANSI y caracteres
  de control, acota longitudes y nunca lanza (ausente, corrupto, otro esquema,
  JSON patologico => estado desconocido).
- `GET /api/verify` read-only. El panel **no ejecuta** el cierre ni la suite:
  no hay endpoint de ejecucion, ni POST, ni SSE, ni polling nuevo.
- Tarjeta "Ultimo cierre" en Resumen: resultado, antiguedad, y por check su
  alcance, resultado y motivo.
- `plugin_doctor.sh`: descubrimiento recursivo de `*.js *.mjs *.cjs *.ts *.tsx`,
  separacion servidor/TUI por lenguaje, y verificacion de la superficie de API
  que consume cada plugin TUI contra el binario.
- ODD abiertos clasificados, sin reejecutar ni cerrar nada.

## Beneficio
Medido: el panel responde "donde esta, que se comprobo, por que" del cierre sin
salir de la interfaz. `overall` solo puede ser `ok` con checks registrados y
`exit_code=0`. `plugin_doctor` paso de 0 plugins vistos a 1, con 6 tokens de API
verificados contra `v2.0.27`.

## No regresion
- `verify.sh` conserva checks, orden, codigos 0/1/2 y formato de stdout. El
  informe nunca condiciona el exit code: con `python3` roto o el directorio en
  solo lectura devuelve el codigo correcto y stderr vacio.
- `health.ok` intacto (servicio + timers + errores).
- Endpoints previos intactos; `/api/verify` es nuevo.
- `plugin_doctor.sh` mantiene salida y codigos; anade deteccion.
- Sin dependencias nuevas, sin SQLite, sin daemon, sin migracion.
- El plugin `uso/tui.tsx` NO se toco ni se sincronizo.

## Verificacion
- `python3 -m unittest discover -s control/tests`: 294 tests OK (1 skipped), ~30 s.
- `./verify.sh`: `[ok] verify verde`.
- `./scripts/qa-gate.sh --strict`: exit 0.
- `python3 validate-skills.py skills`: `[ok] 13 skills valid`.
- `./opencode-ecosystem status`: `[ok] sin drift`.
- `bash ~/tools/plugin_doctor.sh`: exit 0, `plugins detectados: 1 (servidor: 0, TUI: 1)`.
- Focales: `test_verify_report.py` 26 OK, `test_verify_panel.py` 9 OK,
  `test_plugin_doctor.py` 14 OK, `test_verify.py` 14 OK, `test_frontend.py` 25 OK.
- Render real comprobado con datos del endpoint en los tres estados:
  completado verde, en curso, y sin informe.
- Revision independiente read-only: primera `RESULT: failed` con 7 hallazgos
  (1 medio de falso verde); corregidos y confirmados `RESULT: success` con
  reconstruccion del codigo anterior para probar no tautologia.

## Hallazgos corregidos en el camino
1. `exit_code=0` con cero checks se pintaba VERDE. Ahora `overall="ok"` exige
   checks no vacios; sin ellos dice "no hay evidencia para afirmarla".
2. Sin `ended_at` legible, `age=None` se leia como "actual". Ahora se marca
   antiguo, porque no se puede saber cuando se ejecuto.
3. `read_report` podia lanzar `RecursionError` con JSON patologico, contra su
   propio docstring. Ampliado el `except`.
4. El mensaje de "interrumpido" afirmaba un informe anterior que el marcador
   `running` ya habia sobrescrito. Corregido.
5. `verify.sh` no suprimia la salida de su propio escritor de informe: el test
   de fuga de salida de hijos lo detecto y se anadio `>/dev/null 2>&1`.
6. `verify.sh` depender de `date`/`mktemp`/`mkdir` rompia el fixture de tests
   con PATH aislado. Reescrito solo con builtin de bash.
7. Un `.tsx` sin importar la API TUI se clasificaba como plugin de servidor,
   repitiendo el vacio. Clasificacion por lenguaje.
8. `plugin_doctor` imprimia `[ok] N tokens presentes` aun con DRIFT. Ahora
   `[ok]` solo si `drift == 0`.
9. El panel solo mostraba el alcance cuando el motivo faltaba: nunca se veia.
   El alcance se muestra siempre, que es lo que dice que se comprobo.

## Clasificacion y cierre de pendientes (2026-10-12)
- `verifier-sin-duplicar-prompt.md` T5: CERRADO con la delegacion real #17
  (2026-10-11), completada tras el commit de deduplicacion, rc=0, sin errores
  de localizacion del documento ODD.
- `ecosystem-control.md` T47: CERRADO con revision operativa del dia
  (doctor ok=True, 3/3 timers, servicio activo, verify verde, sin drift).
- `odd-primary-workflow.md`: observacion CERRADA con evidencia de cadenas
  worker->verifier completadas entre 2026-09-18 y 2026-10-11.
- `panel-detalle-unificado.md` T3/T4 duplicados: inconsistencia documental en
  un historial ya marcado completada; no se reescribe (regla de historiales).
- Backups: `hygiene.sh prune --apply` ejecutado: 15 podados, quedan 8
  (5 por basename). El trigger deja de disparar.

## Periodo prudencial
- Minimo 7 dias desde 2026-10-12 y varios cierres reales.
- Estable si el informe refleja el cierre real, si nunca aparece verde sin
  evidencia, y si `plugin_doctor` sigue viendo todos los plugins presentes.
- Rollback: `git revert` por commit. `plugin_doctor.sh` se restaura desde su
  historia o copia previa; el informe es regenerable con un `./verify.sh`.

## Fuente
Implementacion propia. Sin codigo copiado de repos externos. Dos jueces
independientes coincidieron en no ejecutar la suite desde el panel y en no
inventar causas ausentes del informe.