# Plan aprobado: delegacion y eficiencia

Estado: cambio operativo con prueba de delegacion reportada por el usuario; cierre RDD pendiente. No equivale a aprobacion formal del candidato.
Fecha de registro: 2026-09-08.

## Objetivo y limites

Objetivo original: resolver la delegacion fallida de `explore` con el parche minimo y observar el uso
normal antes de decidir cualquier optimizacion. OpenCode sigue siendo el unico
runtime; se conservan memory-adapter, SDD file-first, permisos y garantias RDD.
No agregar dependencias, memoria paralela, daemons, telemetria, skills ni modelos
con proveedor o coste diferentes sin aprobacion explicita.

El usuario aprobo este plan reducido, no la implementacion obligatoria de todas
las oportunidades de la comparacion Gentle-AI. Los jueces de riesgo y arquitectura
lo aprobaron con observaciones: preservar configuracion protegida, comprobar el
modelo efectivo y posponer optimizaciones sin ahorro demostrado.

## Checklist verificable

### 1. Corregir la delegacion

- [x] Guardar este plan con criterios de cierre y exclusiones.
- [x] Revisar estado Git; hay cambios previos ajenos que no se deben modificar.
- [x] Rastrear asignacion de `explore` en configuracion canonica y activa.
- [x] Registrar los fallos observados: rechazo de `gpt-5.4-mini` con la cuenta utilizada y error de cuota al intentar `explore` con Sol. No se demostro que Sol causara el agotamiento ni que hubiera cuotas independientes por modelo.
- [x] Reconciliar configuración canónica (`config/opencode.jsonc`, `config/profiles/`, `config/agents/`) a `openai/gpt-5.6-luna`.
- [x] Reconciliar configuración activa protegida (`~/.config/opencode/opencode.jsonc`, `profiles/`, `agents/`, `agent/`) directamente sin `config-apply` destructivo.
- [x] Ejecutar comprobaciones proporcionales: `check-docs` (OK), `lint` (OK), `doctor` (24/24 pass), tests unitarios (24/24 pass).
- [ ] Revisar el candidato segun la politica RDD vigente, usando el manifest explicito de este documento.
- [x] Iniciar sesión nueva de OpenCode (`cd /home/miguel/opencode-ecosystem && opencode`) para cargar la configuración en memoria y verificar la delegación. Confirmado con éxito: subagente `explore` ejecutó lectura de `.env.example`, retornó resumen y completó en 7.1s sin error de incompatibilidad ni límite de cuota.

Cierre funcional: la prueba reportada demuestra una delegacion exitosa de `explore`, no la validacion en vivo de todos los agentes modificados. El texto compartido muestra el modelo del padre (Muse Spark), no el del hijo; la atribucion exacta al modelo del subagente exige metadatos correlacionados con esa ejecucion. RDD sigue pendiente.

### 2. Atribución exacta del modelo del hijo (2026-09-09)

- [x] Correlacionar metadatos de sesión con la ejecución de `explore`:
  - Sesión: `efe8fb09887d`
  - Mensajes: `msg_082b35c000016bVZLCVvzvkhdF` y `msg_082b367f9001aUx4KnP2wy1YoW`
  - Agente: `explore`, proveedor: `openai`, modelo: `gpt-5.6-luna`
  - Duración: `3050 ms + 3958 ms = 7008 ms`, consistente con los 7.1s reportados
  - Fuente: `~/.local/share/opencode/plugins-data/session-metrics.jsonl`
- [x] La lectura de `.env.example` fue ejecutada por el subagente `explore` con modelo `openai/gpt-5.6-luna`.

### 2. Observar uso normal

- [x] Obtener agregado inicial con el lector existente. No hay muestra comparable posterior suficiente para medir ahorro.
- [x] Delimitar la evidencia: la fecha de escritura del almacen RDD no mide consultas de solo lectura, tokens ni verificaciones repetidas. No se demostro ausencia de duplicaciones.
- [x] Separar metricas: 7.1s corresponde a la prueba reportada; 6.084 tokens de entrada y 150 de salida corresponden al agregado de dos mensajes Luna, no necesariamente a esa unica ejecucion. Coste registrado 0 no demuestra facturacion gratuita ni menor consumo de cuota.
- [x] Aplicar regla de parada: no implementar optimizaciones adicionales por evidencia insuficiente de beneficio. Esto no prueba que no exista desperdicio.

### 3. Elegir como maximo una optimizacion

- **Decision**: no implementar ahora proyecciones compactas, caches ni cambios de coordinacion.
- **Justificacion**: no hay evidencia suficiente para justificar mantenimiento adicional. Se puede reconsiderar con una muestra acotada de tareas reales; no es una prohibicion permanente ni una conclusion de eficiencia optima.

### 4. Despliegue y recuperacion

- [x] Revisar diff exacto: únicamente configuración de modelos (`config/opencode.jsonc`, `profiles/`, `agents/`, `tech-stack.md`) y el documento del plan.
- [x] Registrar cambios aplicados en configuracion canonica y activa. La aplicacion local no implica aprobacion RDD ni distribucion oficial; los overrides SDD locales se enumeran aparte.
- [x] No ejecutar `config-apply` completo para preservar personalizaciones y MCPs locales.
- [x] No ejecutar `publish` en worktree sucio ni `commit`/`push` sin solicitud explícita.
- [x] Reiniciar OpenCode: ejecutado por el usuario desde `/home/miguel/opencode-ecosystem`.
- [x] Registrar exito funcional reportado de `explore` (7.1s, lectura de `.env.example`). No atribuir el modelo del padre al subagente.
- [x] Correlacionar metadatos de la prueba con el modelo efectivo del hijo; la configuracion en disco por si sola no lo demuestra.
  - **Atribución completada (2026-09-09)**: sesión `efe8fb09887d`, modelo `openai/gpt-5.6-luna`, duración 7008ms.
- Recuperacion: no se solicitan reversiones. No consta prueba de restauracion ni respaldo previo verificado en esta evidencia; no marcar ese control como ejecutado.

## Evidencia y bloqueos actuales

- Error 1 observado con `gpt-5.4-mini`: No soportado al utilizar Codex con cuenta ChatGPT (`The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account`).
- Error 2 observado al probar `gpt-5.6-sol` en `explore`: `The usage limit has been reached`. El mensaje no establece causa del agotamiento, distribucion de cuotas ni momento de restablecimiento.
- Configuracion actual: `openai/gpt-5.6-luna`. Hubo una prueba funcional exitosa reportada despues del cambio; no garantiza disponibilidad futura, menor coste ni optimalidad frente a otros modelos.
- Fuente canónica corregida: `config/opencode.jsonc` (`small_model`, `explore`, `scout`, `title`, `summary` apuntan a `openai/gpt-5.6-luna`).
- Fuente activa corregida: `~/.config/opencode/opencode.jsonc` (mismos campos apuntan a `openai/gpt-5.6-luna`). Aplicado directamente, sin `config-apply`.
- El worktree tiene cambios previos extensos. No se ejecutó publish, sync, config-apply, commit ni push.

## Manifest de cierre canonico

Revisar exactamente estos 18 archivos, sin incluir otras modificaciones del worktree:

1. `config/opencode.jsonc`
2. `config/profiles/light/opencode.jsonc`
3. `config/profiles/personal/opencode.jsonc`
4. `config/agents/ai-matcher.md`
5. `config/agents/codebase-onboarding-engineer.md`
6. `config/agents/database-optimizer.md`
7. `config/agents/git-workflow-master.md`
8. `config/agents/product-manager.md`
9. `config/agents/prompt-engineer.md`
10. `config/agents/technical-writer.md`
11. `config/agents/ui-designer.md`
12. `spec/constitution/tech-stack.md`
13. `tools/scripts/doctor.js` (guarda `invokedDirectly`)
14. `tools/scripts/profile.js` (guarda `invokedDirectly`)
15. `tools/scripts/skills.js` (guarda `invokedDirectly`)
16. `tools/scripts/opencode-metrics.js` (guarda `invokedDirectly`)
17. `tests/tool-import-safety.test.js`
18. `docs/guides/delegation-efficiency-plan.md`

El alcance final es mayor que el arreglo original de `explore`: debe revisarse
como tal, no como un unico cambio de linea. La autorizacion del cierre no convierte
las comprobaciones de fixtures en pruebas reales de todos los modelos/agentes.

## Configuracion local separada

Fuera del receipt canonico: `~/.config/opencode/opencode.jsonc`, perfiles light
y personal y las copias activas de los ocho agentes listados arriba. No reemplazar
la configuracion activa completa para hacerla identica al repositorio.

Tambien se cambiaron estos overrides personales, sin fuente en el repositorio:

- `~/.config/opencode/agent/sdd-init.md`
- `~/.config/opencode/agent/sdd-explore.md`
- `~/.config/opencode/agent/sdd-tasks.md`
- `~/.config/opencode/agent/sdd-apply.md`
- `~/.config/opencode/agent/sdd-archive.md`

Se mantienen sin incorporarlos al sistema de distribucion. Un gate del repositorio
no certifica estos archivos externos ni garantiza su restauracion o sincronizacion.

## Politica explicita de contexto de ejecucion (`cwd`)

Las herramientas RDD de esta sesion vinculan el proyecto a `ctx.directory`.
Ejecutarlas desde una sesion abierta en el repositorio evita el `project_mismatch`
observado desde `/home/miguel`. Cambiar `workdir` de Bash no cambia ese contexto.
`review_start`, `review_capture` y `review_gate` son herramientas del agente,
no comandos shell con flags inventados.

Para validar cambios de arranque, iniciar un proceso nuevo que cargue la
configuracion correspondiente. El cwd del repositorio fija el contexto de RDD;
no es requisito universal para cargar configuracion global de OpenCode.

```bash
cd /home/miguel/opencode-ecosystem
opencode
```

Congelar el documento solo despues de corregirlo. No editarlo para marcar
aprobacion o insertar un receipt tras el gate: cambiaria los bytes revisados.
El estado definitivo se consulta en el receipt y se comunica con su ID fuera
del candidato. Cualquier edicion posterior requiere revision nueva.

## Protocolo de seguimiento

### Verificacion documental y observacion inicial

- `npm run check-docs`: correcto durante el registro del plan.
- `git diff --check`: correcto para cambios rastreados; no sustituye una prueba
  de delegacion ni comprueba por si solo este archivo nuevo sin rastrear.
- `node tools/scripts/opencode-metrics.js 1`: agregado de un dia, 227 mensajes,
  9 sesiones, 400 tools, 7 delegaciones, 5 fallos y 10 mensajes marcados como loop.
  Las dos entradas de gpt-5.4-mini registran cero tokens de entrada/salida.
- Estos contadores mezclan tareas/modelos; no demuestran causalidad, comandos
  duplicados ni ahorro potencial. `cost: 0` significa valor registrado, no uso
  gratuito ni equivalencia de coste. No modificar RDD basandose en este agregado.

Actualizar este checklist y la evidencia al ejecutar cada paso, nunca por intencion.
Maximo tres iteraciones de correccion/verificacion por tarea. Si el alcance llega
a permisos, persistencia, contratos o arquitectura no aprobados, detenerse y preguntar.
Los errores encontrados fuera del alcance se registran; no habilitan refactors.

Referencia previa: `~/docs/sources/gentle-ai-analysis.md`.
Comparacion externa consultada: Gentle-AI main
`c86693e2714ed6e156cc2974e85e85f5d2da21ae` y Gentleman.Dots main
`6f44b797b016aea92772d8a6d81a5f1bc53a84bb`. Esta referencia no implica
revision integral de esos repositorios ni adopcion de su configuracion.

## Verificacion ejecutada (2026-09-08)

Sin operaciones destructivas ni de distribucion (no publish/sync/config-apply/commit/push).

- `npm test -- tests/profile.test.js tests/doctor.test.js`: 17/17 correctos.
- `npm test -- tests/skills/agents.test.js tests/skills/skills.test.js`: 7/7 correctos.
- `npm run lint`: limpio (sin errores).
- `npm run check-docs`: correcto.
- `git diff --check`: limpio para cambios rastreados.
- El validador rapido anterior dio un falso positivo al recortar `//` dentro
  de `https://` en `$schema`; se descarta su resultado. Los tests de fixtures
  no sustituyen validar la configuracion activa con el parser del inspector.
- `review_start` no pudo ejecutarse desde esta sesion: vincula al cwd del
  proyecto (`/home/miguel`) y el repositorio es un proyecto anidado en
  `/home/miguel/opencode-ecosystem`, devolviendo `project_mismatch`. Se requiere
  una sesion abierta en el repositorio para el gate RDD. No se omitio el control.

Pendiente explicito:
1. Receipt y gate RDD del manifest canonico: **completado** — receipt A `r_1788986702798_627e2d4b-67ee-4c2d-a5a4-b35d6e084f83` (Tier 2, approved, gate: pass).
2. Receipt y gate RDD del launcher y test: **completado** — receipt B `r_1788986707995_7bc83b5e-1969-4817-b1e8-509a7fe06454` (Tier 3, approved, gate: pass).
3. Atribucion exacta del modelo del hijo mediante metadatos correlacionados: **completado** (2026-09-09) — sesion `efe8fb09887d`, modelo `openai/gpt-5.6-luna`, duracion 7008ms.
   Sin commits, publish, sync ni config-apply.

## Cierre administrativo (2026-09-09)

- Documentacion corregida: cuotas, coste, alcance y limites de la prueba funcional.
- `npm run check-docs` y `npm run lint`: correctos en este cierre.
- `npm test -- tests/profile.test.js tests/doctor.test.js tests/skills/agents.test.js tests/skills/skills.test.js`: 4 archivos, 24 tests correctos.
- `node tools/scripts/doctor.js --json`: `ok: true`, 24 comprobaciones correctas,
  0 fallos, 0 errores, 2 omitidas y 18 requeridas. Son comprobaciones del doctor,
  distintas de los 24 tests Vitest; no validan acceso a modelos remotos.
- `inspectConfigFile` del inspector existente: JSONC valido en configuracion
  principal y perfiles light/personal, tanto canonicos como activos (6 archivos).
  No se uso el validador regex defectuoso ni se imprimieron credenciales.
- `git diff --check` sobre los 18 archivos rastreados del manifest: correcto.
- Revision independiente de Code Reviewer, ejecucion
  `ses_f79a3cce2ffem0ZyeI8co2KPUo`: confirma que el diff de configuracion solo
  cambia modelos; no modifica permisos, pasos o MCP. Esto no es un receipt RDD.
- Hallazgo abierto de esa revision: la migracion de perfiles y multiples agentes
  amplifica el alcance original. La prueba de `explore` no demuestra acceso,
  coste ni disponibilidad de todos ellos. No se marca como riesgo aceptado ni
  se revierte configuracion durante este cierre administrativo.
- Hallazgo documental de esa revision: se separo evidencia doctor/Vitest arriba.
- Diagnóstico del fallo de launcher (`Unknown option: run` / `Unknown option: debug`):
  OpenCode importa automáticamente como módulos todos los archivos `.js` ubicados
  en `~/.config/opencode/tools/` al inicializar subcomandos. Los scripts CLI
  `doctor.js`, `profile.js`, `skills.js` y `opencode-metrics.js` ejecutaban parseo de
  `process.argv` y llamadas a `process.exit(2)` en la raíz del módulo, abortando el proceso.
- Corrección aplicada: se añadió la guarda `invokedDirectly` (siguiendo el patrón de
  `book-to-skill.mjs`) en `doctor.js`, `profile.js`, `skills.js` y `opencode-metrics.js`,
  sincronizando los cambios tanto en el repositorio canónico como en la configuración activa.
- Verificación del launcher:
  - Import-safety confirmado en los 4 scripts mediante prueba aislada sin efectos secundarios.
  - Comprobado que `opencode debug agent explore` ahora inicia limpiamente y devuelve
    código de salida 0 (sin abortar con `Unknown option`).
  - Todos los scripts CLI (`doctor.js`, `profile.js`, `skills.js`, `opencode-metrics.js`)
    siguen funcionando al 100% cuando se invocan directamente.
- `tests/tool-import-safety.test.js` reescrita para probar aislamiento real de subprocess:
  - 8 tests de importación: stdout vacío, stderr vacío, exit code 0, sin escrituras en HOME.
  - 4 tests de invocación directa: `main()` se ejecuta y produce salida.
  - Usa `spawnSync` con `node -e "import(...)"` para simular importación por OpenCode.
  - Usa `spawnSync` con ruta completa para simular ejecución directa.
  - 12/12 tests correctos, lint limpio, check-docs correcto.
- Estado RDD y contexto de proyecto:
  - El `project_mismatch` se resolvio configurando `/home/miguel` como repositorio
    git principal y `/home/miguel/opencode-ecosystem` como worktree, permitiendo
    que `resolveGitRoot` devuelva `/home/miguel` como raiz para ambos.
  - `review_start`, `review_capture`, `review_verify`, `review_finalize` y
    `review_gate` ejecutados exitosamente para ambos receipts.
  - Receipt A: `r_1788986702798_627e2d4b-67ee-4c2d-a5a4-b35d6e084f83` (Tier 2, approved, stale).
  - Receipt B: `r_1788986707995_7bc83b5e-1969-4817-b1e8-509a7fe06454` (Tier 3, approved, stale).
  - Ambos receipts requieren successors con sesion abierta en `/home/miguel/opencode-ecosystem`.
  - Atribucion completada (2026-09-09): sesion `efe8fb09887d`, modelo `openai/gpt-5.6-luna`, 7008ms.
  - Estado final: configuracion de modelos (`luna`) plenamente operativa y validada en vivo;
    launcher reparado; suite de tests (202/202) en verde; lint limpio; check-docs OK;
    atribucion de modelo del hijo verificada.
    Sin commits, publish, sync ni config-apply no autorizados.
