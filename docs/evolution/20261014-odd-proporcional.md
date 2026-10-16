---
nombre: 20261014-odd-proporcional
fecha: 2026-10-14
estado: en_observacion
afecta: [skills, configs, reglas, docs]
fuente: propio
---

# ODD proporcional

## Por que
El orquestador pagaba delegacion por existir documento o superar conteos,
y el verifier rechazaba inline aunque su riesgo requiriese revision independiente.
La contradiccion estaba en AGENTS, punto 7 de la skill y prompt verifier.

## Antes
Documento sustancial implicaba worker; conteos de archivos, writes, lecturas y
capas imponian routing. El cierre de la skill hablaba de riesgo sin reconciliarlo.

## Despues
Documento recuperable, delegacion util y revision por riesgo son decisiones
separadas. Inline conserva aprobacion y checks; alto riesgo exige independiente.
Control-plane conserva siempre worker->verifier, contratos y gates existentes.

## Beneficio
Esperado: menos delegacion innecesaria, sin reducir seguridad ni evidencia.
No se han medido tokens, RAM ni ahorro real.

## No regresion
- Baseline HOME limpio de AGENTS: `ba62b2f1c3911630f8f7262b5cca07d964ab22f7`.
- Baseline fuente: `8bc6069231768db00841dd679655bd168695b5f7`.
  Skill original versionada; prompt original igual a HEAD. README/control README
  ya tenian cambios ajenos: se conservan y solo se edita la seccion ODD.
- Config ya tenia retirada de `compaction.prune`: se conserva como trabajo previo.
  Semantica completa salvo system verifier SHA-256 antes/despues:
  `292cbdaead066546e6b0f3fc1d8ec88c5e6f57f6453bc91886a2d2a0d977469a`.
- Sin cambios runner, permisos, modelos, DB ni contratos SUMMARY/RESULT;
  continuaciones del modelo nunca a shell. Sin helpers ni tests de frases.
- `docs/zap-mcp.md` conservado, SHA-256
  `fc780bf8b6778745c61f40c74c9c1b6bb88d4554f3208b07d2c63f2d6cd5eda4`.
- HOME/AGENTS se edita en su repo versionado, no se anade al manifiesto.

## Verificacion
Evidencia detallada en `odd/tasks/odd-proporcional.md`. Antes de editar:
`./opencode-ecosystem status` termino `[ok] sin drift`.
Auditoria previa al sync: solo prompt verifier y skill divergen en gestionados;
scripts, commands, dcp y cron iguales. Sync oficial autorizado conserva
personalizaciones; no se editan memoria viva, backups, receipts ni logs a mano.
Intento `sync --apply`: rc=1 antes de copiar, por enlaces personales existentes
en `~/.config/opencode/node_modules/.bin/` rechazados por `safe_tree`.
No se sortea ni cambia la guarda. Fuentes implementadas; runtime pendiente.
Suite completa: 340 tests OK, 1 E2E opt-in omitido; validate-skills 13 valid;
qa strict rc=0 sin staged. `verify.sh` rc=1 exclusivamente por drift pendiente.
Por ello no se declara cierre verde ni no regresion operativa observada.
Ampliacion posterior autorizada: guarda de sync limitada a arbol skills y
rutas concretas copiadas/escritas (config, scripts fuente, comandos fuente,
scripts de memoria gestionados y manifiesto). No recorre raiz runtime,
node_modules, memoria viva ni scripts/comandos personales. Conserva rechazo
de enlaces en rutas gestionadas y sus antecesores. No se cambia publish.
Sync omite copias/backups de config/comandos/scripts de memoria identicos;
chmod se aplica solo a scripts presentes en fuente, no al glob del destino.
No crea topics de memoria como efecto colateral. Sin helpers ni dependencias.
Test existente ampliado: enlace personal node_modules y scripts, contenido y
modo del script personal intactos; stub find falla si se recorre raiz runtime.
RED observado (rc=1); GREEN 19 tests de mutaciones (rc=0). Se mantienen tests
de rechazo de enlaces gestionados, fallos de copia/backups y memoria viva.
Resultado final tras ampliacion: validate-skills 13 valid; sync oficial rc=0,
solo backup config anunciado; status `[ok] sin drift`. Runtime skill y prompt
identicos a fuente; resto de semantica config/modelos/permisos mantiene hash.
Suite 340 tests OK (1 E2E opt-in omitido); verify verde rc=0; qa strict rc=0
sin staged (no certifica unstaged). Hygiene trigger informativo no bloqueante.
La primera suite completa detecto fixture que suponia topics creado por sync;
se corrigio preparando carpeta personal en el test y exigiendo que sync no la
siembre. No se oculta ese fallo intermedio ni el bloqueo inicial ya resuelto.
Base reversible adicional: `20261014-odd-proporcional.before.md` conserva solo
cmd_sync previo (con trabajo ajeno no commiteado); no restaurar archivo entero
desde HEAD. T1 completa, T2 independiente y observacion real pendientes.

## Periodo prudencial
- Pendiente observacion de sesiones reales: comprobar los cuatro escenarios
  del documento ODD en uso normal antes de declarar estable.
- Baselines permanecen recuperables en Git; no se borran.
- Revertir si reaparecen gates omitidos, delegacion por conteo o revision de
  alto riesgo omitida. Restaurar solo los hunks ODD propios desde los baselines
  (no descartar cambios ajenos) y sincronizar por el comando oficial autorizado.

## Fuente (si aplica)
Propio; reutiliza documento ODD, agentes existentes y tests del runner.
