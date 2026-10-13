---
nombre: 2026-10-12-panel-verdad-declarado
fecha: 2026-10-12
estado: en_observacion
afecta: [scripts, docs, reglas]
fuente: propio
---

# Panel: verdad declarado y alcance de salud

## Por que
`./verify.sh` estaba rojo solo por `plugin doctor` (OpenCode autoactualizado a
`v2.0.27` frente al pin `v2.0.26`). Al diagnosticar aparecieron tres
afirmaciones del plano de control que excedian lo que realmente observa:

- El flujo declarado `qa-gate` describia `restore -> qa-gate -> pre-commit`.
  **No existe hook pre-commit**: `git config core.hooksPath` vacio y
  `.git/hooks/pre-commit` ausente.
- `verify.sh`, que es el cierre real, no aparecia en ningun flujo declarado ni
  como componente observado.
- El panel pintaba `health.ok` con la etiqueta `sano`, pero `Health.ok` solo
  comprueba servicio OpenCode activo + timers activos + `errors == []`
  (`collect.py`). No ejecuta `verify.sh` ni la suite: podia mostrar `sano` con
  el cierre rojo.

## Antes
- 3 flujos declarados; el de calidad prometia un hook inexistente.
- `counts`: scripts 4, flujos 3, componentes 24. `verify.sh` invisible.
- Etiqueta de salud `sano` / `revisar` sin indicar su alcance.

## Despues
- Flujo `qa-gate` conservado por id (cambiarlo romperia consumidores) y
  corregido: `qa-gate --strict` sobre staged + rutas rastreadas, ejecutado
  siempre por el cierre, con ram-guard y kairos **como timers, no hooks**.
- Nuevo flujo declarado `cierre` que nombra `./verify.sh` y sus checks reales.
- `_collect_root_entrypoints` observa `verify.sh` con `kind=script`,
  `source=observado`. **No** se toco el glob de `_collect_scripts`: `verify.sh`
  esta en la raiz, no en `scripts/`. Robusta si el fichero no existe.
- `sources` del snapshot declara `verify.sh` como origen observado.
- La etiqueta de salud pasa a `runtime sano` / `runtime: revisar`, con
  `title` y `aria-label` que aclaran que **no** incluyen `verify.sh` ni los tests.
- `control/README.md` lista el flujo `cierre` y anade una linea de alcance.
- `health.ok` **no cambia de semantica**: sigue siendo servicio + timers + errors.
- Pin de OpenCode actualizado a `v2.0.27` tras revision previa.

## Beneficio
- El panel deja de afirmar mas de lo que observa: tres falsedades retiradas.
- `verify.sh` es observable, asi que el mapa operativo incluye el cierre.
- La etiqueta `runtime sano` ya no puede leerse como "el sistema esta bien".
- Medido: suite completa 245 tests OK (1 skip opt-in), 26.642 s. Snapshot
  observado: `counts={skills:13, scripts:5, agentes:2, timers:3, flujos:4,
  componentes:25}`.

## No regresion
- `health.ok` mantiene exactamente su semantica anterior; no se guarda exit code
  de `verify.sh` en ningun sitio y el panel no ejecuta la suite.
- El id del flujo `qa-gate` se conserva; no se renombro nada.
- `counts` y la forma del `Snapshot` no cambian; sin kind nuevo.
- El glob de `_collect_scripts` sigue siendo `scripts/*.sh`.
- Test de regresion verificado empiricamente como no tautologico: contra
  `collect.py` viejo fallan 3 assertions y 3 dan error; contra el HTML viejo
  fallan los dos tests de la etiqueta de salud.
- Base reversible en Git: los originales de `control/collect.py`,
  `control/web/index.html`, `control/README.md` estan en `8469039`.

## Verificacion
- `python3 -m unittest discover -s control/tests`: passed, 245 tests
  (1 skipped), 26.642 s, exit 0.
- `./verify.sh`: passed, `[ok] verify verde`. Hygiene solo aviso informativo rc=1.
- `./scripts/qa-gate.sh --strict`: passed, exit 0; staged no aplicable.
- `python3 validate-skills.py skills`: `[ok] 13 skills valid`.
- `./opencode-ecosystem status`: `[ok] sin drift`.
- `bash ~/tools/plugin_doctor.sh`: passed, exit 0, pin `v2.0.27` = runtime.
- Verificacion independiente read-only de T1 en contexto fresco: passed.
  Dos hallazgos `low` de mantenibilidad detectados y corregidos por el padre
  (lista `sources` sin `verify.sh`; asercion `title|aria-label` anclada a una
  ventana de 200 chars que incluía markup vecino).

## Hallazgo lateral (FUERA de alcance, no corregido)
`~/tools/plugin_doctor.sh` solo inspecciona `$PLUGINS_DIR/*.js`. Existe un
plugin real `~/.config/opencode/plugins/uso/tui.tsx` (455 lineas, TUI, consumo
por modelo en el pie del prompt) que **el doctor no puede ver**: reporta
"hooks en uso:" vacio y "todos los hooks encontrados en el binario" de forma
vacuamente cierta.

Antes de re-pinear se reviso su superficie de API contra el binario `v2.0.27`:
`session.execution.succeeded`, `session.execution.failed`, `session.stats`,
`prompt.footer.status` y `@opencode/plugin/tui` estan **presentes**. Por eso el
bump se acepto. Advertencia honesta: presencia de cadenas no equivale a
verificacion funcional del renderizado.

El plugin no esta versionado en este repo ni figura en el manifiesto de ficheros
gestionados: es una personalizacion del runtime. **No se toco, no se sincronizo
y no se propone Incorporarlo.** Corregir el glob de `plugin_doctor.sh` requiere
autorizacion aparte: vive en `~/tools`, fuera de `opencode-ecosystem`.

## Periodo prudencial
- Minimo 7 dias desde 2026-10-12 y varios ciclos de uso normal del panel.
- Estable si el mapa sigue cuadrando con lo observado, la etiqueta no vuelve a
  sugerir salud global, y no hay falsos verdes por diferencia observado/declarado.
- Rollback: `git revert` por commit; nada es stateful. El pin se revierte
  volviendo a `v2.0.26`. No afecta a memoria viva, receipts ni backups.

## Fuente
Implementacion propia reutilizando `_build_flows`, `_collect_scripts`,
`Component`, `ComponentKind.SCRIPT` y `Source`. Sin dependencias nuevas, sin
schema nuevo, sin daemon, sin migracion SQLite. Contraste de dos jueces
independientes: ambos marcaron como YAGNI anadir categoria de pin desfasado a
`verify.sh` y como sobreingenieria convertir `docs/` y `odd/tasks/` en
componentes.