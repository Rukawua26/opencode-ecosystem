---
name: ultraplan-lite
description: Plan, arquitectura y tradeoffs. Usar cuando se necesiten 2-3 enfoques y elegir la solucion minima antes de implementar.
---

# ultraplan-lite
1. Preflight (solo si hay feature SDD activa o pedida): una sola pregunta agrupada con la tool `question` — modo (interactivo/auto) + confirmacion de alcance + verificacion esperada. Labels exactos, sin wizard. STOP tras la respuesta; cachea la eleccion para la sesion.
2. Lee solo la spec de la feature activa y sus dependencias explicitas.
3. Propone 2-3 enfoques ordenados por coste de RAM, tokens y mantenimiento.
4. Elige el cambio minimo que satisface los criterios (YAGNI).
5. En Plan Mode presenta el plan en chat. Crea artefactos SDD (`spec.md` -> `plan.md` -> `tasks.md`) solo si SDD fue pedido explicitamente o una propuesta aceptada; nunca `plan.md`/`tasks.md` sin spec previa.
6. No implementes codigo antes de la aprobacion.
