---
nombre: 2026-09-17-gentiai-odd-lite
fecha: 2026-09-17
estado: en_observacion # propuesto | aplicado | en_observacion | verificado | revertido
afecta: [skills, reglas, docs] # skills | configs | scripts | memoria | git | reglas | docs
fuente: gentle-ai # propio | gentle-ai | noffolo | otro-repo (video 3 + baseline `eae8fadd5ece` / v3.1.0)
---

# ODD-lite: skill organic-workflow-lite + kernel organico en AGENTS.md

## Por que
Gentle-AI v3.x (video 3, 2026-09-15..17) convirtio ODD en el workflow por defecto del orquestador
y SDD en rama explicita. Nuestro routing ya cubria ~2/3 de esa filosofia (1-3 inline, 4+ delega,
SDD explicito, evidencia), pero tenia dos huecos reales: (1) ninguna via para trabajo sustancial
no-SDD con progreso recuperable (solo existian artefactos SDD completos o nada); (2) contradiccion
en AGENTS.md: "features nuevas o cambios complejos" activaban SDD automaticamente pese a que la
misma filosofia exige peticion explicita. Ademas, al inspeccionar el flujo se hallaron dos
referencias rotas en AGENTS.md (`customize-opencode` y `opencode debug skill`, inexistentes en el
runtime actual). Evidencia: Compare API `266574b0..eae8fadd5ece` (58 commits), release v3.1.0,
`internal/components/agentguidance/routing.go`; grep del runtime local.

## Antes
- Trabajo sustancial no-SDD: sin documento de seguimiento; reanudar dependia de `/handoff` o memoria.
- AGENTS.md: "Para features nuevas o cambios complejos, crear primero spec..." (SDD auto por tamano).
- AGENTS.md: referencias a `customize-opencode` y `opencode debug skill` fallaban al ejecutarse.
- 9 skills; sin skill ODD (verificado: no existia equivalente; context-compressor mapea repos, no
  flujo de trabajo; ultraplan-lite es pre-aprobacion, no seguimiento).

## Despues
- Skill nueva `organic-workflow-lite` (10a): autorizacion mutacion vs read-only, alcance aprobado
  antes del primer write, documento unico `<proyecto>/odd/tasks/<feature>.md` (objetivo, alcance,
  restricciones, tareas con criterio, decisiones, evidencia, progreso), tarea a tarea con routing
  normal, `[x]` solo con resultado observado, cambios de alcance sin expansion automatica,
  reanudacion file-first contrastando `git status`/diff, cierre con qa-gate y verificacion
  proporcional al riesgo (nunca por checkbox). Git siempre con peticion explicita.
- Kernel ODD-lite en AGENTS.md (3 bullets, ~90 tokens): flujo por defecto, trabajo pequeno inline
  vs sustancial via skill, implementar no autoriza delivery.
- SDD explicito: rama del flujo organico, nunca por tamano/complejidad/riesgo solos.
- Rol Del Programador: "no avances a implementacion sustancial sin alcance aprobado".
- Fixes de referencias rotas: protocolo de skills del ecosistema (sin skill inexistente) y
  verificacion via `~/.config/opencode/skills/` (sin `opencode debug skill`).
- Terminologia: el ciclo sdd-implement->sdd-verify se documenta como "verificacion independiente";
  RDD queda reservado para receipt-driven real (fuera de alcance). Docs historicos no se reescriben.

## Beneficio
- Paridad funcional con ODD upstream sin Engram, binario, commits automaticos, review por commit
  ni chained PRs: una feature sustancial se reanuda leyendo UN archivo local.
- ~90 tokens de kernel global pagados siempre; el detalle largo de ODD solo se paga al invocar la
  skill (0 tokens al arranque, verificado en runtime).
- Elimina la contradiccion SDD-auto y dos referencias rotas que fallaban al seguirlas.

## No regresion
- Base reversible: commit previo `8c53e0e` (skills 9, AGENTS.md anterior en repo home); docs
  evolutivos previos no se tocan.
- Cambio aditivo: la skill existe sin invocarse; sin cambios en configs, comandos, agentes,
  plugins, MCP ni memoria. SDD intacto (`/spec`..`/verify-spec`, mini-enjambre igual).
- Las reglas de routing, lentes 4R, qa-gate y git-atomic-committer (commit solo con peticion
  explicita) siguen mandando; la skill las referencia, no las duplica.

## Verificacion
- `validate-skills.py skills` -> "[ok] 10 skills valid".
- `./opencode-ecosystem sync --apply` -> "[ok] sync aplicado"; `status` -> "[ok] sin drift".
- Skill visible en runtime: `ls ~/.config/opencode/skills/` contiene `organic-workflow-lite` y el
  sistema la notifico como disponible tras sync (sin reinicio).
- `opencode debug skill` no existe en OpenCode V2 actual (hallazgo corregido en AGENTS.md).
- `verify.sh` -> verde.
- Dogfood de escenarios planificado para la primera feature sustancial real (read-only no crea
  artefactos; pequeno inline; sustancial crea unico doc; mencion "SDD" no lo activa).

## Periodo prudencial
- Vigilancia hasta 2026-10-01 (o 2 features sustanciales reales, lo que ocurra antes).
- Estable si: las consultas read-only siguen sin crear artefactos; una feature sustancial produce
  exactamente un documento reanudable; no se dispara SDD sin peticion; `AGENTS.md` no crece mas.
- Revertir si: ODD crea documentos en tareas triviales, se confunde con SDD, o la skill se carga
  en contexto pequeño. Rollback: `git revert` en `~/opencode-ecosystem` + `sync --apply`; en el
  repo home, revert del commit de AGENTS.md. Sin estado que migrar.

## Fuente
- Video 3 Gentleman Programming (WM2JAuR-MOU) contrastado con repo `eae8fadd5ece` / v3.1.0 y con
  Gentleman.Dots `6f44b797b016` (sin ODD; solo dotfiles).
- Ficha TOMAMOS/DEJAMOS: `~/docs/sources/gentle-ai-analysis.md`, seccion "Revision 2026-09-17".
