---
nombre: 2026-09-26-ultraplan-trigger-mejor-forma
fecha: 2026-09-26
estado: aplicado
afecta: [skills]
fuente: propio
---

# Disparador explicito para ultraplan-lite

## Por que
En la sesion de gestion-leads-sociedad el usuario repitio tres veces la pregunta "es esta la mejor forma de implementar este plan o hay una mejor". Es la cuarta pregunta de la autoauditoria de problema convertida en pregunta explicita del humano. La skill ultraplan-lite ya cubria el caso ("2-3 enfoques y elegir la solucion minima"), pero su descripcion no reconocia la frase literal, asi que no disparaba automaticamente.

## Antes
Descripcion: "Plan, arquitectura y tradeoffs. Usar cuando se necesiten 2-3 enfoques y elegir la solucion minima antes de implementar."
Cuerpo: 5 reglas.

## Despues
Descripcion: "...y ante la pregunta 'es esta la mejor forma de implementarlo o hay una mejor'."
Cuerpo: se anade la regla "6. Si el plan ya es el minimo, dilo sin inventar alternativas: 'no hay forma mejor' es una respuesta valida."

## Beneficio
La pregunta recurrente del usuario activa la skill sin que el modelo tenga que ser interpelado. Y la regla 6 evita el error comun de proponer alternativas mas caras solo porque la pregunta suena a critica: a veces el plan ya es la respuesta.

## Validacion
python3 validate-skills.py skills/ → [ok] 10 skills valid
sync --apply → runtime actualizado (diff confirmado) y sin drift.

## Riesgos
Ninguno: cambio de metadatos (descripcion) y de una nota informativa en el cuerpo, sin alterar logica.

## Reversion
git revert del commit correspondiente; el contenido previo esta en el historial.
