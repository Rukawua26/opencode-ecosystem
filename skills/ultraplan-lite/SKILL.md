---
name: ultraplan-lite
description: Plan, arquitectura y tradeoffs. Usar cuando se necesiten 2-3 enfoques y elegir la solucion minima antes de implementar.
---

# ultraplan-lite
1. Lee solo la spec de la feature activa y sus dependencias explicitas.
2. Propone 2-3 enfoques ordenados por coste de RAM, tokens y mantenimiento.
3. Elige el cambio minimo que satisface los criterios (YAGNI).
4. En Plan Mode presenta el plan en chat. Crea artefactos SDD (`spec.md` -> `plan.md` -> `tasks.md`) solo si SDD fue pedido explicitamente o una propuesta aceptada; nunca `plan.md`/`tasks.md` sin spec previa.
5. No implementes codigo antes de la aprobacion.
