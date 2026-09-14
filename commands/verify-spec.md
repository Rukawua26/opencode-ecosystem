---
description: Verifica la implementacion contra spec.md delegando en el subagente sdd-verify. Solo lectura.
---

1. Detecta la feature activa; si falta `tasks.md` o no hay tareas completadas, detente.
2. Delega la verificacion al subagente `sdd-verify` (subagent_type sdd-verify): contrasta la implementacion con `spec.md`, `plan.md` y los criterios de aceptacion. No corrijas inline.
3. Reporta hallazgos con evidencia (CRITICAL/WARNING/SUGGESTION) y sugiere revision humana o `/implement-spec` para corregir.
4. Registra el resultado en `spec/features/NNN-nombre/verify.md`.
