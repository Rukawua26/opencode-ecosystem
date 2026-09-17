# 010-review-effort-por-riesgo — verify.md (2026-09-11)

## Evidencia
1. **Validador**: 9 skills válidas tras editar las 4 descriptions.
2. **Runtime**: `opencode debug skill` carga las 9 propias con los nuevos
   triggers negativos visibles en la descripción.
3. **Ecosistema**: `sync --apply` OK, `status sin drift`, `verify.sh` verde.
4. **AGENTS.md**: línea 4R extendida con la regla de escala
   (evidencia > tamaño; bajo = solo qa-gate; 4R completo = consentimiento +
   aviso de coste). Sin sección nueva.

## Errores encontrados y corregidos
1. Las descriptions nuevas de `resilience-lens` y `reliability-lens` empezaban
   con "Usar solo si", que NO está entre las frases trigger del validador
   (`usar cuando`, `usar para`, `use when`, `use only when`). El validador
   las rechazó al primer chequeo — funcionó como red de seguridad. Se
   reescribieron a "Usar cuando ..." manteniendo el alcance negativo.

## Coste
~80 tokens fijos adicionales (4 triggers negativos + extensión de la línea
4R). Cero archivos nuevos, cero código ejecutable.
