---
name: qa-gate
description: Pre-commit, staged diff y anti-slop con secretos. Usar para detectar catch vacios, logs de depuracion, TODO o FIXME, API keys, ficheros sensibles y senales de riesgo en lineas anadidas antes de un commit.
---

# qa-gate
Ejecuta `bash ~/.config/opencode/scripts/qa-gate.sh [--strict]` desde el repo a revisar (omite los corchetes). Git usa el repo del cwd, su indice canonico y rutas rastreadas desde la raiz; ignora todo GIT_* heredado. Sin staged informa no aplicable, pero comprueba rutas sensibles rastreadas; no audita codigo unstaged.

Warn devuelve 0 por hallazgos; strict devuelve 1 por `catch` vacio, posible secreto (AKIA/sk-/ghp_/PEM/URL con credenciales) o fichero sensible rastreado (.env, .pem, .key, id_rsa). Logs, TODO/FIXME y riesgos son avisos. Error operativo, argumentos invalidos o analisis incompleto devuelven 2 en ambos modos; nunca equivalen a aprobacion.

El catalogo textual revisa lineas anadidas; los riesgos (`subprocess shell=True`, `os.system`, `eval`, `yaml.load`, TLS/JWT sin verificacion, `chmod 777`) excluyen tests y comentarios, no asi los secretos. Un diff binario, no soportado o incompleto falla con 2 incluso en warn; archivos vacios validos SHA-1/SHA-256 son aceptados. No es SAST/SCA ni congela un candidato.

Publica ruta escapada/redactada, linea y etiqueta fija, nunca fragmentos fuente ni errores Git crudos. Muestra hasta 50 hallazgos, pero cuenta y evalua todos, incluidos bloqueantes tardios. Git: 15 s por consulta; transporte temporal descartado y limite de lectura de 16 MiB por salida, NO limite duro de disco/RAM.

En este ecosistema, `./verify.sh` es el cierre local unico: tests sobre working tree y QA strict sobre indice+rutas rastreadas, siempre, aun sin staged. Su verde exige todos los controles obligatorios completos; consulta README y docs/evolution/2026-10-03-cierre-fiable.md para limites y evidencia pendiente.
