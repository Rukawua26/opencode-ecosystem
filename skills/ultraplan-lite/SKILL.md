---
name: ultraplan-lite
description: Plan, arquitectura y tradeoffs. Usar cuando se necesiten 2-3 enfoques y elegir la solucion minima antes de implementar, y ante la pregunta 'es esta la mejor forma de implementarlo o hay una mejor'.
---

# ultraplan-lite
1. Lee solo las fuentes necesarias de la feature activa y sus dependencias explicitas.
2. Propone 2-3 enfoques ordenados por coste de RAM, tokens y mantenimiento.
3. Elige el cambio minimo que satisface los criterios (YAGNI).
4. Presenta el plan en chat. Si se autoriza trabajo sustancial, el seguimiento vive en un unico `odd/tasks/<feature>.md` creado por `organic-workflow-lite`.
5. No implementes codigo antes de la aprobacion.
6. Si el plan ya es el minimo, dilo sin inventar alternativas: "no hay forma mejor" es una respuesta valida.
