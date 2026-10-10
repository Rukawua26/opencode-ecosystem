---
nombre: 2026-10-03-cierre-fiable
fecha: 2026-10-03
estado: en_observacion
afecta: [skills, scripts, docs]
fuente: propio
---

# Cierre fiable y explicito

## Por que
El humano y los agentes necesitaban recordar varios comandos para cerrar: verify
no incluia unittest ni QA strict. El gate podia imprimir fragmentos fuente con
secretos y confundir fallo de Git con ausencia de staged. El alcance fue aprobado
el 2026-10-02; el trabajo se registra en `odd/tasks/cierre-fiable.md`, sin renombrarlo.
Esta nota describe la fuente local, no un cierre global ni runtime ya actualizado.

## Antes
- verify reunia controles de higiene/config/drift/doctores sin suite ni QA strict.
- QA ocultaba errores Git y podia publicar codigo en hallazgos logs/TODO.
- La skill no distinguia fallo operativo, no aplicable y analisis completo;
  tests de working tree y QA de staging no quedaban explicitamente separados.

## Despues
- `./verify.sh`, sin argumentos, es el cierre local unico. Conserva validadores
  de skills fuente/runtime, config, drift y doctores; agrega discovery no vacio,
  unittest obligatorio, consulta staged y QA strict SIEMPRE, incluso sin staged.
- Controles secuenciales con etiquetas/alcance y estados ok/warn/fail/unavailable/
  incomplete. Los fallos de checks no impiden recoger los siguientes. Exit 0
  exige todos los obligatorios completos; 1 indica rojo; 2 argumentos invalidos
  o entorno inicial ausente. Hygiene rc=1 es aviso; otros fallos no son verde.
- stdout/stderr de los hijos de verify se descartan en DEVNULL, sin persistencia.
  QA solo publica ruta escapada/redactada, linea y etiquetas propias, nunca
  snippets, errores Git crudos ni excepciones externas.
- Tests leen working tree; QA consulta el indice canonico y rutas rastreadas
  desde la raiz. verify fija ECO=`~/opencode-ecosystem`; QA independiente descubre
  el repo del cwd, tambien desde subdirectorios. Ambos ignoran TODO `GIT_*`
  heredado, no aceptan indice alternativo ni redireccion a otro repo/config Git.
- Sin staged: analisis staged no aplicable; las rutas sensibles rastreadas
  siguen comprobadas. No se escanea implicitamente codigo unstaged, no se congela
  un candidato y no se ofrece certificacion SAST/SCA.
- QA warn=0 por hallazgos; strict=1 por catch vacio, secreto o ruta sensible
  rastreada. Logs/TODO/FIXME y riesgos son avisos. Error operativo, argumentos
  invalidos o analisis incompleto=2 en ambos modos: no equivalen a aprobacion.
- Catalogo textual sobre lineas anadidas. Solo riesgos de produccion excluyen
  tests y comentarios; secretos no los excluyen. Binarios, formatos no soportados
  y diffs/hunks/cabeceras incompletos fallan con 2 incluso en warn: limitacion
  conservadora de capacidad textual, no afirmacion de auditoria binaria.
  Archivos vacios validos SHA-1/SHA-256, permisos y borrados textuales completos
  siguen admitidos.
- QA usa timeout Git de 15 s por comando y transporte temporal descartado;
  lee hasta 16 MiB por salida. Es limite de LECTURA, NO hard cap de disco/RAM:
  el temporal puede crecer antes de leer y el parser necesita memoria adicional.
  Muestra hasta 50 hallazgos, contando y evaluando todos; un bloqueante posterior
  al cap sigue produciendo strict=1.
- verify usa GNU timeout con KILL al deadline: 15 s consulta Git, 30 s higiene/
  skills, 60 s otros controles/QA/discovery, 180 s unittest. Termina el grupo
  normal de timeout, no procesos deliberadamente detached fuera del grupo.
  Desactiva trace/verbose/errexit heredados antes de expandir datos; BASH_ENV
  arbitrario ejecutado antes de la primera linea queda fuera de esta garantia.
  No es un sandbox ni un limite duro global de recursos.
- Se reutiliza Python stdlib embebido en qa-gate.sh: el sync existente gestiona
  scripts/*.sh, sin ampliar contratos para modulos nuevos. Esta feature excluye
  sync general, pues toca memoria/backups. T4 queda a cargo del padre: status
  antes/despues y copia selectiva SOLO de scripts/qa-gate.sh y
  skills/qa-gate/SKILL.md a sus rutas homonimas bajo ~/.config/opencode.
  verify.sh es local y no se copia al runtime. No se sincronizan cambios ajenos.

## Beneficio
- Esperado: un solo comando de cierre y menos falsos verdes; menos exposicion de
  codigo/secretos en resultados. Cero dependencias nuevas y controles secuenciales
  compatibles con i5-1235U / 8 GB, sin daemons ni polling.
- Medido: suite completa de 233 tests (1 skip) en 64.818 s; T1 35 y T2 14
  focalizados passed segun el ODD; `verify.sh` verde y `status` sin drift tras
  la copia selectiva runtime.
- Ahorro de tokens/RAM y reduccion de incidentes: no medidos. Cierre completo,
  runtime y no regresion final: passed. El pin de OpenCode se actualizo a
  v2.0.22 tras revisar hooks; sin plugins en uso, no hubo deriva de hooks.

## No regresion
- Conservar catalogo previo, warn=0 por hallazgos y strict=1 por bloqueantes;
  errores operativos no aprueban, sin staged no certifica codigo.
- Mantener controles anteriores de verify, sin verde incompleto y sin nuevas
  dependencias, esquema SQLite, memoria, logs, receipts, backups o commits.
- Base reversible existente en Git: `1baf106108c2da0f3fb25c1f2053ce0e237dbda9`.
  Originales versionados y limpios antes del cambio: README.md, verify.sh,
  scripts/qa-gate.sh, skills/qa-gate/SKILL.md y control/tests/test_qa_gate.py.
  No se creo commit ni copia .before.md: esos originales ya estan preservados.
  La base NO incluye test_verify.py, esta nota ni el documento ODD nuevos.
- Revisiones independientes de T1/T2/T3 y no regresion completa: passed.
  La evidencia historica de fallos y reaperturas permanece en el ODD.

## Verificacion
- Baseline registrado en ODD: unittest 189 tests (1 skipped), skills 12 valid,
  status `[ok] sin drift`; es evidencia previa, no resultado del cambio actual.
- T3 `python3 validate-skills.py skills`: passed, exit 0, `[ok] 12 skills valid`.
- T3 `git diff --check -- README.md skills/qa-gate/SKILL.md odd/tasks/cierre-fiable.md docs/evolution/2026-10-03-cierre-fiable.md`:
  passed, exit 0, sin avisos; los dos nuevos no rastreados no entran en ese diff.
- Ambos nuevos revisados tambien con `git diff --no-index --check -- /dev/null
  <ruta>`: sin avisos de whitespace, exit 1 por diferencias en modo no-index,
  no presentarlo como exit 0. Comprobacion directa Python stdlib de whitespace
  sobre los cuatro documentos y skill ASCII: passed, exit 0,
  `[ok] whitespace: 4 documentos; skill ASCII sin acentos`.
- Suite completa `python3 -m unittest discover -s control/tests`: passed,
  233 tests (1 skip opt-in), 64.818 s.
- `./scripts/qa-gate.sh --strict`: passed, exit 0; staged no aplicable y rutas
  rastreadas comprobadas.
- `./opencode-ecosystem status`: passed, `[ok] sin drift`.
- `./verify.sh`: passed, `[ok] verify verde`; higiene solo aviso informativo.
- `python3 validate-skills.py skills` y runtime: passed, `[ok] 12 skills valid`.
- Copia selectiva runtime de `scripts/qa-gate.sh` y `skills/qa-gate/SKILL.md`:
  passed, sin memoria, backups ni otros archivos.
- Revision independiente T1/T2/T3: passed.
- OpenCode se actualizo a v2.0.22; `plugin_doctor.sh pin` actualizado y plugins
  sanos. Fue necesario para que `verify.sh` fuera verde; sin stage/commit.

## Periodo prudencial
- Minimo 7 dias desde 2026-10-03 y varios ciclos de uso normal con/sin staged,
  warn/strict y errores controlados. La verificacion final satisfactoria ya
  ocurrio; el estado queda en observacion durante el periodo.
- Conservar la baseline durante todo el periodo. Estable si controles completos,
  scope correcto, sin fugas/falsos verdes y status sin drift del alcance; revisar
  si hay regresiones, falsos positivos frecuentes o fallos operativos silenciados.
- Rollback manual solo tras decision humana: comparar diff actual y
  `git show 1baf106108c2da0f3fb25c1f2053ce0e237dbda9:<ruta>` para CADA original
  de la lista anterior. Si no hay ediciones posteriores/ajenas, restaurar solo
  ese contenido desde Git; si las hay, retirar por parche solo este cambio.
  Nunca reset/checkout global ni descartar trabajo ajeno.
  Ejemplo SOLO tras esa comprobacion/aprobacion:
  `git show 1baf106108c2da0f3fb25c1f2053ce0e237dbda9:skills/qa-gate/SKILL.md > skills/qa-gate/SKILL.md`;
  repetir exclusivamente para los otros originales aprobados de la lista.
- Los nuevos test_verify.py/nota/ODD no tienen original en esa base: revisar
  separadamente, conservar evidencia e historial y marcar esta nota revertido;
  no borrarlos automaticamente ni afirmar que Git baseline los restaura.
- Si el runtime ya fue actualizado, copiar selectivamente solo gate/skill
  aprobados y comprobar status antes/despues; repetir validaciones y cierre.
  No sync general, memoria/backups ni rollback de cambios ajenos. Ningun rollback
  se ha ejecutado; una baseline antigua no certifica seguridad del cierre.

## Fuente (si aplica)
Implementacion propia reutilizando verify, QA, unittest y validadores locales;
plantilla `_TEMPLATE.md` y evolucion `2026-09-22-qa-gate-secretos.md` como formato
e historial, sin repetir su rollback global. Referencias conceptuales del alcance
aprobado: GentleAI `5140c5...` y Shellac `6715...`; no se copio codigo ni se creo
otro analisis externo. Ficha GentleAI existente: `~/docs/sources/gentle-ai-analysis.md`
(TOMADO/DEJADO). No afirmar validacion nueva de esos repos ni hashes completos
no observados.
