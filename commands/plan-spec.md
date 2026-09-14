---
description: Lee spec.md de la feature activa y genera plan.md con eleccion minima. Sin codigo.
---

1. Detecta la feature activa en `spec/features/` (usa $ARGUMENTS o la mas reciente); si no existe `spec.md`, detente y sugiere `/spec`.
2. Lee `spec/features/NNN-nombre/spec.md`.
3. Genera `spec/features/NNN-nombre/plan.md`: 2-3 enfoques con tradeoffs y la eleccion minima justificada (i5-1235U, 8 GB RAM, ahorro de tokens, YAGNI).
4. Reporta el plan elegido y espera aprobacion antes de `/tasks-spec`. Prohibido codigo.
