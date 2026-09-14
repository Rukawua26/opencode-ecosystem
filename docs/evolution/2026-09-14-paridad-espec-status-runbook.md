---
nombre: 2026-09-14-paridad-espec-status-runbook
fecha: 2026-09-14
estado: en_observacion # propuesto | aplicado | en_observacion | verificado | revertido
afecta: [commands, runbooks, reglas] # skills | configs | scripts | memoria | git | runbooks | reglas | docs
fuente: propio # propio | gentle-ai | noffolo | otro-repo
---

# CMD /spec-status + runbook de crecimiento por demanda (paridad estado)

## Por que
Paridad con gentle-ai `266574b0` incluía un hueco real: el orquestador suyo siempre sabe qué está
en vuelo financieramente porque Engram mantiene el estado SDD; nosotros no teníamos esa vista
canónica (había que leer features uno por uno). Además, el crecimiento del mini-enjambre (agentes
ocultos) necesitaba un proceso contractual documentado para no duplicar ni crear agentes preventivos.

## Antes
- No existía una vista global del estado de features (`spec/features/*`).
- No había proceso para añadir agentes ocultos — se improvisaba (011 los creó sin runbook).
- Runbook `runbook-revisar-agentes.md` referenciaba ruta antigua (`config/agents/`).

## Despues
- **`commands/spec-status.md`** (read-only): lee todas las features, cuenta `[x]/[ ]`, reporta
  tabla con nombre, progreso, estado (abierta/en curso/verificada/en_observacion) y siguiente
  paso recomendado. Si falta un artefacto o hay incoherencia, reporta evidencia, no infiere.
- **`~/docs/runbooks/runbook-agentes-por-demanda.md`**: triggers con evidencia (saturación,
  repetición 2-3, fallo en verify.md), contralogs, checklist 4ª pregunta y receta JSONC, verificación
  pipeline, obligaciones dociales y registro de candidatos (incluye el punto DELETED de JD/refuters).
- **`runbook-revisar-agentes.md`**: prerrequisito actualizado a bloque `agent` + debug agent.
- **AGENTS.md** (línea ~16): añade `/spec-status` y delegación a runbook; +1 línea total.

## Beneficio
- Paridad funcional del "estado SDD" sin Engram completo: `/spec-status` responde la pregunta
  fundamental "en qué estoy".
- Crecimiento de agentes con evidencia + rollback+observación, sin matriz matriz oculta de 20+.

## No regresión
- El comando es read-only; no modifica nada. No interfiere con los 5 comandos existentes.
- El runbook sigue el patrón de runbooks existentes (`runbook-cascada-modelos`, etc.).
- AGENTS.md solo +1 línea de orientación; no cambia ninguna regla existente.
- 0 tokens al arranque: `/spec-status` carga solo al invocarse.

## Verificación
- `/home/miguel/opencode-ecosystem/commands/spec-status.md` existe con el contrato.
- `$CFG/commands/` contiene `spec-status.md` junto a los 5 comandos anteriores.
- `sync --apply` sin drift (`-x '*.bak-*'` cubierto por el fix de 2026-09-14).
- `validate-skills` 9/9 valid; `verify.sh` verde.
- Runbook accesible en `~/docs/runbooks/` scoprelista.padel.

## Periodo prudencial
- Vigilancia hasta 2026-09-28 (mismo ciclo que 010/011).
- Senal de estabilidad: `/spec-status` muestra el estado de features 001-011 correctamente
  (o explica por qué falta información), sin falsos positivos.
- Senal de revertir: si `/spec-status` o el runbook generan confusiones (producen duplicados,
  misses transparentes), documentar y revertir por git.

## Fuente
- Planificación interna (no externa). Referencia a gentle-ai por analogía de concepto (`status`).
