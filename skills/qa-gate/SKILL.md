---
name: qa-gate
description: Pre-commit, staged diff y anti-slop con secretos. Usar para detectar catch vacios, logs de depuracion, TODO o FIXME, posibles API keys y ficheros .env/.pem/.key rastreados antes de un commit.
---

# qa-gate
Ejecuta `bash ~/.config/opencode/scripts/qa-gate.sh` para revisar el staged diff.
El modo normal solo avisa. `--strict` bloquea un `catch {}` vacio, un posible secreto (AKIA/sk-/ghp_/clave PEM/URL con credenciales) o un fichero sensible rastreado (.env, .pem, .key, id_rsa); los logs de depuracion y TODO/FIXME siguen siendo avisos. Nunca imprime valores de secretos, solo el tipo de patron.
