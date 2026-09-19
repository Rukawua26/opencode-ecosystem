---
name: ultraplan-lite
description: Plan, arquitectura y tradeoffs. Usar cuando se necesiten 2-3 enfoques y elegir la solucion minima antes de implementar.
---

# ultraplan-lite
1. Lee solo las fuentes necesarias de la feature activa y sus dependencias explicitas.
2. Propone 2-3 enfoques ordenados por coste de RAM, tokens y mantenimiento.
3. Elige el cambio minimo que satisface los criterios (YAGNI).
4. Presenta el plan en chat. Si se autoriza trabajo sustancial, el seguimiento vive en un unico `odd/tasks/<feature>.md` creado por `organic-workflow-lite`.
5. No implementes codigo antes de la aprobacion.
