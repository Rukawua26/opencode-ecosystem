# Plantilla de instruccion perfecta

> Usar al pedir cualquier tarea no trivial al agente. Si un campo no aplica,
> escribir `N/A` en vez de dejarlo vacio. Referencia: Dia 1 MoureDev,
> de la idea a la instruccion perfecta; patron trigger-rules de `~/AGENTS.md`.

## 1. Contexto

Donde estamos, que repo/ficheros tocan, que se probo ya, enlaces o rutas.

## 2. Rol

Que papel toma el agente (implementador, verificador, explorador) y con que
autorizacion (read-only, editar codigo, ejecutar verificacion local).

## 3. Tarea

Una sola tarea atomica, en una frase, con verbo concreto.

## 4. Restricciones

Lo que NO debe hacer: stack permitido, limites duros (no migrar esquema,
no commit/push/PR, no procesos pesados), YAGNI.

## 5. Ejemplo

Un ejemplo minimo de entrada/salida esperada o de patron a imitar.

## 6. Formato de salida

Que debe entregar exactamente (ficheros, resumen acotado, comandos
ejecutados con resultado). Nunca stdout completo de agentes.

## 7. Criterios de aceptacion

Como se verifica que esta bien: tests, `status sin drift`, `verify.sh`,
`qa-gate --strict`, o comprobacion concreta.

---

## Ejemplo lleno (cambio pequeño)

- Contexto: `opencode-ecosystem/scripts/ram-guard-lite.sh:7` escribe ruido
  en `observations.log`.
- Rol: implementador con autorizacion de editar codigo y verificar local.
- Tarea: redirigir ese `echo` a `ram-guard.log` propio.
- Restricciones: bash existente, sin dependencias, sin cambiar la logica
  de `pkill`, sin tocar `configs/cron-jobs.json`.
- Ejemplo: `echo "..." >> "$HOME/.config/opencode/memory/ram-guard.log"`.
- Formato: diff del fichero + `bash -n` ok.
- Aceptacion: `bash -n` pasa, `status sin drift` tras sync, el log de
  observaciones deja de recibir lineas `ram-guard`.
