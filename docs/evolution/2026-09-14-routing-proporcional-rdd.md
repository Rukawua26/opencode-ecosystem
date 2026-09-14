---
nombre: 2026-09-14-routing-proporcional-rdd
fecha: 2026-09-14
estado: en_observacion # propuesto | aplicado | en_observacion | verificado | revertido
afecta: [configs, commands, docs] # skills | configs | scripts | memoria | git | reglas | docs
fuente: gentle-ai # propio | gentle-ai | noffolo | otro-repo (video 2 + baseline `266574b0`)
---

# Routing proporcional por rol + ciclo RDD proporcional

## Por que
El video 2 de Gentleman Programming (routing/perfiles/RDD) propose revisar cada tarea y
perfiles JSON; contrastado con el repo actual `266574b0`, su mecanismo real es otro:
Model Assignments por fase (sin modelo explicito -> default del runtime), revision
independiente por lote (no por tarea) y maximo una correccion acotada, sin
loop-until-clean. Evidencia: `sdd-orchestrator.md` (secciones Model Assignments y Native
Checking Contract), `sdd-apply.md`/`sdd-verify.md`. Gap real nuestro: los 2 subagentes
heredaban el modelo de sesion sin routing por rol, y el ciclo implementar->verificar no
estaba cableado en el comando.

## Antes
- `sdd-implement` y `sdd-verify` sin claves model/variant: heredaban la sesion completa.
- `/implement-spec` marcaba `[x]` tras el reporte del implementador, sin verificacion
  independiente antes de cerrar la tarea.

## Despues
- `sdd-implement`: `model: openai/gpt-5.6-luna` + `variant: low` (disponibles; ~10x mas
  barato que sol; tareas atomicas con criterio de verificacion).
- `sdd-verify`: SIN pin (hereda la sesion; el auditor sigue el frontier del humano).
- `/implement-spec`: tras exito de sdd-implement, invoca sdd-verify UNA vez antes de pedir
  aprobacion; maximo UNA correccion acotada; segundo rechazo = STOP y decision humana.

## Beneficio
- Tokens: el worker atomico corre en luna low; el verificador conserva calidad frontier
  sin coste sorpresa.
- Ciclo RDD real: implementa -> verifica (contexto fresco) -> humano marca, con tope de
  correcciones (fiel al upstream, no revision por tarea).
- Cero estado nuevo: sin perfiles JSON; el runbook cascada y /models siguen siendo la
  via de cambio de modelo.

## No regresion
- Todo aditivo: 2 claves de config y un micro-edit de comando.
- `sdd-verify` sin pin: si el runtime no soporta variant, es metadata inerte.
- El flujo sin comandos (routing manual) queda intacto.
- Modelos locales 14B/32B del video rechazados (8 GB); Playwright y skill review-and-verify
  fuera de alcance (duplicarian sdd-verify + lenses).

## Verificacion
- Prueba dogfood feature 011 (2026-09-14): T1 y T2 delegadas a `sdd-implement` (contrato
  de resultado devuelto; el gate detecto un task_result vacio en el intento 1 de T2 y el
  reintento 2 paso). JSON parse ok; comando con ciclo y tope de 1 correccion.
- validate-skills + sync + status + verify.sh + verificacion independiente de `sdd-verify`
  al cerrar el lote: ver `verify.md` de la feature.
- Base reversible: commit previo en Git (estado sin pin y comando sin ciclo).
- Reinicio requerido para que el pin de modelo surta efecto en el runtime.

## Periodo prudencial
- Vigilancia hasta 2026-09-28 (mismo ciclo que las features 010 y paridad gentle-ai).
- Senal de estabilidad: al menos una feature real con luna low en sdd-implement sin
  degradacion de calidad visible y sin rechazos dobles del verificador.
- Senal de revertir: luna low produce fixes defectuosos recurrentes (se lo atribuye el
  gate), o el verificador hereda un modelo free y pierde precision; rollback por git + sync.
- Hallazgo menor anotado: `spec/constitution/` referenciada en AGENTS.md no existe.
  RESUELTO (2026-09-14) con lectura condicional: AGENTS.md linea 12 ahora lee
  `working-agreement.md` y `tech-stack.md` solo si existen; siempre lee
  `spec.md`/`plan.md`/`tasks.md`. Texto anterior (rollback manual):
  "Antes de implementar una feature SDD, leer solo la constitucion minima y la feature
  solicitada: `spec/constitution/working-agreement.md`, `spec/constitution/tech-stack.md`,
  `spec/features/<feature>/spec.md`, `plan.md` y `tasks.md`."

## Fuente
- Video 2 Gentleman Programming (routing, perfiles, RDD) contrastado con repo `266574b0`.
- Seccion video-2 con TOMAMOS/DEJAMOS: `~/docs/sources/gentle-ai-analysis.md`.
- DEJADO: perfiles JSON (drift), modelos 14B/32B (8 GB), pin de sdd-verify (coste),
  skill review-and-verify (duplicacion), Playwright (RAM), skill-harvester (regla linea 25).
