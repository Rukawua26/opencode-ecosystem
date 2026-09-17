# 011-routing-proporcional-rdd — Plan

## Enfoques considerados

### A. Pin solo en worker + ciclo RDD suave (ELEGIDO)
- `sdd-implement`: `model: openai/gpt-5.6-luna` + `variant: low` en opencode.jsonc.
- `sdd-verify`: sin pin (hereda sesión).
- `/implement-spec`: verifica UNA vez al cerrar el lote, máx. 1 corrección acotada.
- Coste: 2 claves config + micro-edit comando. Riesgo: mínimo (reversible por git+sync).
- Fidelidad: exacta al upstream (`Model Assignments`: sin modelo explícito → default; una
  corrección acotada, sin loop-until-clean).

### B. Pin en ambos + revisión por tarea
- Verificador fijo a modelo caro + audit tras cada tarea.
- Rechazado: pierde control de coste (verificador debe seguir el frontier del humano) y
  consume más tokens que el upstream actual (que revisa por lote, no por tarea).

### C. Perfiles JSON + skill review-and-verify + Playwright
- Rechazado: copiar config = drift contra el que ya nos protege sync/status; skill duplicaría
  sdd-verify+lenses; Playwright gasta RAM que no tenemos (8 GB). YAGNI.

## Elección mínima
A, porque es la única que cierra los 2 gaps reales (routing por rol y ciclo RDD) sin añadir
estado, skills duplicadas ni dependencias nuevas. Todo aditivo y reversible.

## Impacto
- `configs/opencode.jsonc`: +2 claves en `agent.sdd-implement`.
- `commands/implement-spec.md`: micro-edit del paso 3 (ciclo con verificación única).
- Docs: evolution + gentle-ai-analysis (sección video-2).
- Token de arranque: +0 (el pin es metadata de config; el comando solo edita texto breve).
