# 011-routing-proporcional-rdd — Spec

## Objetivos
Cerrar los 2 gaps reales del video 2 (orquestación/perfiles/RDD) con paridad proporcional
a gentle-ai `266574b0`, filtrado por i5-1235U, 8 GB RAM, ahorro de tokens y YAGNI.

## Alcance (TOMAMOS)
1. **Routing proporcional por rol** (patrón `Model Assignments` upstream, escala 1/2):
   - `sdd-implement` pinneado a `openai/gpt-5.6-luna` con variante `low` (disponibles, ~10×
     más barato que sol; tareas atómicas con criterio de verificación).
   - `sdd-verify` SIN pin: hereda el modelo de sesión (contrato upstream: sin modelo explícito
     se usa el default del runtime; el auditor sigue el frontier elegido por el humano).
2. **RDD proporcional** (fiel al upstream actual, NO revisión por tarea):
   - `/implement-spec`: tras `sdd-implement` con status éxito, invocar `sdd-verify` UNA vez
     antes de pedir aprobación para marcar `[x]` en tasks.md.
   - Máximo UNA corrección acotada por rechazo; segundo rechazo = STOP y decisión humana.
   - No hay loop-until-clean.
3. **Documentación**: doc de evolución + sección video-2 en `gentle-ai-analysis.md`.

## Fuera de alcance (DEJAMOS, con por qué)
- `profiles/active.json` y JSONs de perfil: copiar config = drift; cubierto por `/models`
  + runbook cascada + `small_model` free.
- Modelos locales 14B/32B del video (qwen2.5-coder, deepseek-r1): no caben en 8 GB.
- Pin permanente de `sdd-verify` a modelo caro: pierde control de coste.
- Skill `review-and-verify` con reglas Java/Spring: duplicaría `sdd-verify` + lenses 4R.
- Playwright/screenshots: sin frontends web en alcance; RAM que no tenemos.
- skill-harvester: regla de repetición (AGENTS.md línea 25) ya lo cubre con consentimiento.

## Criterios de aceptación
- `opencode.jsonc` JSON válido con `sdd-implement` con `model` + `variant` luna/low.
- `sdd-verify` sin claves `model`/`variant` nuevas.
- `/implement-spec` incluye el ciclo implementa→verifica→aprobar con tope de 1 corrección.
- `opencode debug agent sdd-implement` (tras reinicio) muestra luna + low.
- `validate-skills` 9/9, `sync --apply` sin drift, `verify.sh` verde, commit git.
- `verify.md` registrado con resultado de la verificación independiente.

## Contexto y decisiones
- Fuente: video 2 Gentleman Programming (routing/perfiles/RDD) contrastado con repo
  `266574b0`: `sdd-orchestrator.md` (Model Assignments, no loop-until-clean, una corrección
  acotada), `sdd-overlay-single.json`, `sdd-apply.md`/`sdd-verify.md`.
- Preflight (2026-09-14): modo Interactivo; verificación independiente al cerrar lote.
- Anotación: `spec/constitution/` referenciada en AGENTS.md no existe (hallazgo menor;
  corregir en feature futura o ajustar AGENTS.md).
