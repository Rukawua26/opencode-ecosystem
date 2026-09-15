---
description: Estado canonico de features SDD: lee spec/features/*/ y reporta estado y siguiente paso. Solo lectura.
---

Reporta el estado canonico de todas las features SDD del proyecto. Solo lectura: no modifiques ningun archivo.

1. Lista `spec/features/*/`; si no hay features, dilo y sugiere `/spec`.
2. Para cada feature lee `tasks.md` (cuenta `[x]` y pendientes), `spec.md` (objetivo si falta contexto) y `verify.md` si existe (estado y periodo de observacion).
3. Presenta una tabla: feature | tareas (x/total) | estado (abierta/en curso/verificada/en observacion) | siguiente paso recomendado.
4. Estado sugerido: todas las tareas `[x]` + verify.md -> verificada (o en observacion si verify.md declara periodo prudencial vigente); ninguna `[x]` -> abierta; mezcla -> en curso.
5. Si falta un artefacto esperado (`spec.md`, `tasks.md`) o el estado es incoherente (verify.md sin tasks completas, etc.), senala la evidencia exacta; no infieras ni inventes. `plan.md` es opcional (features pequenas/mecanicas); su ausencia no es hallazgo.
