# odd/tasks/ui-ux-master.md

## Objetivo
Crear la skill global `ui-ux-master` en la fuente de verdad `~/opencode-ecosystem/skills/`, que guíe el diseño de interfaces web completas: dirección de arte intencional, tokens, usabilidad y verificación del resultado.

## Problema y por qué
El ecosistema no tiene ninguna skill de diseño (verificado: 10 skills instaladas, ninguna de diseño visual). El usuario aporta una base externa (ui-ux-master: frontend-design + UI/UX Pro Max) y pide una skill propia que produzca diseños completos y utilizables, no solo estilos: el valor está en obligar a verificar el diseño funcionando y adaptarlo al producto existente.

## Alcance
Incluye: `SKILL.md` en `skills/ui-ux-master/` con 3 modos (diseñar/construir, definir sistema, auditar), regla de proporcionalidad, accesibilidad práctica y verificación del resultado; validación, sync y verificación de runtime; doc de evolución.
Excluye: skills separadas independientes; diseño móvil nativo u otras disciplinas; cambios a skills existentes; configuración de OpenCode (plugins/config de arranque); commit/push/PR/merge.

## Restricciones
- Español, sin acentos en el contenido de la skill.
- Cuerpo breve, estilo de las skills existentes (descripción "qué hace + Usar cuando").
- No commitear (base reversible: `skills/` sin cambios pendientes en Git).
- i5-1235U / 8GB: sin procesos pesados ni polling.

## No romper
- Las 10 skills existentes y su descubrimiento (`python3 validate-skills.py skills` verde).
- `./opencode-ecosystem status` termina `[ok] sin drift`.
- Trabajo ajeno en curso (feature `monitor-ejecucion-observable`, cambios M en `control/` y docs sin commit): no tocar.
- No commitear, no pushear, no crear PR, no borrar worktrees.

## TDD
Modo: off. Fuente: default (no hay política TDD para skills ni instrucción del usuario). Runner: no disponible para TDD; checks funcionales obligatorios: `python3 validate-skills.py skills`, `./opencode-ecosystem status`, presencia en `~/.config/opencode/skills/`.

## Tareas
- [x] T1: Crear `skills/ui-ux-master/SKILL.md` con el contenido aprobado; validar con `python3 validate-skills.py skills`; sincronizar con `./opencode-ecosystem sync --apply`; verificar aparición en `~/.config/opencode/skills/` y `status` sin drift; documentar en `docs/evolution/2026-09-29-skill-ui-ux-master.md` usando `_TEMPLATE.md`. Criterio: skill descubrible, validación verde, runtime sin drift, doc de evolución completo.

## Criterios de aceptación
- [x] `skills/ui-ux-master/SKILL.md` existe con frontmatter `name: ui-ux-master` y description "qué hace + Usar cuando".
- [x] Contenido en español, sin acentos, cuerpo breve: flujo de 5 pasos + 3 modos como intenciones + regla de proporcionalidad.
- [x] `python3 validate-skills.py skills` exit 0.
- [x] `./opencode-ecosystem sync --apply` sin errores y la skill aparece en `~/.config/opencode/skills/ui-ux-master/`.
- [x] `./opencode-ecosystem status` termina `[ok] sin drift`.
- [x] Doc de evolución en `docs/evolution/` usando `_TEMPLATE.md` con decisión, base reversible y no regresión.
- [x] Sin commit, push ni PR.

## Decisiones aceptadas
- Skill única con modos como intenciones (no comandos obligatorios) frente a skills separadas (pérdida de contexto, 2 pasos) y monolito rígido (sobredimensiona peticiones pequeñas).
- Proporcionalidad: petición pequeña = respuesta pequeña; página completa = identidad + tokens + implementación + comprobaciones.
- Accesibilidad práctica: contraste y foco verificados; no declarar WCAG sin comprobar.
- Estados (carga, vacío, error, deshabilitado) donde correspondan, no por obligación.
- Alcance inicial: interfaces web; ampliar solo si aparece la necesidad.
- Descartado: usar el ejemplo React/Tailwind del usuario como plantilla de producción (semántica incompleta, estados solo visuales).

## Reutilización investigada
- No existe skill de diseño equivalente (verificado en `~/.config/opencode/skills/` y `skills/` del ecosistema).
- Canónica de formato: skills existentes del ecosistema (kebab-case, description "qué hace + Usar cuando", cuerpo breve sin acentos).
- Documentación oficial V2 de skills consultada (frontmatter, discovery, sync); el runtime ya usa `~/.config/opencode/skills` como fuente global.
- Base externa del usuario (frontend-design + UI/UX Pro Max) adaptada: se añaden verificación del resultado, respeto por el sistema existente y proporcionalidad.

## Evidencia
- Estado inicial: `./opencode-ecosystem status` → `[ok] sin drift` (passed). Git: `skills/` sin cambios pendientes (base reversible commiteada); trabajo ajeno M en `control/` (no tocar).
- `python3 validate-skills.py skills` → `[ok] 11 skills valid`, exit 0 (passed, observado por el padre tras el worker).
- Presencia: `skills/ui-ux-master/` en fuente de verdad y `~/.config/opencode/skills/ui-ux-master/` en runtime (passed, observado).
- Acentos: `grep -nP '[áéíóúñü...]' SKILL.md` sin coincidencias, exit 1 (passed, observado).
- `./opencode-ecosystem status` → `[ok] sin drift`, exit 0 (passed, observado).
- Git final: HEAD `1f57bca` sin commits nuevos; untracked solo `skills/ui-ux-master/` y el doc de evolución (passed, observado).
- `./scripts/qa-gate.sh --strict` → exit 0 (passed, observado en cierre).
- `verify.sh` + 182 tests: ejecutados por odd-worker tras el estado final (recibo en su SUMMARY); no re-ejecutados por el padre (diff solo docs, riesgo bajo).
- odd-verifier: abortado en 2 intentos por interrupción; los checks read-only se completaron inline por el padre con resultados observados.

## Progreso
- Estado: cerrado (verificado).
- Última tarea: T1 completada y verificada; doc de evolución actualizado a `estado: verificado`.
- Siguiente paso: usar la skill en la próxima petición de diseño; periodo de observación prudencial antes de dar la base por estable.
- Bloqueos: ninguno.
