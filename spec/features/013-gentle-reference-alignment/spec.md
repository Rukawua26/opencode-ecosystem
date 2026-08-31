# Feature 013: Gentleness Reference Alignment

## Problema

La referencia externa (Gentle AI) se siguió en `~/docs/sources/gentle-ai-analysis.md`
con baseline de agosto 14-29, pero desde entonces hubo cambios (`a537c63` →
`1863432`, beta sin cambios) y aparecieron dos deudas locales:

1. La comparación documental (`docs/comparison.md`, `_MOC.md`, `Sources.md`)
   está desactualizada respecto al estado real alcanzado con la Feature 012.
2. `opencode-doctor --json` no distingue entre plugins activos por
   auto-descubrimiento del directorio y los declarados en `plugin[]`, cosa
   crítica tras mover opcionales a `plugins.disabled/`.

## Alcance

IN:

- Actualizar baseline y decisiones TOMAMOS/DEJAMOS en las 4 notas.
- Añadir al doctor un bloque `plugins` read-only con `configured`,
  `discoveredActive` y `disabled`, sin cargar contenido de plugins.
- Registrar decisión sobre E2E mínimo y sobre optimización de backups,
  sustentada por mediciones locales.
- Tests del nuevo bloque del doctor.

OUT (DEJAMOS, filtro filosofía):

- Engram, TUI, binario Go, updater, firma de binarios, soporte multi-agente,
  perfiles generados masivos, subagentes background, Judgment Day,
  `auto-memory` activo por defecto, dependencia de `main`/beta externas,
  framework E2E general, compresión de backups sin medición previa.

## Criterios de aceptación

- AC1: las 4 notas documentan baselines `1863432`/`420555a` y nuestra versión actual.
- AC2: `opencode-doctor --json` incluye `plugins.{configured,discoveredActive,disabled}`
  y sigue siendo read-only (tests existentes de snapshot intactos).
- AC3: hay una decisión documentada sobre E2E mínimo, con evidencia de cobertura actual.
- AC4: hay medición de backups (tamaño, duplicados) antes de decidir compresión.
- AC5: suites completas verdes y CI verde; commit único de cierre.
