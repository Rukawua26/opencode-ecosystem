---
name: code-forge-fix-lite
description: Bug, error, regresion y TDD. Usar para reproducir un fallo, encontrar su causa raiz y aplicar el fix minimo verificable.
---

# code-forge-fix-lite
1. Traza la causa raiz aguas arriba; tras 3 lecturas sin respuesta, delega una exploracion acotada.
2. Escribe un test que reproduzca el fallo cuando sea viable.
3. Aplica el fix minimo y ejecuta la verificacion relevante.
4. Propón registrar en `observations.log` solo una causa raiz o decision reutilizable, y escribe solo tras aprobacion del usuario; nunca resultados efimeros, fechas o numeros de linea.
