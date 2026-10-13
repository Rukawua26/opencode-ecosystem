# Evidencia del cierre y plugin_doctor honesto

## Objetivo
Que el panel responda "donde esta, que se comprobo y por que fallo o por que fue
exitoso" sin inventar evidencia: registrar el ultimo `./verify.sh` explicito en
un informe privado y acotado, mostrarlo en Resumen, y corregir `plugin_doctor.sh`
para que deje de afirmar "no hay plugins" cuando existe `uso/tui.tsx`.

## Problema y por que
1. `verify.sh` imprime por check `resultado: detalle; alcance` pero descarta su
   resultado al terminar. El panel observa que el fichero existe y nada mas, asi
   que puede marcar "runtime sano" con el cierre en rojo, sin poder explicar por
   que fallo.
2. `~/tools/plugin_doctor.sh` inspecciona solo `$PLUGINS_DIR/*.js`. Existe
   `~/.config/opencode/plugins/uso/tui.tsx` (455 lineas) que el doctor no puede
   ver: reporta "hooks en uso:" vacio y "todos los hooks encontrados en el
   binario" de forma vacuamente cierta. Una afirmacion de salud sin evidencia.
3. `plugins/uso/tui.tsx` es un plugin TUI: usa `context.data.on(...)`, no hooks
   de servidor. Un grep de hooks de servidor no puede verificarlo.

## Alcance
### Incremento 1 - verdad de origen
- `~/tools/plugin_doctor.sh`: descubrimiento recursivo de plugins (`*.js`,
  `*.mjs`, `*.cjs`, `*.ts`, `*.tsx`), verificacion de la superficie usada por
  plugins TUI contra el binario, y estado explicito "no verificable" cuando no
  haya superficie comprobable. Clasificar los ODD abiertos.
### Incremento 2 - evidencia del cierre
- `verify.sh`: escribir informe privado, atomico y acotado al ejecutar.
- `control/verify_report.py`: lectura saneada por allowlist + antiguedad.
- `control/server.py`: `GET /api/verify` read-only.
- Panel: tarjeta "Ultimo cierre" en Resumen.
### Incremento 3 - experiencia de diagnostico
- Panel:_runtime / ultimo cierre / trabajo del runner separados; detalle por
  check con "que comprobo / resultado / por que / que revisar".

### Excluye
SQLite, migraciones, dependencias nuevas, daemons, polling nuevo, ejecutar
`verify.sh` desde el navegador, observar sesiones interactivas, tocar el plugin
`uso/tui.tsx`, podar backups, reejecutar ODD ya completados, reescribir
documentos historicos de `odd/tasks/` o `docs/evolution/`.

## Restricciones
- Python stdlib + Bash. Sin CDN ni frameworks en el panel.
- i5-1235U/8GB: el panel NUNCA ejecuta la suite; solo lee un fichero pequeno.
- Nunca persistir stdout/stderr de hijos, prompts, rutas sensibles ni secretos.
- Escritura atomica y permisos privados (0600) del informe.
- No cambiar `Health.ok` ni su semantica. No tocar memoria viva, receipts,
  backups ni logs.
- No commit, branch, push ni PR sin peticion explicita.
- Respetar los cambios sin commit de `panel-verdad-declarado` ya en el arbol.

## No romper
- Contratos existentes: `/api/snapshot`, `/api/graph`, `/api/events`,
  `/api/tasks`, `/api/tasks/<id>/trace`, `/api/reconcile`, `/api/execution-metrics`,
  `/api/health`. Anadir uno nuevo no los altera.
- `verify.sh` mantiene stdout, codigos de salida (0/1/2) y semantica de cada
  check. El informe es un efecto adicional, nunca un requisito para el verde.
- `plugin_doctor.sh` mantiene su salida y codigos; anade deteccion, no la cambia.
- La suite completa sigue verde; `status` sin drift; `qa-gate --strict` exit 0.
- `panel-verdad-declarado` (sin commit): flujo `cierre`, `verify.sh` como
  componente, etiqueta `runtime sano`. Intacta.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks funcionales obligatorios. Escribir regresion antes del fix cuando sea
  viable: ausente/viejo/incompleto para el informe; `.tsx` no visto para el doctor.

## Tareas
- [x] T1: `plugin_doctor.sh` descubre plugins recursivamente y verifica la
  superficie TUI; clasificar ODD abiertos en el documento.
- [x] T2: `verify.sh` escribe informe atomico privado; `control/verify_report.py`
  con allowlist y antiguedad; tests.
- [x] T3: `GET /api/verify` read-only + tarjeta "Ultimo cierre" en Resumen.
- [x] T4: detalle por check (que comprobo / resultado / por que / que revisar).
- [x] T5: cierre con evidencia, revision independiente y nota de evolucion.

## Criterios de aceptacion
- [x] `plugin_doctor.sh` ve `uso/tui.tsx`; no dice "hooks en uso: vacio" como si
      no hubiera plugins; dice "no verificable" si no puede comprobarlo.
- [x] Un informe ausente se muestra como "sin ejecucion registrada", nunca verde.
- [x] Un informe antiguo se marca como antiguo y no como estado actual.
- [x] Una ejecucion interrumpida no se presenta como completada.
- [x] Cada check del informe muestra resultado y alcance; el motivo solo si el
      informe lo trae; si no, dice que no hay causa disponible.
- [x] El informe no contiene stdout de hijos, prompts ni secretos.
- [x] El panel no ejecuta `verify.sh` ni la suite en ninguna interaccion.
- [x] `verify.sh` conserva stdout y codigos de salida actuales.
- [x] Suite completa verde, skills validas, status sin drift, verify verde,
      qa-gate strict exit 0, node --check del JS inline.
- [x] `overall="ok"` exige checks registrados y `exit_code=0`. Sin evidencia
      no hay verde (regresion cubierta).

## Decisiones aceptadas
- El informe es un fichero JSON nuevo en `~/.local/share/opencode-control/`,
  separado de `control.db`, `snapshot.json` y de los receipts. Autorizado
  explicitamente por el humano el 2026-10-12.
- No se guarda hash del codigo ni "candidato": no puede probarse con lo
  observado. En su lugar se guardan `head` y si el arbol de trabajo estaba
  sucio, y la edad del informe manda sobre la interpretacion.
- No hay accion en el panel para ejecutar el cierre: se ejecuta desde la
  terminal. Evita convertir la navegacion en ejecucion de procesos.
- Causa = solo la cadena `detail` fija que `verify.sh` ya produce. Nunca texto de
  error del hijo.

## Reutilizacion investigada
- Canonicos: `verify.sh:30-54` (`run_check` y su `printf` fijo),
  `control/collect.py:24-25` (`STATE_DIR`, `SNAPSHOT_PATH`),
  `control/collect.py:444-452` (`write_snapshot_atomic`) como patron de
  escritura atomica, `control/server.py` (`_json`, allowlist de GET),
  `control/trace.py` (traduccion de motivo a lenguaje humano) y
  `index.html:1028-1073` (`explainTrace`) como patron de "por que".
- `write_snapshot_atomic` sirve de plantilla pero escribe JSON del Snapshot;
  el informe necesita su propio escritor porque lo produce un script Bash.
- `db.record_event` NO se usa: es receipts/eventos del plano de control, y el
  informe del cierre es de otro proceso y otro contrato.

## Evidencia
- Baseline: suite 245 tests OK (1 skip). `./verify.sh` verde tras re-pinear
  OpenCode a `v2.0.27`. `status` sin drift. Snapshot: skills 13, scripts 5,
  flujos 4, componentes 25.
- `plugins/uso/tui.tsx`: 455 lineas, importa `@opencode/plugin/tui`, usa
  `context.data.on("session.execution.succeeded"|"session.execution.failed")`,
  `context.client.session.stats`, slots `prompt.footer.status` y
  `home.footer.status`.
- Superficie de `uso/tui.tsx` presente en el binario `v2.0.27` (grep -a):
  PRESENTES los dos eventos, `session.stats`, `prompt.footer.status`,
  `@opencode/plugin/tui`. `tool.execute.before` AUSENTE (no lo usa el plugin).
- `plugin_doctor.sh:60` y `:97` globean `"$PLUGINS_DIR"/*.js` con
  `nullglob`: un `.tsx` en subdirectorio nunca se abre.
- T1: passed. Ver seccion "Evidencia T1" y "Clasificacion de ODD abiertos".
- T2-T5: passed. Detalle:
  - `verify.sh` reescrito: informe privado 0600, atomico, por check. Sin
    `date`/`mktemp`/`mkdir` (solo builtin de bash) para ser hermetico en el
    PATH aislado del fixture.
  - `control/verify_report.py`: allowlist, saneado ANSI + control, truncado,
    nunca lanza. Estados none/corrupt/unknown_schema/completed/running/
    interrupted; fresh 6 h; running >15 min = interrupted.
  - `GET /api/verify` read-only en `server.py`. El panel no ejecuta nada.
  - Tarjeta "Ultimo cierre" en Resumen + glosario en Ayuda + `control/README.md`.
  - Tests nuevos: `test_verify_report.py` (26), `test_verify_panel.py` (9, node
    sin navegador), `test_plugin_doctor.py` (14). `test_verify.py` ajustado
    para distinguir checks de las 2 llamadas auxiliares del informe, fijando su
    numero para que no crezcan en silencio.
  - Suite completa: `Ran 294 tests ... OK (skipped=1)`, ~30 s.
  - `./verify.sh` verde; `qa-gate --strict` exit 0; 13 skills validas; sin drift.
  - Render real comprobado en 3 estados con datos del endpoint.
  - Revision independiente: 1a `RESULT: failed` con 7 hallazgos (1 medio de
    falso verde). Corregidos y 2a verificacion `RESULT: success`, con
    reconstruccion del codigo anterior para probar no tautologia.
  - Nota de evolucion: `docs/evolution/2026-10-12-evidencia-del-cierre-y-doctor-honesto.md`.
  - Nota: Playwright E2E sigue being opt-in (Chromium no instalado). El render
    se verifico con un arnes de node que ejecuta la funcion real del panel.
- Sin stage, commit, push ni PR.

## Progreso
- Estado: done (en observacion 7 dias desde 2026-10-12).
- Cierres con evidencia (2026-10-12):
  - `verifier-sin-duplicar-prompt.md`: observado el verificador #17 tras el
    commit de deduplicacion -> done rc=0, localizo la tarea via documento ODD.
  - `ecosystem-control.md` T47: periodo de observacion cerrado con revision
    operativa del dia (doctor ok=True, 3/3 timers, suite 294, verify verde,
    sin drift). Task #11 dead es terminal y no bloquea.
  - `odd-primary-workflow.md`: observacion larga cerrada con evidencia de
    cadenas worker->verifier completadas del 2026-09-18 al 2026-10-11.
  - `panel-detalle-unificado.md` T3/T4 duplicados: inconsistencia documental
    en documento historico; el propio documento tiene estado completada y
    evidencia. Comportamiento y tests ya pasan. Se deja como historial; la
    ficha de evolucion lo registra.
  - Backups: `hygiene.sh prune --apply` ejecutado (15 podados, quedan 8,
    trigger ya no dispara).
- T1-T5: passed, con revision independiente en contexto fresco.
- Pendiente resuelto por el humano (2026-10-12): NO reestructurar los ODD
  historicos duplicados (`panel-detalle-unificado` T3/T4). Quedan como
  historial de solo lectura; no son error a corregir.
- Pendiente resuelto por el humano (2026-10-12): NO unir la verdad del cierre
  a `health.ok`. La salud de la API queda solo como runtime (servicio+timers);
  el cierre vive aparte en `overall` de `/api/verify`. No hay endpoint nuevo.
- Bloqueos: ninguno.

## Evidencia T1 - plugin_doctor honesto
- Causa raiz: globa `"$PLUGINS_DIR"/*.js` con `nullglob`. Un `.tsx` en
  subdirectorio nunca se abria, asi que "hooks en uso:" salia vacio y
  "todos los hooks encontrados en el binario" era vacuamente cierto.
- Descubrimiento recursivo de `*.js *.mjs *.cjs *.ts *.tsx`.
- Separacion servidor/TUI por lenguaje (`*.ts|*.tsx` = TUI), como hace el
  runtime; un `.js` que importe la API de TUI se reetiqueta.
- Superficie TUI verificada contra el binario: eventos `data.on/listen`,
  slots conocidos, `client.*` y el import. Token ausente => DRIFT + exit 1.
- Plugin sin superficie reconocible => aviso de que no se puede afirmar que
  este sano. Nunca "sano".
- Si hay plugins pero ninguna superficie verificable => aviso explicito de
  que el estado del binario NO queda comprobado.
- Defecto propio corregido durante T1: se imprimia `[ok] N tokens presentes`
  aunque hubiera DRIFT. Ahora `[ok]` solo si `drift == 0`.
- Real: `plugins detectados: 1 (servidor: 0, TUI: 1)`, 6 tokens presentes,
  exit 0. `bash -n` ok. Fichero del plugin intacto: no se toco.
- `python3 -m unittest discover -s control/tests -p "test_plugin_doctor.py"`
  -> `Ran 14 tests ... OK`, 0.173 s.

## Clasificacion de ODD abiertos (T1)
No se reejecuta ni se cierra nada: solo se clasifica con evidencia.

| Documento | Marca abierta | Clasificacion | Motivo |
|---|---|---|---|
| `verifier-sin-duplicar-prompt.md` T5 | `[ ] Observacion 7 dias` | observacion en curso | Requiere 1-2 delegaciones reales por la cola. Sin evidencia nueva. |
| `ecosystem-control.md` T47 | `[ ] Cerrar periodo observacion` | obsoleto por fecha | Pedia ventana "hasta ~2026-09-25"; hoy es 2026-10-12. Su evidencia es de septiembre. |
| `panel-detalle-unificado.md` T3/T4 | `[ ]` duplicados tras `[x]` | inconsistencia documental | El documento dice `Estado: completada` y sus lineas 51-52 ya registran T3/T4 con evidencia. Las 53-54 son duplicado. Historico: no reescribir. |
| `odd-primary-workflow.md` | `Estado: en_observacion` | observacion larga | Pedia observar 2 semanas tras reiniciar OpenCode. Sin evidencia de cierre. |
| `panel-tema-oscuro.md` | deuda declarada | fuera de alcance | Sin listener `change` en `matchMedia`. Deuda aceptada. |
| `panel-ayuda-estatica.md` | tablist sin roving tabindex | fuera de alcance | Deuda declarada preexistente. |
| Backups | 23 con 15 podables | ~~decision humana~~ **resuelto 2026-10-12** | El humano autorizo el cierre: `hygiene.sh prune --apply` recupero la regla conservando los 5 ultimos por basename (quedaron 8, trigger deja de disparar). |