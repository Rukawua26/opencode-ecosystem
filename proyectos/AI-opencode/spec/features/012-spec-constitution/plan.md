# 012-spec-constitution — Plan

## Enfoques considerados

### A. Destilado directo de fuentes existentes (ELEGIDO)
- Redactar ambos archivos extrayendo solo acuerdos ya practicados: AGENTS.md (rol, RDD,
  fail-closed), specs 005-011 (verificación independiente, evidence en verify.md), patrones
  de scripts reales (hygiene.sh: preview por defecto, `set -u`).
- Coste: 2 archivos estáticos en `spec/constitution/`. Riesgo: mínimo (doc-only, reversible
  por git). Tokens: lectura única al implementar features futuras.
- Trazabilidad: cada regla citada con su fuente (AGENTS.md línea, feature, script).

### B. Constitution generada por script (drift-proof)
- Un script que derive working-agreement/tech-stack de AGENTS.md y configs en cada sync.
- Rechazado: parser de Markdown a reglas es frágil, añade código a mantener para 2 archivos
  estáticos que cambian rara vez. YAGNI puro.

### C. No hacer nada (mantener lectura condicional)
- AGENTS.md ya tolera la ausencia desde 011.
- Rechazado: el gap está documentado dos veces (spec 011 y su verify.md); sin constitution,
  cada feature re-decide reglas ya cerradas y un agente nuevo no tiene ancla única.

## Elección mínima
A: es escritura única de lo ya acordado, sin lógica nueva ni mantenimiento continuo.
B automatiza un cambio que ocurre 1-2 veces al año; C perpetúa la deuda documentada.

## Impacto
- +2 archivos markdown en `spec/constitution/` (nuevo directorio).
- 0 cambios de código, 0 cambios en AGENTS.md, 0 cambios en ecosistema (no toca
  `~/opencode-ecosystem`; no requiere sync/publish ni reinicio).
- Token de arranque: +~200 tok solo cuando existan (la lectura ya es condicional).
