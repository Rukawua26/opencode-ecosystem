---
name: qa-gate
description: Pre-commit, staged diff y anti-slop. Usar para detectar catch vacios, logs de depuracion y TODO o FIXME antes de un commit.
---

# qa-gate
Ejecuta `bash ~/.config/opencode/scripts/qa-gate.sh` para revisar el staged diff.
El modo normal solo avisa. `--strict` bloquea un `catch {}` vacio; los logs de depuracion y TODO/FIXME siguen siendo avisos.
