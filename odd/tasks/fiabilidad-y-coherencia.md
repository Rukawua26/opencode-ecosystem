# Fiabilidad y coherencia del ecosistema

## Objetivo
Aplicar pasos 1-3 y cierre del plan aprobado: proteger operaciones mutantes, precisar drift/diagnostico y alinear documentacion. No cambiar politica ODD (paso 4 requiere aprobacion separada).

## Problema y por que
Auditoria read-only detecto MEMORY.md en manifiesto borrable por uninstall; copias/backup fallidos no detienen operaciones; publish elimina skills antes de sustituirlas; status omite cron; descripciones RAM guard/servidor/skills/DCP no coinciden con comportamiento.

## Alcance
Correcciones minimas verificables reutilizando CLI, control/collect y tests existentes. Tests aislados con HOME temporal, fallos simulados y checks de preservacion. Comparacion read-only de horarios/comandos systemd si hay mecanismo existente viable; ante desconocido informar, no adivinar. Docs coherentes, sin reorganizar carpetas ni instalar capacidades Gentle.

## Restricciones
No commits, ramas, push, deploy ni dependencias. No migrar SQLite. No tocar memoria viva, receipts, backups ni logs manualmente. No ejecutar uninstall/publish sobre instalacion real. No modificar timers activos/perfiles shell/plugins personales/modelos/umbrales ni repinear. Runtime solo sync oficial de gestionados necesarios tras auditar diff, preservando personalizaciones. Antes/despues status.

## No romper
CLI argumentos/codigos existentes salvo correccion de falsos exitos. No borrar trabajo ajeno: README y configs tienen cambios previos propios; docs/zap-mcp.md tiene cambios ajenos: preservar su diff y evitar editarlo sin poder aislar claramente correccion aditiva. Nuevos ficheros previos test_checked_launcher/opencode-checked/documentos se conservan. Los manifiestos antiguos nunca autorizan borrar memoria viva ni escapar del destino gestionado. No convertir informacion de systemd desconocida en saludable. No cambiar politica RAM guard ni reglas ODD/skills/globales.

## TDD
Modo: off. Fuente: default. Runner: python3 -m unittest discover -s control/tests. Tests funcionales aislados obligatorios; observar fallos originales cuando viable sin mutar estado real.

## Tareas
- [x] T1: proteger sync/publish/uninstall, manifiestos nuevos y antiguos, copias/backup fallidos, sustitucion skills preparada/validada antes de reemplazo; tests aislados de errores/preservacion y baseline reversible exacto. Reutilizar helpers existentes; minimo sin framework nuevo. Actualizar evidencia.
- [x] T2: status incluye cron y cobertura precisa; revisar contraste systemd actual y usar consultas read-only existentes para horarios/comandos o indicar limitacion explicita sin implementar parser fragil ni contrato nuevo. Tests drift/errores. No tocar timers reales.
- [x] T3: docs precisas RAM guard, servidor, inventario skills, DCP/consumidor, cron/status; cerrar registro compactacion con evidencia posterior sin borrar historial. Guía ZAP preservar cambios ajenos: correccion aditiva aislada si segura, sino registrar discrepancia pendiente. Documentar evolucion con template. Validar config efectiva antes/despues sin volcar secretos; sync solo necesario y seguro. Ejecutar tests, validate-skills, status, verify.sh y QA strict.
- [x] T4: verificacion independiente de cada tarea worker antes de avanzar; cierre integrado tras ultima tarea.

## Criterios de aceptacion
- [x] Memoria viva no aparece como eliminable aun en manifiesto antiguo; backup fallido nunca autoriza borrar.
- [x] Fallos copias/validacion retornan error, sin mensaje de exito falso; skills originales preservadas ante fallo preparacion.
- [x] Cron drift detectado; cobertura y desconocidos descritos honestamente.
- [x] Docs operativas ajustadas a codigo, sin cambio politica ODD/RAM guard.
- [x] Tests completos, skills, status, verify y QA reportados honestamente; sin regresiones de config.

## Decisiones aceptadas
Saneamiento primero, capacidades despues. No añadir set -e indiscriminado ni transacciones generales sin necesidad; explicitar fallos en operaciones existentes. No prometer atomicidad completa si no existe. Mantener historial y fuente Git reversible sin commits. No hay forma mas simple que corregir guardas existentes y probar fallos aislados; no se necesita segundo runtime.

## Reutilizacion investigada
opencode-ecosystem managed_list/backup_dest/cmd_*; control/collect.py timers, control/tests y verify.sh. Buscar equivalentes antes de helpers. Metadatos de contexto locales ausentes segun auditoria; no reconstruir contexto global en esta feature.

T1: busqueda dirigida `uninstall|backup_dest|cmd_publish|ecosystem.*sync` en control/tests: solo referencia frontend, sin suite funcional equivalente. Se reutilizan managed_list, backup_dest, cmd_* y validate-skills.py; tests siguen unittest, subprocess y TemporaryDirectory de test_checked_launcher.py, sin alterar ese trabajo previo. Se anaden solo safe_tree (rechazo de enlaces/antecesores) y managed_path (allowlist y profundidad del manifiesto), porque no habia guardas equivalentes. Preparacion local con mktemp/cp/mv, sin framework transaccional ni dependencias.

T2: busqueda dirigida `list-timers|NextElapse|TimersCalendar|ExecStart|systemctl.*show` en control: solo _systemd_timers y crosscheck_timers realizan observacion; no existe comparador de horarios/comandos reutilizable. Se reutiliza diff en cmd_status y el fixture HOME temporal/run_cli/fail_command de test_ecosystem_mutations (sin heredar sus tests). Se conserva el parser key=value de systemctl show y el esquema TimerInfo; no se crea parser cron/ExecStart ni modulo nuevo de produccion.

T3: se reutilizan README, control/README, docstring existente, notas de compactacion y template de evolucion; sin helpers/modulos nuevos. Busqueda dirigida DCP en fuente: CLI copia/compara, collect inventaria, plantilla MEMORY contiene referencia historica; ninguno demuestra un consumidor de poda. API/config oficial filtrada y hashes stdlib para contraste sin persistir stdout. Contexto local docs/agent-context ausente; consulta list del indice global confirma proyecto, sin reconstruir metadatos.

## Evidencia
### T1 — worker, 2026-10-14
- Baseline reversible exacto: HEAD `8bc6069231768db00841dd679655bd168695b5f7`. CLI sin cambios previos al inicio; su version base se conserva en ese objeto Git (sin crear commits/ramas ni restaurar archivos). README.md, configs/opencode.jsonc, docs/zap-mcp.md y nuevos archivos de lanzador/compactacion permanecen ajenos a T1 y sin edicion del worker.
- Auditoria dirigida: managed_list incluia MEMORY.md; sync ignoraba backup/cp/chmod; publish borraba skills antes de copiar e ignoraba errores; uninstall aceptaba cualquier ruta del manifiesto y borraba aunque fallase backup.
- Estado: passed. Reproduccion contra CLI extraida con `git show 8bc6069231768db00841dd679655bd168695b5f7:opencode-ecosystem` en /tmp/opencode y ejecutada con los fixtures de test_ecosystem_mutations: 5/5 fallos originales observados (memoria borrada, backups sync/uninstall fallidos ignorados, preparacion publish destructiva y copia config publish ignorada). Runner de contraste confirma 5 fallos esperados, 0 errores; nada mutante sobre HOME real.
- Cambios: MEMORY.md fuera del manifiesto nuevo y omitida en manifiesto viejo; manifiesto completo prevalidado antes de borrar, sin escapes ni enlaces; backup unico y exitoso requerido antes de borrar/sobrescribir; errores de copia/permisos/manifiesto propagados; publish copia y valida skills preparadas antes de mover originales, restaura ante fallo del reemplazo y conserva originales con diagnostico si tambien falla la restauracion.
- Estado: passed. `python3 -m unittest discover -s control/tests`: 328 tests, OK, 1 skipped existente. Incluye 19 pruebas aisladas nuevas en control/tests/test_ecosystem_mutations.py, HOME bajo /tmp/opencode, sin ejecutar scripts de memoria ni tocar runtime real.
- Estado: passed. `bash -n opencode-ecosystem` y `git diff --check`: exit 0.
- Estado: passed. `python3 validate-skills.py skills`: 13 skills validas.
- Estado: passed. `./opencode-ecosystem status`, antes y despues de la verificacion final: `[ok] sin drift`; solo lectura, sin sync/publish/uninstall reales.
- Estado: passed. `scripts/qa-gate.sh --strict`: exit 0; sin staged, rutas rastreadas comprobadas. No certifica codigo unstaged/nuevo: revisado directamente en esta tarea.
- Estado: pending. `./verify.sh` y documentacion de evolucion/cierre integrado corresponden a T3; no ejecutado por T1 (escribe verify-last.json fuera del repo). Verificacion independiente T4 pendiente.
- Limites deliberados: no atomicidad global de sync/publish, una copia tardia fallida puede dejar copias anteriores aplicadas, siempre con retorno de error. Rollback acotado a sustitucion de skills. Guardas conservadoras rechazan enlaces en arboles comprobados, incluso personales, sin modificarlos. No protege contra cambios concurrentes hostiles entre comprobacion y operacion. No se tocaron cron/status (T2), docs (T3), timers/modelos ni politica ODD.

### T2 — worker, 2026-10-14
- Estado: passed. Solo T2 por encargo explicito del padre; T1 y sus tests preservados. Cambios de produccion limitados a una comparacion cron en cmd_status y guardas de observacion systemd en control/collect.py, sin dependencias ni migraciones/contratos nuevos.
- Cobertura exacta de status para T3: compara bytes de configs/opencode.jsonc, dcp.jsonc y cron-jobs.json frente al runtime; compara recursivamente skills/ y scripts/; commands/ solo si existe en fuente y excluyendo *.bak-*; compara solo memory/kairos.sh y memory/autodream.sh. No certifica validez semantica de JSON, consumidores DCP, timers instalados, horarios/comandos efectivos, permisos ni memoria viva. Un error diff sigue retornando drift/exit 1 (no distingue diferencia de error de lectura, contrato conservado); nunca [ok].
- Estado: passed. Observacion systemd ahora descarta list-timers con retorno no cero/JSON invalido o estructura incorrecta; detalles comienzan inactivos, fallos/timeout/salida sin ActiveState quedan result=unknown y generan health.errors (health.ok=false incluso si otro timer esta activo). No se conservan activos de una consulta de detalle fallida. Sin modificar esquema, argumentos CLI, timers ni unidades.
- Estado: passed. Consultas reales exclusivamente read-only: `systemctl --user show opencode-kairos.timer opencode-ram-guard.timer --no-pager --property=Id,ActiveState,TimersCalendar,TimersMonotonic,Unit`; consulta de sus servicios con `--property=Id,ExecStart`; equivalente para opencode-control-reconcile.timer/.service; consulta de WorkingDirectory de control-reconcile. Exit 0. Los tres timers activos. Kairos: OnUnitActiveUSec=30min, OnBootUSec=5min; ram-guard: 5min/2min; control-reconcile: 5min/3min. ExecStart: kairos.sh con /home/miguel, ram-guard-lite.sh, python3 -m control.cli reconcile --apply con WorkingDirectory=/home/miguel/opencode-ecosystem. Solo resumen acotado, sin persistir salida completa ni ejecutar los comandos observados.
- Limitacion explicita para T3: cron declara */5 y */30 (calendario), las unidades observadas usan intervalos monotonicos desde activacion + arranque; frecuencia nominal semejante NO implica equivalencia de horario. crosscheck_timers contrasta solo nombres/presencia/actividad, no schedule ni command ni salida del servicio disparado. ExecStart de systemctl es una representacion estructurada textual con escapes/metadatos; normalizarla contra comandos shell y cron exigiría parser/contrato nuevo. Se descarta por alcance/fragilidad. Ausencia/fallo de list-timers devuelve [] y no identifica por separado indisponibilidad frente a ausencia; salud sin timers es false, no saludable. Las advertencias de divergencia conocidas no cambian por si solas health.ok (comportamiento previo conservado).
- Estado: passed. `python3 -m unittest control.tests.test_ecosystem_status control.tests.test_timer_observation control.tests.test_ecosystem_mutations control.tests.test_control`: 42 tests OK en comprobacion final.
- Estado: passed. `python3 -m unittest discover -s control/tests`: 340 tests OK, 1 skipped existente (328 previos + 12 nuevos). Nuevos tests: igualdad, cron diferente/ausente en fuente/runtime/ambos, error diff, destino directorio, exclusiones memoria/backups; list-timers fallido/JSON malformado, show fallido/timeout/incompleto, whitelist, detalle correcto/inactivo y health con fallo parcial/total. HOME temporal bajo /tmp/opencode y systemd mockeado; sin sleeps/reloj real en tests nuevos.
- Estado: passed. `python3 validate-skills.py skills`: 13 validas; `bash -n opencode-ecosystem`, `git diff --check`: exit 0. `scripts/qa-gate.sh --strict`: exit 0, rutas rastreadas comprobadas/sin staged; tests nuevos revisados directamente porque QA no certifica untracked.
- Estado: passed. `./opencode-ecosystem status` antes y despues: `[ok] sin drift`, exit 0. No sync/publish/uninstall reales, ni modificacion de memoria viva/logs/backups/timers. No edicion de docs ajenos ni politica ODD.
- Estado: pending. verify.sh y docs/evolution integrados corresponden a T3 (verify escribe estado fuera del repo); verificacion independiente corresponde a T4. No se marca cierre integrado.

### T3 — worker, 2026-10-14
- Estado: passed. El padre comunica T1 y T2 verificadas independientemente sin hallazgos antes de este encargo; se registra esa evidencia previa sin atribuirla a este worker. Sus implementaciones y tests se preservan sin cambios. T4 de cierre integrado no se marca completa.
- Estado: passed. README conserva integra la seccion previa del lanzador; describe RAM guard real (no compacta ni detecta huerfanos), acciones POST, skill ui-ux-master y cobertura exacta de status/cron/desconocidos. server.py solo cambia docstring; control/README elimina promesa read-only. No cambios de comportamiento T3.
- Estado: passed. DCP etiquetado inactivo/no acreditado: consumidores encontrados solo gestion/inventario; configuracion efectiva sin referencia DCP observada. No se activa ni modifica su archivo, ni se afirma ausencia universal de consumidores externos. Compactacion nativa efectiva sigue auto=true/buffer=8000.
- Estado: passed. Se inspecciono primero `git diff -- docs/zap-mcp.md`: trabajo ajeno de verificacion/arranque preservado, solo bloque aditivo identificado tras `Que es`. Distingue plantilla deshabilitada de instalacion historica, sustitucion de entorno de fallo observado y API key de security key MCP. No arranque/smoke-test/configuracion/secretos. Comprobacion actual ZAP no ejecutada, no se presenta el antecedente como nueva evidencia.
- Estado: passed. Evolucion creada con template en docs/evolution/20261014-fiabilidad-y-coherencia.md: base Git exacta, no regresion, limites y rollback por hunks. Notas de compactacion solo reciben evidencia posterior; prefijos originales preservados y comprobados por SHA-256 (4118/4655 bytes, hashes en evolucion). Fallo anterior plugin doctor permanece historico; ahora verify observa plugin doctor verde sin repineado en T3. Observacion longitudinal permanece pending.
- Estado: passed. `python3 -m unittest discover -s control/tests`: 340 tests en 35.011s, OK (1 skipped existente). `python3 validate-skills.py skills`: 13 skills validas. `./verify.sh` ejecutado dos veces, incluido despues de cambios de docs/docstring: exit 0, `[ok] verify verde`, todos los obligatorios completos. Informe canonico de metadatos fuera del repo, sin stdout persistido por el worker.
- Estado: passed. `scripts/qa-gate.sh --strict`: exit 0, sin staged, rutas rastreadas comprobadas; no certifica unstaged/untracked. Lentes reliability/risk ejecutadas sobre rutas candidatas segun skills, y lectura focal adicional de los tres tests nuevos untracked y diff T1/T2: sin hallazgos reales. Sin sleeps/reloj real, systemd mockeado y HOME temporal. Barrido solo encontro mencion documental TODO/FIXME, no defecto.
- Estado: passed. API `opencode api get /api/config` capturada/filtrada en memoria: lista de 3 fuentes, 1 info; hash JSON canonico antes/despues identico `07b25755436e8a8e53c95deb23f87898f1472813478759182e61805c8f374b77`, auto=true/buffer=8000. Primer intento de extraccion supuso dict y fallo localmente al recibir lista; corregido sin mutacion ni volcado de respuesta. Solo resumen acotado temporal en /tmp/opencode, sin config completa ni secretos.
- Estado: passed. SHA-256 runtime antes/despues identicos: opencode.jsonc `70eaaa8033eae39e24d7e46c30b2c15d2abd7688bbaaabc52f6c12cd35c3befd`; dcp.jsonc `61a3788a425a3e799a9540ba0c43dbe5b97c040d8dab597d7a3e5ad8a92876a3`; cron-jobs.json `c021e6d8c4d52e35b2cde68b3b6850189ebc9480dd5d49c0d25dad97ed56ff99`.
- Estado: passed. `./opencode-ecosystem status` real antes/despues: exit 0, `[ok] sin drift`. `git diff --check`: exit 0. No cambios en scripts fuente gestionados; CLI raiz y control no se instalan con sync. No sync necesario ni ejecutado; no mutacion runtime config/timers/modelos ni memoria viva/receipts/backups/logs manuales.
- Decision minima Gentle: conservar saneamiento local, sin capacidades nuevas ni reabrir research. Contradiccion/reglas ODD diferidas a aprobacion separada; no se cambian skills ni reglas.
- Estado: pending. Verificador independiente T3/cierre T4 corresponde al padre. No commits, ramas, push ni deploy.

### T4 — verificacion independiente
- T1: 19 tests aislados y 3 comprobaciones adicionales de enlaces/chmod/backup, sin hallazgos. No atomicidad global ni proteccion frente a carreras hostiles, limites declarados.
- T2: 42 tests aislados OK; cron/errores y salud desconocida contrastados, sin hallazgos.
- T3/cierre integrado: 340 tests OK (1 skipped), 13 skills validas, status sin drift, diff check y QA strict exit 0 reproducidos. Informe canonico verify completed/exit 0 revisado sin reejecutarlo. Hashes runtime/config y prefijos historicos contrastados. Sin hallazgos bloqueantes; preservacion del diff ajeno ZAP apoyada en contraste previo del worker, no inventada como nueva prueba independiente.

## Progreso
T1-T4 completadas con cierre integrado verificado. Sin commits, nuevas dependencias ni sync innecesario. Politica ODD explicitamente diferida a aprobacion separada. Observacion longitudinal compactacion pendiente, sin bloqueo local de verify actual.
