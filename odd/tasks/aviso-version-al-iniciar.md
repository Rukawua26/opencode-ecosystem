# Aviso de version al iniciar

## Objetivo
Implementar el lanzador ligero aprobado: al cerrar y abrir OpenCode mediante el lanzador, comparar version instalada con pin aprobado y solicitar autorizacion de revision si cambio.

## Problema y por que
OpenCode puede cambiar sin haber revisado compatibilidad del ecosistema. plugin_doctor detecta desfase pero no esta integrado en el lanzamiento.

## Alcance
Lanzador explicito ligero en fuente de verdad, Python stdlib, tests aislados y documentacion de uso. Integrar en instalacion/sync existente solo si ya hay mecanismo seguro, sin sobrescribir binarios ni configuracion shell. Comprobacion local, acotada, sin red ni polling. Misma version: silencio. Diferencia: versiones y solicitud humana para revisar; nunca actualizar automaticamente. Rechazo: abrir normalmente sin adaptar. Aceptacion: dejar clara la autorizacion de revision solamente y como solicitarla en chat, sin fingir inyeccion al agente. Sin TTY: no esperar entrada ni inferir permiso. Pasar argumentos y estado de salida correctamente y evitar recursion.

## Restricciones
No tocar /usr/bin/opencode, plugin personal, perfil shell, SQLite, memoria viva, receipts, logs ni backups manuales. No commits ni push. No cambiar pin, auto-update ni realizar migraciones/sync automaticos al arrancar. No instalar Gentle. Trabajo ajeno docs/zap-mcp.md intocable; cambios de compactacion previos se preservan.

## No romper
CLI directa sigue disponible; argumentos con espacios, --help, --version y comandos no interactivos no deben quedar bloqueados por preguntas. No prometer cobertura de web/API ni de sesiones nuevas en TUI abierta. Pin ausente/invalido y version no legible se informan sin aceptar actualizacion. No ejecutar cadenas originadas en salida del modelo ni binario.

## TDD
Modo: off. Fuente: default. Runner: python3 -m unittest discover -s control/tests. Tests funcionales aislados obligatorios.

## Tareas
- [x] T1: auditar reutilizacion existente (control/cli.py probe, plugin_doctor, scripts e instalacion); implementar lanzador minimo y tests de bordes y consentimiento; documentar README y evolucion segun template con base reversible Git; instalar solo mediante mecanismo existente seguro si disponible o dar ruta ejecutable explicita; ejecutar tests, validate-skills, status, verify.sh y QA strict. Documentar rutas y cobertura exactas, sin prometer arranque automatico por binario directo. Reabierta tras T2 por captura stdout sin cota de disco y errores de lectura de consentimiento no capturados; corregida y verificada localmente de nuevo.
- [x] T2: verificador independiente read-only comprueba requisitos, tests y diff; dos hallazgos iniciales corregidos y reverificados.

## Criterios de aceptacion
- [x] Mismo pin silencioso; cambio pregunta solo en lanzamiento interactivo; no-tty sin bloqueo.
- [x] Sin cambios automaticos; consentimiento no se confunde con permiso para mutar.
- [x] Argumentos y exit code preservados, sin recursion; errores diagnosticados acotadamente.
- [x] Checks de cierre reportados con evidencia y trabajo ajeno preservado.

## Decisiones aceptadas
Se elige lanzador explicito en vez de plugin por menor mantenimiento, sin dependencia ni proceso residente. La apertura directa con opencode no queda interceptada automaticamente: documentar comando real. Aceptacion autoriza revision, no adaptacion automatica. Si integrar invocacion necesita sobrescribir shell/binario, parar esa integracion y entregar lanzador explicito.

## Reutilizacion investigada
Exploracion previa: /home/miguel/tools/plugin_doctor.sh compara .config/opencode/.opencode-version.pin; control/cli.py tiene probe stdlib con timeout. Revisar firmas actuales antes de reutilizar; evitar importar modulos pesados o duplicar detector sin justificar.

T1: firmas revisadas. Se reutiliza ruta/contrato del pin de plugin_doctor y patron
subprocess argv + timeout=3 de control/cli.py. No se importa _opencode_diagnostic:
importa db/runner/state y devuelve compatibilidad 2.x, no el pin exacto ni binario
seleccionado. El pequeno parser local admite tanto `2.0.0` como `opencode v2.0.0`
y sufijos; rechaza texto libre/control. No se crea modulo generico adicional.
managed_list solo instala scripts/*.sh; sync copia configs y crea backups.
Se descarta integracion por innecesaria: ejecutable raiz `opencode-checked`.
docs/agent-context no existe aqui; se consulto el indice query_context.py list.

Reapertura T1: busqueda dirigida en control/ de selectors/DefaultSelector/os.read
y monotonic: solo cronometraje en runner/state, sin capturador acotado reutilizable.
Se sustituye la captura temporal por un unico helper local probe_version para
encapsular ciclo de vida/limites del proceso, sin importar control ni dependencias.

## Evidencia
T1 Estado: passed (reapertura corregida; evidencia inicial historica debajo).
- Base Git previa: 8bc6069231768db00841dd679655bd168695b5f7; README recuperable
  en ese commit y archivos nuevos retirables selectivamente. Sin commits nuevos.
- Ruta ejecutable: /home/miguel/opencode-ecosystem/opencode-checked (modo 755).
- Tests nuevos: control/tests/test_checked_launcher.py, 11 casos: match,
  rechazo, aceptacion solo revision, respuesta desconocida/EOF, noTTY sin leer,
  pin ausente/invalido, timeout/OSError/salida invalida/returncode probe,
  argv con espacios/help/version/ruta, recursion directa/guard, missing binary,
  integracion con binario falso que conserva exit=37.
- passed: python3 -m unittest control.tests.test_checked_launcher: 11 OK.
- passed: python3 -m unittest discover -s control/tests: 305 tests OK,
  skipped=1 preexistente; ejecucion de 90.366 s.
- passed: python3 validate-skills.py skills: [ok] 13 skills valid.
- passed: ./opencode-ecosystem status: [ok] sin drift.
- passed: ./verify.sh: [ok] verify verde; repetido tras fortalecer tests,
  incluye unittest del working tree, status, plugin doctor y QA strict.
- passed: scripts/qa-gate.sh --strict: exit 0. Staged no aplicable;
  solo rutas rastreadas, no certifica codigo nuevo/unstaged. Revision manual de
  codigo nuevo sin secretos, shell=True, eval ni comandos construidos de salida.
- Probe corregido: pipe stdlib con selectors, lectura acumulada maxima 257 bytes;
  rechaza mas de 256, no captura a disco. Deadline monotonic global de 3 s para
  lectura y wait; mata/recolecta el proceso al fallar. stderr descartado.
- Revision interna de bloques/razones/entradas inesperadas completada.
  Tests sin red, runtime ni sleeps. TTY real y uso humano quedan en observacion.
- Trabajo previo preservado: configs/opencode.jsonc, docs/zap-mcp.md y
  documentos de compactacion. Sin sync, instalaciones ni cambios de pin.
- Docs: README.md y docs/evolution/20261014-aviso-version-al-iniciar.md.

### Evidencia de reapertura T1
- passed: python3 -m unittest control.tests.test_checked_launcher: 15 OK,
  3.326 s. Nuevas regresiones: stdout continuo en bloques de 1 MiB rechazado
  con lectura maxima 257 y sin TemporaryFile; timeout con stdout abierto;
  OSError/UnicodeError en readline llegan a exec sin consentimiento ni detalles
  de excepcion. Probe real correcto y returncode no cero tambien cubiertos.
- passed: python3 -m unittest discover -s control/tests: 309 tests OK en
  83.880 s, skipped=1 preexistente.
- passed: python3 validate-skills.py skills: [ok] 13 skills valid.
- passed: ./opencode-ecosystem status: [ok] sin drift.
- passed: ./verify.sh: [ok] verify verde, incluidos tests, status y QA strict.
- passed: scripts/qa-gate.sh --strict: exit 0; sin staged, no certifica
  nuevas lineas/unstaged. Codigo revisado manualmente, sin comandos inyectados.
- passed: git diff --check: exit 0. Sin commits, delegacion, sync ni cambios
  de trabajo ajeno. Autochequeo de bloques/razones/entradas inesperadas repetido.

## Progreso
T1 y T2 completadas. Verificador independiente reprodujo 15 tests OK en
3.306 s y diff check limpio; ambos hallazgos cerrados, sin nuevos hallazgos.
Captura acotada sin disco y errores de consentimiento permiten abrir sin permiso.
Checks completos verdes. Sin commits. Pendiente solo observacion humana en TTY;
el comando directo opencode no queda interceptado y el aviso no adapta nada.
