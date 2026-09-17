# 009-lenses — Spec

## Problema
El review de `qa-gate.sh` cubre catch-vacío y TODO, pero no las 4R de gentle-ai
(Risk, Resilience, Readability, Reliability). Las 4R no están como skills
disponibles para el agente.

## Alcance
- ENTRA: 4 skills lens (`risk-lens`, `resilience-lens`, `reliability-lens`,
  `readability-lens`) como wrappers guiados de `qa-gate.sh`. Solo informan,
  nunca bloquean ni automatizan juicio humano (especialmente `readability-lens`).
- FUERA: Engram, Pi package, plugins TUI, GGA, RDD hooks, telemetría.

## Criterios de aceptación
1. 4 skills válidas por `validate-skills.py` (nombre regex, description con trigger).
2. Carga por `opencode debug skill` — aparecen las 9 propias + integrada.
3. Cada una indica en el body qué grep ejecutan (sin bloquear) y cuándo usar.
4. `sync --apply` OK, `status sin drift`, `verify.sh` verde.
