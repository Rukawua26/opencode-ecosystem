---
nombre: 20261014-compactacion-conservadora
fecha: 2026-10-14
estado: en_observacion
afecta: [configs, docs]
fuente: propio
---

# Compactacion conservadora

## Por que
La fuente declaraba `compaction.prune=true`, pero el runtime ya lo omitia. La auditoria fresca encontro exclusivamente esa diferencia byte a byte; `status` devolvia drift de opencode.jsonc.

## Antes
Fuente con `auto=true`, `prune=true`, `reserved=8000`; runtime identico salvo ausencia de prune. La API autenticada de OpenCode 2.0.29 normaliza la configuracion efectiva a `{"auto":true,"buffer":8000}`. La documentacion V2 no incluye prune.

## Despues
Se retira solo la linea prune de la fuente. Fuente y runtime coinciden sin ejecutar sync ni escribir personalizaciones. No se cambian modelos, umbrales, keep, salidas de herramientas ni reglas globales.

## Beneficio
Drift eliminado; no se atribuye ahorro de tokens ni mejora de compactacion a retirar un campo que no aparecia en la configuracion efectiva.

## No regresion
- Base reversible versionada exacta: `8bc6069231768db00841dd679655bd168695b5f7`, ruta `configs/opencode.jsonc`, sin cambios previos en esa ruta.
- Se conservan auto=true y buffer efectivo=8000, permisos, agentes, MCP, modelos y plugin personal. No se toca docs/zap-mcp.md (trabajo ajeno).
- No se ejecuta sync porque el runtime ya coincide; no se modifica memoria viva, receipts, backups ni logs manualmente.

## Verificacion
- passed: `python3 -m unittest discover -s control/tests`: 294 tests, OK, 1 skipped.
- passed: `python3 validate-skills.py skills`: 13 skills valid.
- passed: `./opencode-ecosystem status`: `[ok] sin drift`.
- passed: `scripts/qa-gate.sh --strict`: exit 0; sin staged, comprueba rutas rastreadas, no certifica contenido unstaged.
- failed (ajeno): `./verify.sh`: exit 1, solo plugin doctor rojo; restantes checks verdes, incluido debug config, unittest y QA. El informe canonico del script contiene solo metadatos, no stdout completo.
- failed (preexistente): `bash ~/tools/plugin_doctor.sh`: version pineada 2.0.27 frente a instalada 2.0.29. Plugin TUI personal uso/tui.tsx, 6 tokens presentes; sin hooks de servidor. No se repinea ni se modifica el plugin.
- passed: `opencode api get /api/config`, filtrado en memoria: compaction efectiva `auto=true, buffer=8000`; keep no explicitado. `opencode api` reutiliza descubrimiento/autenticacion oficial, sin exponer secretos.
- Medicion puntual mediante `opencode api get /api/experimental/session/stats`, filtrada en memoria: rango epoch-ms 1789094999964..1792007212404; 122 sesiones, 1883 prompts, 17042 steps, 320 subagentes, 32 dias activos. Tokens acumulados: input 304239548, output 6901160, reasoning 4045942, cache read 1671644539 y write 935950. Son agregados historicos, NO ventana actual ni evidencia de un umbral apropiado.
- Limitaciones de exploracion: `/openapi.json` via CLI produjo JSON truncado; descarga publica con urllib devolvio 403. No se persistieron sus salidas. API/config y stats si respondieron con JSON valido; no se consultaron context ni mensajes.

## Periodo prudencial
- Observacion longitudinal pendiente durante varias tareas reales; no se generan tokens artificiales ni se declara estabilidad de compactacion a partir de agregados.
- Reutilizar los habitos existentes de handoff/compactacion y consulta de metadatos cuando proceda, sin nuevas reglas o automatizaciones. Antes de proponer umbrales, obtener evidencia de ventana real y compactaciones sin conversaciones ni secretos.
- Estable: fuente/runtime sin drift y comportamiento de tareas reales sin regresiones atribuibles. Reabrir si aparece una regresion demostrada o deriva de configuracion efectiva.
- Rollback acotado: recuperar solo la linea prune desde la ruta y HEAD anteriores, con aprobacion y sin sobrescribir cambios posteriores; ello reintroduciria el drift previo, no es una mejora funcional demostrada. No borrar la base Git durante la observacion.

## Fuente (si aplica)
Documentacion oficial: https://opencode.ai/v2/docs/config, https://opencode.ai/v2/docs/compaction y https://opencode.ai/v2/docs/api. Sin codigo externo incorporado.

## Evidencia posterior — 2026-10-14, T3 fiabilidad y coherencia

Sin borrar ni reinterpretar los fallos anteriores: `./verify.sh` ejecutado en
T3 devuelve exit 0, `[ok] verify verde`, incluido plugin doctor. No se ha
repineado ni modificado el plugin en T3; este resultado posterior no explica
por si solo el cambio del entorno. Suite: 340 tests OK, 1 skipped existente;
skills: 13 validas; QA strict exit 0 (sin staged, no certifica unstaged).
Status antes de editar: `[ok] sin drift`. API/config filtrada en memoria:
`auto=true, buffer=8000`; no se cambian umbrales ni configuracion runtime.
La observacion longitudinal sigue pendiente; este cierre local posterior no
demuestra ahorro de tokens ni estabilidad de compactaciones reales.
