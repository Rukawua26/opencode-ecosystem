---
nombre: <fecha-AAAAMMDD>-<slug-del-cambio>
fecha: AAAA-MM-DD
estado: propuesto # propuesto | aplicado | en_observacion | verificado | revertido
afecta: [skills] # skills | configs | scripts | memoria | git | reglas | docs
fuente: propio # propio | gentle-ai | noffolo | otro-repo
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
- Antes de aplicar, conserva el estado actual en Git. Si todavia no existe una base
  versionada, adjunta un fichero `<cambio>.before.md` con el contenido necesario para revertir.

## Verificacion
Comandos ejecutados y resultado exacto (`verify.sh`, `validate-skills.py`, `status`, `opencode debug config`, tests).

## Periodo prudencial
- Duracion / criterio para declararlo estable.
- Lo anterior permanece recuperable hasta que el cambio se verifique sin errores.
- Señales de que es estable / de que debe revertirse.
- Plan de rollback concreto si falla.

## Fuente (si aplica)
Si se tomo de otro repo: referencia a la ficha TOMADO/DEJADO en `~/docs/sources/`.
