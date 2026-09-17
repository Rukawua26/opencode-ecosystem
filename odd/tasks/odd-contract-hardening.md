# Endurecimiento del contrato ODD (odd-contract-hardening)

## Objetivo
Cerrar las brechas de comportamiento con ODD upstream (gentle-ai v3.1.0): incertidumbre acotada, IDs estables, TDD recuperable, delegacion con documento, evidencia honesta y reanudacion robusta.

## Problema y por que
La skill organic-workflow-lite (2026-09-17) cubria el flujo basico, pero le faltaban los detalles finos del protocolo ODD v3.1: research/preguntas sin cota, tareas renumerables, TDD sin modo/fuente/runner persistente, workers sin obligacion de leer el documento, evidencia sin estados y reanudacion sin descubrimiento de multiples features. Quien lo sufre: cualquier feature sustancial interrumpida o delegada.

## Alcance
### Incluye
- Endurecer `skills/organic-workflow-lite/SKILL.md` (unico artefacto de comportamiento).
- Dogfood con este documento.
- Actualizar `docs/evolution/2026-09-17-gentiai-odd-lite.md`.

### Excluye
- Kernel AGENTS.md (ya correcto y minimo).
- `verify-odd-contract.sh` (automatizacion pospuesta a evidencia de regresiones repetidas).
- Engram, commits automaticos, review por commit/slice, chained PRs, 400 lineas, RDD, /odd-status.

## Restricciones
- i5-1235U, 8 GB RAM, ahorro de tokens: cero dependencias, agentes o estado nuevos.
- Sin regresion: SDD, comandos y configs intactos.
- Gate Git humano: commit solo con peticion explicita.

## TDD
- Modo: off
- Fuente: default (sin politica de proyecto para skills markdown)
- Runner: `python3 validate-skills.py skills` + `bash verify.sh` (checks funcionales obligatorios)

## Tareas
- [x] T1 — Incertidumbre acotada: research nombrado, 1 pregunta por decision real, max 1 challenge de premisa
  - Criterio: regla en skill con las tres cotas
  - Verificacion: validate-skills ok + revision del diff
- [x] T2 — IDs estables (T1.. sin renumerar) y bloque TDD (modo/fuente/runner) en el documento
  - Criterio: reglas presentes en la skill
  - Verificacion: validate-skills ok
- [x] T3 — Delegacion con documento, evidencia con estados y reanudacion con descubrimiento
  - Criterio: reglas presentes en la skill
  - Verificacion: validate-skills ok
- [x] T4 — Validar, sincronizar y probar comportamiento, incluida reanudacion en contexto fresco
  - Criterio: sync sin drift, runtime actualizado, subagente con contexto fresco lee el documento y reporta la siguiente tarea sin crear artefactos
  - Verificacion: status sin drift + subagente + verify.sh verde
- [x] T5 — Registrar resultados en evolution doc y dejar proxima prueba (sesion nueva del humano)
  - Criterio: evolution doc actualizado con evidencia y estado `en_observacion`
  - Verificacion: lectura del doc

## Decisiones aceptadas
- 2026-09-17: posponer `verify-odd-contract.sh` (YAGNI; automatizar solo con evidencia de regresiones repetidas).
- 2026-09-17: mantener gate Git humano (commit solo con peticion explicita).

## Evidencia
- T1 — Estado: passed
  - Comando: `python3 validate-skills.py skills` (fuente) tras editar skill
  - Resultado: `[ok] 10 skills valid`; item 2 con las tres cotas presente en el diff
- T2 — Estado: passed
  - Comando: `python3 validate-skills.py skills`
  - Resultado: `[ok] 10 skills valid`; items 5 (TDD modo/fuente/runner) y 6 (IDs estables) presentes
- T3 — Estado: passed
  - Comando: `./opencode-ecosystem sync --apply && ./opencode-ecosystem status`
  - Resultado: `[ok] sync aplicado`, `[ok] sin drift`; items 7, 8 y 10 presentes en runtime
- T4 — Estado: passed
  - Comando: subagente `general` con contexto fresco (read-only) + `bash verify.sh` + `scripts/qa-gate.sh`
  - Resultado: subagente descubrio el documento, reporto T4/T5 pendientes, reconcilio contra `git status` (coherente), cero artefactos, cero SDD; verify verde; qa-gate exit 0
- T5 — Estado: passed
  - Comando: lectura de `docs/evolution/2026-09-17-gentiai-odd-lite.md`
  - Resultado: secciones Despues/Verificacion actualizadas con evidencia; estado sigue `en_observacion`

## Progreso
- Estado: completada (codigo y docs); en observacion hasta 2026-10-01 o 2 features sustanciales
- Ultima tarea terminada: T5
- Siguiente paso: reanudacion desde una sesion nueva del humano + dogfood en features reales
- Bloqueos: ninguno
