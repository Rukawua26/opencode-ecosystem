# 010-review-effort-por-riesgo — Spec

## Problema
Las 4 lentes 4R (009) pueden dispararse todas en cualquier review, gastando
tokens sin necesidad. gentle-ai escala el esfuerzo de revisión por riesgo
evidenciado (bajo = 0 lenses, medio = 1 con consent, alto = 4R con consent +
coste). Nosotros no teníamos esa política.

## Solución aprobada (híbrida, no tabla en AGENTS.md)
1. Triggers negativos en la `description` de cada lente (~10 tok c/u): la
   decisión vive donde OpenCode la toma (el trigger).
2. Extender la línea 4R existente en `~/AGENTS.md` con la regla de escala:
   esfuerzo por evidencia del diff, no por tamaño; riesgo bajo = solo qa-gate;
   4R completo requiere consentimiento con aviso de coste.

## Fuera de alcance
Skill router, codigo ejecutable de clasificacion, protocolo RDD formal
(freeze/ack/receipts), plugins TUI, Engram, GGA, telemetria.

## Criterios de aceptación
1. 4 descriptions actualizadas y válidas por `validate-skills.py`.
2. `sync --apply` OK, `status sin drift`, `verify.sh` verde.
3. `opencode debug skill` carga las 9 propias.
4. AGENTS.md refleja la regla de escala sin sección nueva (solo extensión de
   la línea 4R); +~80 tokens fijos totales.
