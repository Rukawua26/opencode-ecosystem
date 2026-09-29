---
nombre: 2026-09-29-skill-supabase-apply-lite
fecha: 2026-09-29
estado: aplicado
afecta: [skills]
fuente: propio
---

# Skill supabase-apply-lite (aplicar en el remoto con evidencia)

## Por que
Durante la fase de roles del CRM se repitio un mismo flujo de 6 pasos: leer el estado remoto, aplicar una migracion con `apply_migration`, volver a leer para contrastar, desplegar una Edge Function, confirmar que el contenido activo es el del fichero y cerrar con un smoke test HTTP mas una nota de evidencia en `odd/tasks/`. Sin skill, cada repeticion obligaba a reconstruir el orden desde cero y era facil saltarse la relectura posterior al deploy o el chequeo de efectos laterales en el smoke test. Evidencia: el flujo existio al menos dos veces en la misma semana (migracion de campanas `202609290001` y migracion de roles `202609290002` + despliegue de `authorize-user`), y uno de los hallazgos (upsert con `onConflict` sobre una columna sin unica) solo salio a la luz porque se verifico leyendo el remoto tras aplicar.

## Antes
11 skills, ninguna cubria el remoto de Supabase. Habia un subagente `supabase` para inspeccion y consulta, pero no un protocolo de escritura + verificacion + evidencia, asi que el orden de pasos dependia de la memoria de la sesion.

## Despues
Skill nueva `skills/supabase-apply-lite/SKILL.md` con 7 pasos numerados: autorizacion explicita, pre-flight read-only (con parada si el cuerpo remoto difiere del fichero), aplicacion idempotente, verificacion read-only en el remoto, despliegue de Edge Function con relectura tras deploy, smoke HTTP con chequeo de efectos laterales, y evidencia en `odd/tasks/<feature>.md` sin secretos. Sincronizada al runtime: aparece en `~/.config/opencode/skills/supabase-apply-lite`.

## Beneficio
- 6-7 pasos ya no se reconstruyen a mano: se sigue una lista con la verificacion obligatoria.
- Menos riesgo de dejar el remoto a medio aplicar o de dar por bueno un deploy sin mirar el contenido activo.
- Coste de contexto bajo: cuerpo breve (7 lineas densas), estilo y vocabulario coherentes con `qa-gate` y `organic-workflow-lite`.

## No regresion
- Alta de skill nueva: no modifica ni sustituye a ninguna existente; la base anterior (11 skills) sigue intacta en el commit `67dbb55` y no se elimina.
- Comportamientos que deben seguir funcionando: `validate-skills.py` en verde, `sync --apply` sin errores, las 11 skills previas siguen en `~/.config/opencode/skills/`.
- No aporta comandos nuevos ni toca `scripts/`, `configs/` ni la memoria.

## Verificacion
- `python3 ~/opencode-ecosystem/validate-skills.py skills` → `[ok] 12 skills valid`, exit 0.
- `~/opencode-ecosystem/opencode-ecosystem sync --apply` → `[ok] 12 skills valid`, `[ok] sync aplicado`, exit 0 (backups de `opencode.jsonc`, `dcp.jsonc`, `cron-jobs.json`).
- `ls ~/.config/opencode/skills/` → `supabase-apply-lite` presente junto a las 11 anteriores.

## Periodo prudencial
- Duracion: hasta la siguiente aplicacion real en remoto con la skill cargada.
- Señal de estable: se aplican migracion y deploy siguiendo la lista, con evidencia registrada y ninguna fase de verificacion saltada.
- Señal de revertir: si el paso 2 (pre-flight) o el 4 (relectura) se omiten igualmente por ser obvios en el 100% de los casos, o si el cuerpo resulta mas largo de lo util.
- Rollback: `rm -rf skills/supabase-apply-lite/` y `sync --apply`; la base queda en `67dbb55`.

## Fuente (si aplica)
No aplica: flujo propio derivado de la sesion de implementacion de roles del CRM.
