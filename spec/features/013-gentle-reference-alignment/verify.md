# Verify 013

## AC1 — Baselines actualizados: PASS
`gentle-ai-analysis.md`: main `1863432`, beta `420555a` (sin cambios), verificado
con `git ls-remote` 2026-08-31. `comparison.md`, `_MOC.md`, `Sources.md` alineados.

## AC2 — Doctor con bloque plugins: PASS
`doctor.js` incluye `plugins.{configured, discoveredActive, disabled,
undeclaredActive}` listando archivos sin cargarlos. Tests nuevos en
`tests/doctor.test.js` (11/11). Read-only confirmado por los tests de snapshot
existentes sin modificacion.

Beneficio real detectado al activarlo: el manifest quedaba con 5 entradas
obsoletas tras el traslado a `plugins.disabled/` (doctor fallaba); detectado y
reparado con `install.sh --sync --skip-memory` (doctor ok=true, 107/107).

## AC3 — E2E minimo: DECISION: NO construir todavia
Cobertura actual: `install.test.sh` instala el stack completo en HOME temporal
e importa el plugin RDD con el Node real; CI lo repite en Linux/macOS/Windows;
hooks, router y memoria tienen suites propias. La unica brecha (ejecutar el
binario `opencode` con proveedor simulado) no justifica el coste en un stack
sin quebrantos reproducidos. Se documenta como backlog vigilado.

## AC4 — Medicion backups: PASS (no optimizar)
- checkpoints: 8.6 MB, 552 ficheros, solo 38 hashes duplicados~ (~0,6 MB
  recuperables con dedup): compresion/dedup NO justificada (YAGNI confirmado).
- 2 backups manuales grandes (63/83 MB) son historicos de incidentes, fuera de
  la retencion automatica; no aplica.
- Decision: mantener keep-N actual; retroalimentar solo si crecen 10x.

## AC5 — Suites y CI
Local: vitest (con nuevos tests doctor), suites router/memory/RDD, install,
hooks, shellcheck, lint, check-docs. CI y CodeQL tras push.
