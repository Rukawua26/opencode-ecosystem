---
nombre: 2026-09-13-alineacion-gentle-ai
fecha: 2026-09-13
estado: en_observacion
afecta: [skills, git, reglas, docs]
fuente: gentle-ai
---

# Alineacion de lenses y commits con gentle-ai (main `131a328a`)

## Por que
Los lenses 4R disparaban falsos positivos sobre el arbol completo (`rg` sin scope);
`risk-lens` usaba un patron roto (`.edge.`); `resilience-lens` declaraba "sin timeout"
solo por la presencia de `setTimeout`; `reliability-lens` hacia una heuristica ambigua
de aserciones; `git-atomic-committer` nunca se preguntaba si tests/docs viajaban con el
codigo ni si el mensaje contaba el resultado. Ademas el repo no tenia historial de
versiones, con lo que revertir era imposible.

Durante la verificacion final se detecto que la primera implementacion guardaba las
rutas en una cadena `$F`: separaba nombres con espacios y, si el diff estaba vacio,
`rg` podia volver a recorrer el arbol. Se corrigio antes de cerrar la evolucion.

## Antes
- Lenses: `rg -n '<patron>'` sin rango de ficheros; sin contrato de silencio.
- risk-lens: patron `.edge.` (coincidia con cualquier identificador).
- resilience-lens: presencia de `sleep|setTimeout` -> riesgo seguro.
- reliability-lens: check estrambotico `expect().and/or` en el ANTES.
- commits: sin regla de "tests y docs con el codigo ni mensaje-outcome".
- formacion solo: plantillas SDD sin trazabilidad de cambios (no versionado).

## Despues
- Las 4 lenses cargan rutas NUL-safe en un array Bash con `mapfile`; priorizan el
  staged diff, usan el working diff como fallback y no ejecutan `rg` si ambos estan vacios.
- Todas incluyen "puerta de precision" (evidencia o silencio; prohibidos hallazgos de estilo)
  y contrato de salida `Sin hallazgos.` para evitar ruido.
- risk-lens perdio el patron roto `.edge.`; resilience evalua impacto, no la mera presencia;
  reliability elimina el check ambiguo.
- git-atomic-committer: tests y docs viajan en el mismo commit; el mensaje explica el
  resultado, no la lista de ficheros.
- Nota `~/docs/sources/gentle-ai-analysis.md` actualizada con baseline `131a328a`.
- El repo `~/opencode-ecosystem` tiene git + primer commit (`a2f77e4`).

## Beneficio
- Menos falsos positivos y menos tokens gastados en barridos irrelevantes.
- Rutas con espacios y diffs vacios se manejan sin ampliar accidentalmente el scope.
- Alineacion selectiva con el repo modelo (gentle-ai) sin cargo de su maquinaria RDD.
- Rollback real por primera vez en el ecosistema.

## No regresion
- La logica de verificacion sigue intacta; solo cambio el alcance y el filtrado.
- Ninguna lens perdio una capacidad util: se eliminaron heurísticas falsas o erroneas.
- El comportamiento `lens = informa, nunca bloquea` se conserva inalterado.
- Como el cambio precede al historial Git, la baseline anterior se conserva en
  `2026-09-13-alineacion-gentle-ai.before.md`. Los cambios futuros deben conservar
  su estado anterior en un commit antes de aplicar la evolucion.

## Verificacion
- `python3 ~/opencode-ecosystem/validate-skills.py ~/opencode-ecosystem/skills` -> `[ok] 9 skills valid`.
- `~/opencode-ecosystem/opencode-ecosystem sync --apply` -> drift-cero tras sincronizar.
- `~/opencode-ecosystem/verify.sh` -> verde.
- `opencode debug skill` -> 9/9 skills cargan; las 5 editadas muestran contenido nuevo.
- Prueba con una ruta que contiene espacios -> `rg` recibe el fichero como un argumento.
- Asercion sobre `opencode debug skill` -> las 4 lenses contienen `mapfile -d` y
  `"${files[@]}"`.
- `git log --oneline` (ecosistema) -> base `a2f77e4`.

## Periodo prudencial
- Estado tras 14 dias de uso real (hasta 2026-09-27): si no hay falsos positivos / falsos
  negativos graves, se declara estable.
- Senales de revertir: lens que deje de disparar donde antes si lo hacia, o que dispare
  en tests triviales. Plan: restaurar la baseline `.before.md`, validar y ejecutar
  `./opencode-ecosystem sync --apply`.
- El backup `~/.config/opencode/backups/skills-20260913/` contiene el estado nuevo;
  sirve como copia operativa, no como rollback a la baseline anterior.

## Fuente
- `internal/assets/skills/work-unit-commits/SKILL.md` (git-atomic-committer parts).
- `internal/assets/claude/agents/review-risk.md` (sweep acotado + puerta de precision).
- **DEJADO** (sin adoptar): findings ledger, refuters 2-de-3, Judgment Day, chained PRs,
  presupuesto 400 lineas y maquinaria SDD. Filtro: 8 GB RAM, YAGNI, carga local minima.
