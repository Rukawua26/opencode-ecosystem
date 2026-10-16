---
name: security-lens
description: 4R Security lens. Usar cuando el diff toque entradas, autenticacion, permisos, red, secretos o almacenamiento, para revisar inyeccion, control de acceso y fuga de credenciales; NO usar en diffs de solo docs o config sin esos elementos.
---

# security-lens
Lens persuasivo: informa, nunca bloquea. Complementa `qa-gate` (patrones fijos de secretos y riesgos) y no es una auditoria completa ni SAST.

1. Carga rutas seguras con `mapfile -d '' -t files < <(git diff --cached --name-only -z --diff-filter=ACMR)`; si queda vacio, repite con `git diff --name-only -z --diff-filter=ACMR`. Si sigue vacio, responde `Sin hallazgos.` sin ejecutar `rg`.
2. Ejecuta `bash ~/.config/opencode/scripts/qa-gate.sh --strict` y resume su salida; no repitas a mano sus patrones de secretos.
3. Un unico barrido sobre `"${files[@]}"`:
   - `rg -n 'eval\(|exec\(|pickle\.loads|yaml\.load\(|innerHTML|dangerouslySetInnerHTML|verify\s*=\s*False|allow_origins.*\*|Access-Control-Allow-Origin.*\*' --no-heading -g '!*.bak-*' -- "${files[@]}"` — ejecucion, deserializacion, HTML sin escapar, TLS o CORS abiertos
   - `rg -n 'execute\(f|SELECT .*\+|WHERE .*\+|os\.path\.join\(.*request' --no-heading -g '!*.bak-*' -- "${files[@]}"` — SQL o rutas construidas con datos externos
4. Revisa solo lo que el barrido señala y las acciones sensibles del diff: cada accion que cambia datos o permisos debe validar identidad y propietario; las entradas deben validarse antes de llegar a consultas, rutas, comandos o HTML; ningun secreto o token debe llegar al cliente, a logs o a la salida.
5. Puerta de precision: reporta solo defectos reales con evidencia (`path:linea` + por que es explotable o por que importa). Ante la duda, silencio; prohibidos los hallazgos de estilo.
6. No corrige ni bloquea. No leas ni imprimas secretos reales para demostrar un fallo: describe la ruta. Si no hay nada, responde exactamente: `Sin hallazgos.`
