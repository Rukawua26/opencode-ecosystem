# 012-spec-constitution — Spec

## Objetivos
Cerrar el gap documentado más antiguo del proyecto: `spec/constitution/` es referenciada por
AGENTS.md desde hace varias features pero nunca existió. La feature 011 lo mitigó vía
lectura condicional en AGENTS.md (no crear archivos vacíos), pero el ancla de acuerdos de
trabajo y stack sigue ausente: cualquier agente o humano nuevo debe deducir las reglas del
contexto o de specs antiguas.

## Alcance (TOMAMOS)
1. **`spec/constitution/working-agreement.md`** — destilado de lo ya decidido y practicado
   (sin políticas nuevas):
   - Rol humano/agente (humano define alcance y aprueba; agente ejecuta y verifica).
   - No avanzar a implementación sin plan aprobado; una tarea por turno.
   - Ciclo RDD: verificación única tras implementar, máx. 1 corrección acotada,
     segundo rechazo = STOP y decisión humana.
   - Fail-closed en decisiones humanas ambiguas (consentimiento explícito).
   - Evidencia-first: registro en `verify.md` al cerrar lote.
2. **`spec/constitution/tech-stack.md`** — destilado del stack real en uso:
   - OpenCode + ecosistema (`~/opencode-ecosystem` como fuente de verdad, sync/publish,
     validate-skills 9/9).
   - Scripts bash con `set -u`, preview por defecto, borrado solo con `--apply`/`--confirm`
     (patrón hygiene.sh).
   - Python 3 stdlib para verificación; JSON/JSONC para config.
   - Máquina: i5-1235U, 8 GB RAM — límite duro para tamaño de modelos y RAM de sesiones.
3. **Referencia viva**: AGENTS.md ya apunta a ambos archivos con lectura condicional
   (línea 12); no se edita AGENTS.md.

## Fuera de alcance (DEJAMOS, con por qué)
- Políticas nuevas no practicadas (definición de hecho, taxonomía de regresión, etc.):
  introducirían acuerdos no validados; se destila solo lo existente.
- Editar AGENTS.md: ya tiene la referencia condicional correcta desde 011.
- Propagar constitution a otros proyectos (pbot, vozart): cada proyecto es dueño de su
  spec; se evaluará allí si aplica.
- Skills, comandos o agentes nuevos: duplicarían el flujo SDD existente.

## Criterios de aceptación
- `spec/constitution/working-agreement.md` y `tech-stack.md` existen y contienen solo
  acuerdos/stack ya practicados y verificables (cada regla trazable a AGENTS.md, a una
  spec anterior o al patrón de un script existente).
- Ningún contenido contradice AGENTS.md ni las features 001-011.
- AGENTS.md sin cambios (la referencia condicional ya existe).
- Verificación independiente (`sdd-verify`) sin hallazgos, o con corrección acotada única.
- `verify.md` registrado con el dictamen.
