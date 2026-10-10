# Cierre fiable y explicito

## Objetivo
Reunir el cierre local del ecosistema en `./verify.sh`, con resultados seguros y
alcances explicitos, reutilizando los controles existentes.

## Problema y por que
- `qa-gate.sh` imprime codigo de logs/TODO y puede filtrar un secreto en esa linea.
- Los errores de Git se ocultan con `|| true`; no hay distincion entre fallo y
  ausencia de cambios staged.
- `verify.sh` no incluye unittest ni QA estricto: el cierre depende de recordar
  varios comandos y no explicita que tests y QA leen alcances distintos.
- El usuario aprobo implementar el primer incremento del plan el 2026-10-02.

## Alcance
Incluye gate seguro y fail-closed, skill existente, cierre unico, pruebas y docs.
Excluye panel, huellas/candidatos, estados nuevos, JSON, routing, consumo, CI,
instalaciones, plugins, SAST/SCA nuevos y pruebas pesadas.

## Restricciones
Python stdlib y Bash existentes; ejecucion secuencial, sin procesos permanentes.
No modificar SQLite, memoria viva, receipts, logs, backups ni cambios ajenos.
Sin branch, commit, push, PR o deploy. No poner codigo/secretos en resultados.
La fuente es el repo; sincronizar solo el gate y la skill modificados. El sync
general actual toca memoria/backups y queda fuera del alcance de esta feature.

## No romper
- Warn conserva exit 0 para hallazgos; strict conserva exit 1 para los bloqueantes.
- Fallos operativos y argumentos invalidos deben ser no-cero en ambos modos.
- Mantener las reglas existentes: secretos, rutas sensibles, catch vacio,
  avisos de logs/TODO y riesgos solo en lineas anadidas de produccion.
- Conservar los checks actuales de verify y su exit no-cero ante fallo.
- Sin staged: no declarar auditoria del codigo; las rutas rastreadas siguen
  comprobadas. No auditar implicitamente el codigo sin stage.
- Tests sobre working tree y QA sobre staged son alcances distintos, no un
  candidato congelado ni una certificacion SAST/SCA.
- Los archivos originales del alcance estan versionados y limpios en baseline
  `1baf106108c2da0f3fb25c1f2053ce0e237dbda9`; conservarlo como base reversible.
- Dejar intactos los cambios preexistentes en memory/, opencode-ecosystem,
  scripts/ram-guard-lite.sh y los archivos no rastreados ajenos.

## TDD
- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks funcionales obligatorios; agregar regresiones y reproducir los bugs
  antes del fix cuando sea viable, sin afirmar que hay Strict TDD configurado.

## Tareas
- [x] T1: endurecer scripts/qa-gate.sh y ampliar control/tests/test_qa_gate.py.
  Verificar errores Git, fugas, scope vacio, rutas especiales y reglas previas.
  Reabierta: verificador independiente failed; metadata new/deleted truncada
  se acepta como archivo vacio y ls-files desde subdirectorio omite rutas raiz.
  Segunda reapertura: hallazgo independiente compartido con T2; GIT_* heredado
  permite auditar otro repo/indice limpio en lugar del repo canonico del cwd.
  Correccion local passed; tarea abierta hasta nueva verificacion independiente.
  Tercera reapertura: autochequeo detecta SHELLOPTS=xtrace filtrando argumentos
  del gate standalone; se autoriza solo startup set +evx y regresion acotada.
  Correccion startup passed por worker; verificacion independiente del delta
  passed (1 test, 16 casos) tras el autochequeo.
- [x] T2: ampliar verify.sh como cierre unico y crear test_verify.py con fixtures
  aislados, sin llamadas a proveedores ni recursion sobre la suite real.
  Reportar checks/alcances y continuar recogiendo fallos; nunca verde incompleto.
  Reabierta por verificador fresh failed: GIT_* redirige preflight, SHELLOPTS
  filtra valores/interrumpe resumen y TERM permite sobrevivir a descendientes.
  Correccion local passed; verificacion independiente del delta passed.
- [x] T3: actualizar skill qa-gate, README y docs/evolution con limites,
  contratos, base reversible y periodo prudencial.
  Documentacion y validacion local passed; revision independiente passed.
- [x] T4: sincronizacion selectiva y verificacion final, revision independiente
  de cada tarea, registro de evidencia y estado honesto del cierre.

## Criterios de aceptacion
- [x] Sin fragmentos fuente ni secretos en avisos, errores o resumen del gate.
- [x] Error Git y fallos de herramientas no se convierten en aprobacion.
- [x] No staged se explicita, sin omitir chequeo de rutas sensibles rastreadas.
- [x] Reglas y semantica warn/strict preservadas con regresiones verificadas.
- [x] verify ejecuta tests, skills fuente/runtime, config, drift, doctores y QA.
- [x] Cada check muestra resultado y alcance; salida de herramientas no se vuelca.
- [x] Check obligatorio fallido/incompleto/no disponible impide verify verde.
- [x] Sin nuevas dependencias, daemons, esquema, memoria o cambios ajenos.
- [x] unittest, validate-skills, status sin drift, verify y QA strict pasan.

## Decisiones aceptadas
- Incremento pequeno sobre componentes existentes, no nuevo motor QA.
- La ausencia de staged es no aplicable para ese analisis, no un fallo por si
  misma ni una aprobacion del codigo unstaged. El cierre informa este limite.
- No obtener ni fabricar metricas de tokens, hashes o autoria de cambios.
- Delegacion con herramientas del harness: general actuando como odd-worker
  para una tarea atomica y otro contexto como odd-verifier read-only; profundidad 1.

## Reutilizacion investigada
- Canonicos: scripts/qa-gate.sh (Python embebido y catalogo), verify.sh,
  control/tests/test_qa_gate.py (repos temporales), validate-skills.py y doctores.
- No se encontro sanitizador reutilizable del gate en control/; no importar
  el plano de control desde el runtime ni crear dependencia entre ambos.
- Mantener Python dentro del .sh si hace falta: el sincronizador solo gestiona
  scripts/*.sh; no ampliar su contrato para un modulo standalone.
- test_verify.py se justifica como fixture del cierre, que hoy no tiene tests;
  reutilizar unittest/tempfile/subprocess, no otro framework.
- T1: busqueda dirigida de sanitize/redact/escape/TimeoutExpired en scripts/ y
  control/: no hay transporte/sanitizador canonico reutilizable para este gate.
  Se conservaron el catalogo y Python embebido de qa-gate.sh y se amplio el
  fixture unittest con repos temporales; el staging ocurre solo en esos repos.
  Helpers locales de transporte, ruta y validacion de seccion evitan duplicar
  comprobaciones; no se importo control/ ni se creo modulo runtime nuevo.
- Reapertura T1: busqueda dirigida de hashlib/empty blob/object format/sha256
  en control/ sin equivalentes. Se reutilizaron complete_section, git_output y
  el mismo fixture temporal. Solo hashlib stdlib, --full-index y pathspec raiz:
  sin nuevos helpers, parser generico ni consultas Git adicionales por archivo.
- Segunda reapertura T1: busqueda dirigida de GIT_INDEX_FILE/GIT_CONFIG_COUNT/
  filtrado GIT_* en control/ sin equivalente. Se reutilizan git_output y el
  fixture temporal con entorno solo para el gate; filtrado stdlib inline, sin
  helper ni consulta Git para sanitizar. PATH y HOME generales conservados.
- Tercera reapertura T1: reutilizados el startup canonico set +evx de verify.sh
  y su matriz SHELLOPTS, mas run_gate/credenciales sinteticas existentes.
  Unica linea runtime nueva antes de expansiones; sin helpers ni plataforma.
- T2: busqueda dirigida de timeout/DEVNULL/command -v/run_check/countTestCases
  en scripts/ y control/tests/: no existe wrapper de cierre equivalente.
  Se reutilizaron los comandos de verify, unittest discovery stdlib y el patron
  QA de tempfile/subprocess/repos Git aislados. run_check concentra transporte
  DEVNULL, timeout GNU instalado y resumen fijo; no runner/modulo/formato nuevo.
  El fixture HOME+PATH es local a test_verify porque run_gate no ejecuta verify
  ni sustituye sus doctores; no importar tests ni runtime del plano de control.
  Reapertura: reutilizado el contrato canonico de T1 (sin GIT_* heredados),
  con expansion de nombres y unset builtins Bash, sin imprimir valores.
  Se mantiene run_check y GNU timeout; KILL sustituye TERM+gracia, sin runner
  ni gestion de grupos nueva en runtime. Fixture existente ampliado con socket
  stdlib de readiness y GNU timeout real, solo para probar el grupo temporal.

- T3: busqueda dirigida en docs/evolution de qa-gate/cierre/rollback; reutilizados
  _TEMPLATE.md y 2026-09-22-qa-gate-secretos.md como formato e historial, no su
  rollback global. verify.sh y scripts/qa-gate.sh actuales son los contratos
  canonicos; skill y secciones existentes del README se actualizan sin nuevo
  formato/helper ni analisis externo. Nota nueva exigida por las reglas del repo.
  Mapa de contexto local ausente; query_context list encontro el proyecto, pero
  summary opencode-ecosystem no esta disponible. Exploracion limitada al alcance.

## Evidencia
- Baseline unittest: passed; 189 tests, 1 skipped, 20.033 s.
- Baseline skills: passed; 12 skills valid.
- Baseline runtime: passed; ./opencode-ecosystem status -> [ok] sin drift.
- T1: correccion startup SHELLOPTS passed por worker,
  nueva verificacion independiente pending, tarea abierta.
  Informe del coordinador: verificacion independiente previa passed,
  34 tests y 158 probes; conservar como historial anterior a este autochequeo.
  Hallazgo independiente nuevo: entorno GIT_* puede redirigir repo/indice.
  Verificacion independiente inicial: failed (dos hallazgos reproducibles).
  Evidencia historica anterior, invalidada como cierre por esos hallazgos:
  - Regresion antes del fix: `python3 -m unittest control.tests.test_qa_gate`:
    19 tests, 39 fallos de asercion/subtest, 7.437 s, exit 1.
  - Final: mismo comando, 28 tests, 0 fallos, 14.074 s, exit 0.
  - `bash -n scripts/qa-gate.sh`: passed, exit 0.
  - `git diff --check -- scripts/qa-gate.sh control/tests/test_qa_gate.py`:
    passed, exit 0.
  - `scripts/qa-gate.sh --strict` en repo real: passed, exit 0;
    staged no aplicable (sin cambios staged), rutas rastreadas comprobadas.
    No certifica el codigo unstaged. No stage/commit/sync del repo real.
  - Contrato verificado: hallazgos warn=0; bloqueantes strict=1;
    Git fallido/faltante, Python faltante, argumentos invalidos y errores
    externos/timeout=2, sin fuente, stderr/stdout Git ni excepciones crudas.
  - Politica conservadora: cualquier diff binario staged, formato no soportado,
    hunk/cabecera incompletos o transporte incompleto devuelve 2 en ambos modos:
    el catalogo textual no puede auditar esos bytes. Archivos vacios, cambios
    solo de permisos y borrados textuales completos siguen siendo aplicables.
  - Limites: Git tiene timeout de 15 s por consulta; transporte temporal sin
    logs, lectura de entrada maximo de 16 MiB por salida. No es un hard cap de
    disco ni de RAM: el temporal puede crecer durante la consulta y parsear
    requiere memoria adicional. Superar el limite de lectura no aprueba.
    Hasta 50 hallazgos impresos, contando/evaluando todos antes de publicar;
    el bloqueante tardio tambien conserva strict=1.
  - Regresiones cubren catalogo, credenciales sinteticas construidas en runtime,
    doble/triple +, solo anadidos, alcance vacio, rutas rastreadas sensibles,
    quoting/UTF-8/controles y redaccion de credenciales en nombres de archivo.
    Timeouts/errores se inyectan sin sleeps; fixture Git aislado, sin proveedores.
  - Suite completa/skills/runtime/verify: pending para T4, no ejecutados por T1.
  - Reapertura: regresiones antes del fix con
    `python3 -m unittest control.tests.test_qa_gate`: failed, 31 tests,
    20 fallos de subtests (16 truncamiento, 4 rutas), 20.301 s, exit 1.
  - Correccion actual: mismo comando passed, 31 tests, 0 fallos/skip,
    21.066 s, exit 0. Un intento de fix por hallazgo; no verificacion independiente.
  - `bash -n scripts/qa-gate.sh` y
    `git diff --check -- scripts/qa-gate.sh control/tests/test_qa_gate.py`:
    passed, ambos exit 0 despues de la correccion.
  - `scripts/qa-gate.sh --strict`: passed, exit 0; staged no aplicable y rutas
    rastreadas comprobadas. No se hizo staging del repo real ni sync.
  - New/deleted sin hunk requiere hashes completos y par null/blob vacio,
    calculado con hashlib a partir de la cabecera Git blob 0; SHA-1 y SHA-256.
    Tests incluyen truncamiento al EOF y antes de otra seccion, warn y strict;
    repos Git reales de ambos formatos conservan archivos vacios y hunks.
  - ls-files usa --full-name -z -- :/: pruebas desde nested/deep, con/sin staged,
    warn/strict, .env raiz, ruta con credencial sintetica/control y archivo
    sensible fuera del subdirectorio. Rutas raiz de diff y safe_path preservados.
  - Timeout 15 s y cap de presentacion 50 sin cambios. Politica binaria conserva
    exit 2, no afirma auditoria; documentacion publica explicita pendiente en T3.
  - Segunda reapertura: tres regresiones nuevas ejecutadas antes del fix con
    `python3 -m unittest control.tests.test_qa_gate.QaGateTests.test_git_environment_cannot_redirect_repo_or_index control.tests.test_qa_gate.QaGateTests.test_git_environment_configuration_cannot_change_queries control.tests.test_qa_gate.QaGateTests.test_git_environment_cannot_invent_repository_for_nonrepo_cwd`:
    failed, 3 tests, 19 fallos (12 repo/indice, 6 config, 1 fuera de repo),
    3.144 s, exit 1. Observado falso strict=0 con .env rastreado real.
  - Resultado actual: `python3 -m unittest control.tests.test_qa_gate` passed,
    34 tests, 0 fallos/skip, 24.062 s, exit 0. Un intento de fix del alcance.
  - `bash -n scripts/qa-gate.sh` y
    `git diff --check -- scripts/qa-gate.sh control/tests/test_qa_gate.py`:
    passed, ambos exit 0. Sin cambios en verify, test_verify ni skill.
  - Alcance canonico: Git descubre el repo desde cwd (tambien subdirectorios)
    y consulta su indice normal. Cada subprocess Git recibe el entorno sin
    TODAS las variables GIT_* heredadas; no se respeta GIT_INDEX_FILE alterno
    ni redireccion/config de GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_CONFIG_*.
    Se mantienen PATH, HOME y los flags seguros existentes; sin nuevas opciones
    de scope, consultas auxiliares ni valores/rutas raw en errores.
  - Pruebas reales con dos repos temporales: main con .env rastreado y alternate
    limpio, indices compatibles SHA-1; raiz y nested/deep, warn y strict.
    Config COUNT/KEY/VALUE/PARAMETERS y COUNT invalido no alteran las consultas.
    Cwd sin repo sigue devolviendo 2 aunque GIT_DIR apunte a un repo valido.
    Los tests existentes de Git stub prueban que PATH sigue disponible.
  - Esta evidencia es local del worker, no verificacion independiente ni cierre
    global; suite completa/runtime/sync siguen fuera de esta correccion de T1.
  - Tercera reapertura: `python3 -m unittest control.tests.test_qa_gate.QaGateTests.test_inherited_shell_options_do_not_leak_or_change_exit_codes` antes del fix:
    failed, 1 test, 11 fallos de subtests, 2.488 s, exit 1. Reproduce fuga de
    argumentos con xtrace y fuente embebido con verbose; aserciones booleanas
    de mensajes fijos no imprimen stdout capturado ni el token sintetico.
  - Tras unica linea startup set +evx:
    `python3 -m unittest control.tests.test_qa_gate`: passed, 35 tests,
    0 fallos/skip, 26.825 s, exit 0. Un intento de fix.
    `bash -n scripts/qa-gate.sh` y
    `git diff --check -- scripts/qa-gate.sh control/tests/test_qa_gate.py`:
    passed, ambos exit 0.
  - Matriz nueva: xtrace, verbose, errexit y las tres combinadas; argumento
    invalido sintetico con/sin --strict, warn valido y strict valido con .env
    rastreado. Conserva rc2/0/1 y etiquetas seguras, sin fuente ni token.
    Solo lineas iniciales estaticas pueden aparecer antes de desactivar trace.
  - Historial independiente previo conserva passed (34 tests, 158 probes,
    informado por coordinador); no cubre este cambio. Nueva revision pending.
- T2: correccion de reapertura passed (worker); ajuste reliability en validacion.
  Verificacion independiente anterior: passed, 14 tests y probes, informado
  por coordinador. No cubre el nuevo ajuste de budget del fixture; nueva
  revision independiente pending, check focalizado local passed.
  Verificacion fresh anterior: failed por cuatro reproducciones confirmadas.
  Evidencia historica inicial, no valida como cierre tras esos hallazgos:
  - `python3 -m unittest control.tests.test_verify`: passed, 11 tests,
    0 fallos/skip, 11.982 s, exit 0. TDD off; pruebas funcionales focalizadas.
  - `bash -n verify.sh` y
    `git diff --check -- verify.sh control/tests/test_verify.py`: passed, exit 0.
  - Checks secuenciales conservados mas discovery no vacio, comando exacto
    unittest, consulta staged Git segura y qa-gate --strict siempre ejecutado.
    Todos en cwd ECO aunque verify se invoque desde otro directorio.
  - Resumen fijo por check y alcance, sin stdout/stderr de herramientas en
    terminal/disco: DEVNULL. Fallos continuan; rc2 gate incompleto, rc124/137
    incompleto, rc126/127 no disponible, hygiene rc1 aviso y rc2+ error.
  - Tests prueban cada fallo obligatorio y continuacion, argumentos invalidos,
    HOME/repo/comandos/recursos ausentes, ambos streams no confiables ocultos,
    staged vacio/aplicable/desconocido y timeouts inyectados sin sleeps.
    El fixture ejecuta solo una suite minima temporal, nunca la suite real.
  - Discovery cuenta tests sin parsear texto: vacio, directorio ausente e
    import fallido no producen verde. Se simula runner rc0 sin tests para cubrir
    ese contrato; el Python actual devuelve rc5 en discovery vacio real.
  - Gate real en repo Git temporal: sensible rastreado sin staged devuelve 1;
    binario staged devuelve 2; ambos impiden verify verde. QA sigue limitado a
    staged+rutas rastreadas y el resumen no certifica codigo unstaged.
  - Timeout GNU inicial: 15 s consulta Git, 30 s hygiene/skills, 60 s otros
    checks/QA, 180 s unittest, TERM+gracia 5 s; sustituido en la reapertura.
  - Suite completa, verify real, skills/runtime/doctores reales y QA del repo
    real: pending para T4; no ejecutados por T2. Sin stage/commit/sync.
  - Regresiones de reapertura antes del fix:
    `python3 -m unittest control.tests.test_verify.VerifyTests.test_inherited_shell_options_do_not_leak_or_stop_remaining_checks control.tests.test_verify.VerifyTests.test_git_environment_cannot_redirect_canonical_staged_query control.tests.test_verify.VerifyTests.test_real_timeout_kills_term_ignoring_descendant`:
    failed, 3 tests, 7 fallos de subtests y 1 error, 7.350 s, exit 1.
    Scope alterno/vacio/config invalida altera preflight; HOME marker aparece
    con xtrace/verbose; errexit omite cierre; hijo que ignora TERM conserva socket.
  - Resultado corregido: `python3 -m unittest control.tests.test_verify`:
    passed, 14 tests, 0 fallos/skip, 15.804 s, exit 0.
    `bash -n verify.sh` y
    `git diff --check -- verify.sh control/tests/test_verify.py`: passed, exit 0.
    Primer intento de fix por hallazgo; no se excedio el presupuesto de 3.
  - Startup `set +evx` fijo antes de expandir datos; opciones SHELLOPTS quedan
    actualizadas para hijos. Trace/verbose solo pueden mostrar lineas iniciales
    estaticas, nunca HOME/argumentos/comandos con valores. BASH_ENV arbitrario
    previo a la primera linea queda fuera de alcance: no se promete sandbox.
  - Todo GIT_* heredado se elimina mediante nombres, sin volcar valores; Git
    consulta el repo e indice canonicos de ECO, alineado con QA. Pruebas con
    repos reales cubren GIT_DIR/WORK_TREE, INDEX_FILE y CONFIG_COUNT invalido.
  - Timeout usa KILL al deadline sobre su grupo normal (rc137 incompleto);
    mismos limites amplios 15/30/60/180 s, sin gracia ni cleanup normal.
    Redireccion del bloque tambien oculta diagnosticos de senal de Bash.
    No se cubren procesos detached deliberados fuera del grupo de timeout.
  - Test GNU real inicialmente reducia solo higiene a 0.2 s: socket comunica grupo
    del hijo que ignora TERM; EOF prueba su terminacion sin sleeps/polling ni
    aserciones de duracion. El fixture limpia su grupo en finally incluso si
    falla el runner; no crea procesos permanentes ni llama doctores reales.
  - Autochequeo reliability: el deadline arranca antes del handshake; 0.2 s puede
    matar el fixture durante startup en laptop cargado aunque timeout funcione.
    Se amplia solo el budget del fixture a 5 s; se conservan handshake/EOF y
    cleanup finally, sin sleeps ni aserciones de tiempo. No se cambia produccion
    ni se introduce orquestador/timer; el limite unittest 180 s no cambia.
    `python3 -m unittest control.tests.test_verify.VerifyTests.test_real_timeout_kills_term_ignoring_descendant`:
    passed, 1 test, 0 fallos/skip, 5.346 s, exit 0; una sola ejecucion.
    Nueva revision independiente del ajuste y suite completa: pending.
  - Suite completa, verify real, QA del repo real, sync y revision independiente:
    pending, no ejecutados por esta correccion T2. Ningun cambio fuera de T2.
- T3: documentacion implementada por worker; validacion de skills/diff passed.
  - Skill breve sin acentos, README y nueva nota de evolucion describen contratos,
    alcances, limites conservadores, baseline y rollback selectivo.
  - git diff previo de README.md y skills/qa-gate/SKILL.md: vacio; git ls-tree
    confirmo los cinco originales en baseline 1baf106108c2da0f3fb25c1f2053ce0e237dbda9.
    test_verify.py, nota nueva y ODD no estan en esa baseline.
  - `python3 validate-skills.py skills`: passed, exit 0, `[ok] 12 skills valid`.
  - `git diff --check -- README.md skills/qa-gate/SKILL.md odd/tasks/cierre-fiable.md docs/evolution/2026-10-03-cierre-fiable.md`:
    passed, exit 0, sin avisos (no cubre los nuevos no rastreados).
  - Nota y ODD nuevos: `git diff --no-index --check -- /dev/null <ruta>` sin
    avisos; exit 1 por diferencias no-index, no afirmar exit 0.
  - Python stdlib directo sobre los cuatro documentos (lineas sin whitespace
    final) y skill ASCII: passed, exit 0, `[ok] whitespace: 4 documentos;
    skill ASCII sin acentos`.
  - Suite completa/verify/QA/runtime/sync y revision independiente: pending T4;
    no ejecutados por T3. Sin cambios en codigo/tests ni memoria, logs o backups.
- T4: passed.
  - `python3 -m unittest discover -s control/tests`: passed, 233 tests
    (1 skip opt-in), 64.818 s, exit 0.
  - `python3 validate-skills.py skills`: passed, exit 0, `[ok] 12 skills valid`.
  - `./opencode-ecosystem status`: passed, `[ok] sin drift`.
  - `./scripts/qa-gate.sh --strict`: passed, exit 0; staged no aplicable,
    rutas rastreadas comprobadas; no certifica unstaged.
  - Copia selectiva runtime de `scripts/qa-gate.sh` y
    `skills/qa-gate/SKILL.md`: passed; sin memoria, backups ni otros archivos.
  - `./verify.sh` primer intento: failed solo por `plugin doctor` rc=1:
    OpenCode actualizado a v2.0.22 frente al pin v2.0.18. Sin plugins ni
    hooks en uso; `plugin_doctor.sh pin` actualizado a v2.0.22 y el doctor
    paso a `RESULTADO: plugins sanos`.
  - `./verify.sh` final: passed, `[ok] verify verde`; higiene solo aviso
    informativo rc=1. Sin stage, commit, push, PR ni sync general.
  - Revision independiente T1/T2/T3: passed en contexto fresco.

## Progreso
- Estado: done (en observacion 7 dias desde 2026-10-03).
- T1: passed; verificador independiente del delta tras el autochequeo.
- T2: passed; verificador independiente del ajuste de timeout.
- T3: passed; revision independiente de documentacion.
- T4: passed; suite completa, copia selectiva, runtime y `verify.sh` verde.
- Ultima tarea: cierre final observado y registrado.
- Siguiente: uso normal y revision del periodo prudencial; rollback manual
  solo tras decision humana.
- Bloqueos: ninguno.
