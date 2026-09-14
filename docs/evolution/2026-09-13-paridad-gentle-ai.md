---
nombre: 2026-09-13-paridad-gentle-ai
fecha: 2026-09-13
estado: en_observacion # propuesto | aplicado | en_observacion | verificado | revertido
afecta: [commands, configs, skills, reglas] # skills | configs | scripts | memoria | git | reglas | docs
fuente: gentle-ai # propio | gentle-ai | noffolo | otro-repo (baseline `266574b0`)
---

# Paridad con gentle-ai: comandos SDD + mini-enjambre + preflight

## Por que
El objetivo del humano es que el ecosistema funcione lo mas semejante posible a gentle-ai.
Analisis del repo en su nuevo baseline `266574b0` (ADR-004, clon temporal) encontro 2 gaps
reales con paridad funcional: (1) `AGENTS.md` prometia 5 comandos SDD (`/spec`, `/plan-spec`,
`/tasks-spec`, `/implement-spec`, `/verify-spec`) pero `~/.config/opencode/commands/` estaba
vacio; (2) nuestro SDD ejecutaba todo inline en el hilo principal, inflando contexto, mientras
que el mecanismo suyo (fase pesada -> subagente con contexto fresco -> resumen) ahorra tokens.
Evidencia: `sdd-overlay-single.json` y `sdd-orchestrator.md` upstream; el schema actual de
OpenCode (`AgentConfig`) soporta `mode: subagent`, `hidden`, `permission`.

## Antes
- `commands/` vacio: los 5 comandos eran promesa de AGENTS.md sin ficheros reales.
- Sin agentes definidos en `opencode.jsonc`: solo subagente `explore` nativo.
- SDD fases pesadas (implementacion, verificacion) inline en el hilo principal.
- Preflight SDD: pausa manual sin estructura.

## Despues
- `commands/` con 5 comandos cortos (frontmatter `description`, cuerpo con gates y pausas),
  gestionados por el CLI (managed_list, sync con backup, status drift, publish).
- Mini-enjambre en bloque `agent` de `configs/opencode.jsonc` (patron overlay suyo, escala 2/20):
  `sdd-implement` (subagent, hidden, task deny; implementa una tarea atomica y devuelve
  status/resumen/archivos/riesgos) y `sdd-verify` (subagent, hidden, edit/write/task deny;
  read-only con puerta de precision, devuelve CRITICAL/WARNING o `Sin hallazgos.`).
  0 tokens al arranque: los prompts solo se cargan al invocar el subagente.
- `/implement-spec` y `/verify-spec` delegan en esos subagentes (AGENTS.md: depth 1, no inline).
- Preflight agrupado en 1 `question` (modo + alcance + verificacion) como paso 1 de
  `ultraplan-lite`, solo cuando hay feature SDD; sin wizard.

## Beneficio
- Paridad funcional: flujo visible identico (`/implement-spec` ~ `/sdd-apply`) y mecanismo
  interno identico en lo que importa (contexto fresco por fase pesada).
- Ahorro real: la implementacion de una tarea no ensucia el hilo principal; el verificador
  read-only corre aislado.
- Consentimiento: el preflight agrupado pide modo/alcance una sola vez, con STOP.

## No regresion
- Todo aditivo: comandos nuevos no existen sin llamada; subagentes hidden solo invocables via task.
- CLI: cambios aditivos; skills/scripts/configs flujos intactos; `uninstall` por manifiesto ahora
  incluye `commands/` automaticamente.
- `ultraplan-lite`: solo se anadio el paso 1 (preflight); los pasos previos quedan como estaban.
- Si el bloque `agent` no fuera aceptado por el runtime, es una clave inerte: sin efecto; rollback
  por git + sync.
- Fases ligeras (spec, plan) siguen en el hilo principal; no se orquesta lo que no lo necesita.

## Verificacion
- `python3 ~/opencode-ecosystem/validate-skills.py ~/opencode-ecosystem/skills` -> `[ok] 9 skills valid`.
- `./opencode-ecosystem sync --apply` -> sin drift, ficheros en `$CFG/commands/`.
- JSON de config valido (comentarios jsonc stripping + parse).
- Base reversible: commit previo en Git (estado anterior sin agentes ni commands).
- Reinicio de OpenCode requerido: agentes y comandos nuevos solo se cargan al arrancar.
- Prueba post-reinicio (pendiente del humano): `/spec` debe lanzar preflight; `/implement-spec`
  debe delegar en `sdd-implement`; `sdd-verify` debe responder `Sin hallazgos.` o hallazgos con evidencia.

## Periodo prudencial
- Vigilancia hasta 2026-09-27 (mismo ciclo que loop-budget y alineacion gentle-ai).
- Senal de estabilidad: al menos una feature SDD completa via comandos con el mini-enjambre y sin
  bloqueos no explicados; drift cero mantenido.
- Senal de revertir: los subagentes no aparecen tras reinicio, los comandos no disparan, o el
  aislamiento de contexto rompe flujos (artefactos no encontrados).
- Rollback: `git revert` del commit de este cambio en `~/opencode-ecosystem`, validar y `sync --apply`;
  quitar el bloque `agent` de la config si el runtime lo requiere.

## Fuente
- gentle-ai @ `266574b0`: `internal/assets/opencode/sdd-orchestrator.md`, `sdd-overlay-single.json`,
  `commands/sdd-*.md`, `session_preflight.go`, `sdd-task-result-artifacts.ts`.
- Mapa de paridad completo: `~/docs/sources/gentle-ai-analysis.md` (Revision 2026-09-13, 007-paridad).
- DEJADO del mismo analisis: orquestador dedicado, matriz 20+ agentes, plugins Go/TS, engram,
  persona, ledger/refuter/judgment-day, skill-registry, chained PRs (ver nota de analisis).
