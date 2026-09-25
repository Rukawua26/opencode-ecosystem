---
name: qa-gate
description: Pre-commit, staged diff y anti-slop con secretos. Usar para detectar catch vacios, logs de depuracion, TODO o FIXME, API keys, ficheros sensibles y senales de riesgo en lineas anadidas antes de un commit.
---

# qa-gate
Ejecuta `bash ~/.config/opencode/scripts/qa-gate.sh` para revisar el staged diff.
El modo normal solo avisa. `--strict` bloquea un bloque `catch` vacio, un posible secreto (AKIA/sk-/ghp_/clave PEM/URL con credenciales) o un fichero sensible rastreado (.env, .pem, .key, id_rsa); los logs de depuracion, TODO/FIXME y las senales de riesgo son avisos. Revisa solo lineas anadidas de produccion para patrones como `subprocess ... shell=True`, `eval`, `yaml.load`, TLS desactivada, JWT sin verificacion o `chmod 777`. Nunca imprime valores de secretos, solo path:linea y tipo de patron.
