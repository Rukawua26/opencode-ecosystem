# Compactacion conservadora

## Objetivo
Aplicar el plan aprobado de saneamiento minimo sin cambiar la politica de compactacion.

## Problema y por que
La revision previa detecto drift: la fuente conserva compaction.prune=true y el runtime ya lo omite. V2 ignora ese campo. No hay evidencia suficiente para imponer 300k/400k.

## Alcance
Reconciliar exclusivamente esa diferencia, documentar configuracion efectiva, observar metricas disponibles sin guardar conversaciones y ejecutar verificacion completa. Documentar habitos usando mecanismos existentes; no crear automatizaciones ni reglas nuevas innecesarias.

## Restricciones
Sin commits, ramas, push, deploy, dependencias, cambios SQLite, memoria viva, receipts, backups ni logs manuales. Sync oficial autorizado solo tras comprobar su alcance y preservar personalizaciones. No instalar Gentle AI/Shell. No modificar limites, buffer=8000, auto=true, keep ni salidas de herramientas.

## No romper
Preservar modelos, permisos, agentes, MCP y plugin personal. docs/zap-mcp.md tiene trabajo ajeno: no tocar ni revertir. No repinear plugin_doctor automaticamente para pasar checks; reportar desfase por separado.

## TDD
Modo: off. Fuente: default. Runner: python3 -m unittest discover -s control/tests. Checks funcionales obligatorios.

## Tareas
- [x] T1: worker audita diferencias actuales, retira solo prune si confirma el diagnostico, documenta evolucion segun docs/evolution/_TEMPLATE.md y evidencia acotada; verifica y sincroniza solo si necesario y seguro. Reutilizar comparacion/config/API y scripts existentes. Registrar metricas reales disponibles sin transcripciones, nunca confundir tokens acumulados con ventana actual. Si no hay datos suficientes, marcar observacion pendiente sin inventar mediciones. Ejecutar tests, validate-skills, status, verify.sh y qa-gate --strict; corregir solo errores causados o dentro del alcance y reportar bloqueos ajenos.
- [x] T2: verificador independiente read-only contrasta diff, alcance, configuracion efectiva y resultados.

## Criterios de aceptacion
- [x] prune ausente de fuente y runtime, resto de configuracion efectiva preservada.
- [x] status sin drift o bloqueo concreto demostrado.
- [x] Verificaciones reportadas honestamente, incluidas incidencias preexistentes.
- [x] Sin umbral nuevo ni instalaciones Gentle; observacion longitudinal no fingida.

## Decisiones aceptadas
Primero saneamiento, despues medicion, umbral solo con evidencia y aprobacion futura. Sintaxis V1 soportada se conserva. Base reversible exacta: `8bc6069231768db00841dd679655bd168695b5f7` para configs/opencode.jsonc, limpia antes del cambio; no crear commit. El desfase de plugin_doctor se reporta, no se oculta.

## Reutilizacion investigada
configs/opencode.jsonc, CLI status/sync, verify.sh, scripts/qa-gate.sh, API /api/config y docs de OpenCode V2 existentes. No se necesitan helpers nuevos.
Auditoria byte a byte mediante comparacion en memoria: unica diferencia prune. Se reutiliza CLI API autenticada y stats existentes; no se crean helpers persistentes. Sync descartado por innecesario y por evitar escrituras ajenas.

## Evidencia
2026-10-14, T1: ver detalle acotado en `docs/evolution/20261014-compactacion-conservadora.md`.
- passed: tests 294, OK (1 skipped); validate-skills 13 valid; status `[ok] sin drift`; QA strict exit 0 (sin staged, no certifica unstaged).
- failed ajeno: verify.sh exit 1 exclusivamente por plugin_doctor (pin 2.0.27, instalada 2.0.29); tokens del plugin presentes, sin repinear. Resto de checks verify passed.
- passed: API/config muestra auto=true, buffer=8000 sin prune; fuente y runtime identicos. No sync.
- passed: stats autenticadas existentes, 122 sesiones/1883 prompts/17042 steps; agregados historicos, no ventana actual. Medicion detallada y rango en evolucion. Sin /context, mensajes, exportaciones, secretos ni stdout completo persistido.
- unavailable parcial: OpenAPI CLI truncado y descarga publica urllib 403; no bloquean API/config ni stats validas.
- pending: observacion longitudinal de tareas reales; no se infieren umbrales ni ahorro.
- passed T2: verificador independiente sin hallazgos; reprodujo tests (294 OK, 1 skipped), skills (13 valid), QA strict exit 0 y status sin drift. Confirmo equivalencia fuente/runtime y fallo exclusivo preexistente de plugin_doctor; no certifica cierre global verde.

## Progreso
T1 y T2 completadas; saneamiento verificado independientemente. Cierre global bloqueado por desfase preexistente de plugin_doctor, fuera del alcance aprobado de repineado. No commits. Observacion de varias tareas reales pendiente; no se modifican umbrales sin evidencia y aprobacion futura.

### Actualizacion posterior de cierre — 2026-10-14, T3 fiabilidad y coherencia

El bloqueo de cierre arriba es historico: una ejecucion posterior de
`./verify.sh` dio exit 0, incluido plugin doctor, sin repineado ni cambios del
plugin en T3. Tests 340 OK (1 skipped), skills 13 validas, QA strict exit 0.
No sustituye la evidencia anterior ni acredita observacion longitudinal;
esa observacion sigue pendiente. Ver detalle en la evolucion de compactacion
y comparacion efectiva antes/despues en `odd/tasks/fiabilidad-y-coherencia.md`.
