---
nombre: <fecha-AAAAMMDD>-<slug-del-cambio>
fecha: AAAA-MM-DD
estado: propuesto | aplicado | verificado | revertido
afecta: [ skills | configs | scripts | memoria | git ]
fuente: opportunista | gentle-ai | noffolo | otro-repo | propio
---

# <titulo del cambio>

## Por que
Problema real, quien lo sufre, evidencia de que existe.

## Antes
Como se comportaba antes del cambio.

## Despues
Como se comporta ahora.

## Beneficio
Esperado o medido (tokens, RAM, menos pasos, menos errores).

## No regresion
- El cambio es mejor o igual que lo anterior; nunca se vuelve a una version ya superada.
- Lista de comportamientos previos que deben seguir funcionando.

## Verificacion
Comandos ejecutados y resultado exacto (`verify.sh`, `validate-skills.py`, `status`, `opencode debug skill`, tests).

## Periodo prudencial
- Duracion / criterio para declararlo estable.
- Lo anterior no se borra hasta que el cambio se verifique sin errores.
- Señales de que es estable / de que debe revertirse.
- Plan de rollback concreto si falla.

## Fuente (si aplica)
Si se tomo de otro repo: referencia a la ficha TOMADO/DEJADO en `~/docs/sources/`.
