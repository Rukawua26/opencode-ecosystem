---
nombre: 2026-09-22-qa-gate-secretos
fecha: 2026-09-22
estado: aplicado
afecta: [skills, scripts]
fuente: propio
---

# Guardia de secretos y .env rastreados en qa-gate

## Por que
Un borrador de skill externo ("security-check") proponia un escaneo de secretos
pre-commit. Al auditarlo contra el ecosistema se confirmo que ni `qa-gate` ni las
lentes 4R cubrian secretos ni ficheros sensibles rastreados: `.env`, `*.pem`,
`*.key` o API keys podian colarse en un commit sin ningun aviso. El coste real
era nulo a la hora de reusar: `qa-gate.sh` ya opera sobre el staged diff.

## Antes
`qa-gate.sh` solo detectaba catch vacio, logs de depuracion y TODO/FIXME sobre el
staged diff. Sin chequeo de secretos ni de ficheros sensibles rastreados.

## Despues
- `qa-gate.sh` escanea solo las lineas anadidas del diff contra 5 patrones
  (AKIA, ghp_, sk- de 32+ chars, clave PEM, URL con usuario:password embebido).
  Avisa del tipo de patron sin imprimir el valor del secreto.
- Comprueba `git ls-files` contra `.env*`, `*.pem`, `*.key` e `id_rsa` rastreados.
- En `--strict`, secreto o fichero sensible rastreado -> exit 1, igual que
  catch vacio. Logs/TODO siguen siendo solo avisos. Warn mode sigue en exit 0.
- `qa-gate` SKILL.md describe el nuevo alcance. `risk-lens` hereda el chequeo
  sin cambios porque invoca `qa-gate.sh` en su paso 2.

## Beneficio
Cero skills nuevas (sin duplicar triggers pre-commit), ~20 lineas de bash,
cero dependencias, y una sola fuente de verdad que alimenta a qa-gate y a la
review de riesgo a la vez.

## No regresion
- Comportamientos previos intactos: catch vacio, console.log, TODO/FIXME, exit
  codes de warn y --strict (verificado con casos limpio/sucio/strict).
- Error encontrado y corregido en pruebas: el patron PEM `-----BEGIN...` se
  interpretaba como opcion de grep; fijado con `grep -E --`.
- Falsos positivos del borrador descartados: `postgres://` a secas y `sk-`
  de longitud corta ya no avisan (verificado con caso FP controlado).
- Secreto solo en lineas eliminadas no avisa; es el comportamiento deseado.
- Base reversible: estado anterior disponible en el historial Git del repo
  (`scripts/qa-gate.sh`, `skills/qa-gate/SKILL.md`).

## Verificacion
- `bash -n scripts/qa-gate.sh` -> OK.
- Casos funcionales en repo tmp: limpio (sin avisos), sucio (4 patrones + .env),
  --strict exit 1, FP controlado en silencio, eliminacion en silencio.
- `python3 validate-skills.py skills` -> `[ok] 10 skills valid`.
- `./opencode-ecosystem sync --apply` -> `[ok] sync aplicado`; runtime identico
  a fuente (diff vacio en script y SKILL).
- `./opencode-ecosystem status` -> `[ok] sin drift`.
- `./verify.sh` -> `[ok] verify verde`; `qa-gate.sh --strict` en repo exit 0.

## Periodo prudencial
- 1 semana de uso normal. Estable si: no hay falsos positivos frecuentes en
  warn mode ni avisos en repos sin secretos. Revertir si el gate cansa (avisos
  sin valor) o si el bucle de patrones degrada el tiempo del gate.
- Rollback: `git checkout -- scripts/qa-gate.sh skills/qa-gate/SKILL.md` en
  este repo, `sync --apply`, y mover este doc a `revertido`.

## Fuente (si aplica)
No aplica (borrador revisado y descartado como defectuoso; solo se adoptaron
dos ideas: patrones de secretos y chequeo de .env rastreado, reescritas).
