---
description: Genera tasks.md atomico (15-30 min por tarea) desde spec.md y plan.md. Sin codigo.
---

1. Detecta la feature activa; si faltan `spec.md` o `plan.md`, detente y sugiere el comando que falta (`/spec` o `/plan-spec`).
2. Genera `spec/features/NNN-nombre/tasks.md`: tareas atomicas de 15-30 minutos, cada una con criterio de verificacion y orden de dependencias.
3. Reporta el desglose y espera aprobacion antes de `/implement-spec`. Prohibido codigo.
