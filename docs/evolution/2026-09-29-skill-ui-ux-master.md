---
nombre: 2026-09-29-skill-ui-ux-master
fecha: 2026-09-29
estado: verificado
afecta: [skills, docs]
fuente: propio
---

# Skill ui-ux-master

## Por que
El ecosistema no tenia una skill de diseno visual. Se necesitaba una guia para interfaces web completas, con direccion visual, usabilidad y comprobacion practica de accesibilidad.

## Antes
No habia una skill de diseno en `skills/` ni en el runtime global.

## Despues
Se incorpora una skill unica con modos como intenciones: disenar o construir, definir sistema y auditar. Incluye proporcionalidad, respeto por componentes existentes, estados pertinentes y verificacion visual, de teclado y contraste.

La decision evita skills separadas, que perderian contexto, y evita un monolito rigido que sobredimensionaria peticiones pequenas. La base externa frontend-design + UI/UX Pro Max se adapto con verificacion del resultado, uso del sistema existente y accesibilidad practica verificada.

## Beneficio
La skill orienta respuestas proporcionales y reutilizables para interfaces web sin imponer framework ni dependencias, y evita declarar cumplimiento WCAG sin comprobacion.

## No regresion
- La base reversible estaba limpia en Git para `skills/`, sin skill de diseno previa.
- No se modifican las skills existentes ni su descubrimiento.
- El cambio no toca configuracion, memoria ni trabajo ajeno.

## Verificacion
- `./opencode-ecosystem status` antes: `[ok] sin drift`.
- `python3 validate-skills.py skills`: correcto.
- `./opencode-ecosystem sync --apply`: correcto.
- Presencia verificada en `/home/miguel/.config/opencode/skills/ui-ux-master/SKILL.md`.
- `./opencode-ecosystem status` despues: `[ok] sin drift`.

## Periodo prudencial
- Mantener la base versionada y reversible hasta confirmar que la skill permanece descubrible y el status no presenta drift.
- Si falla la validacion, el sync o el descubrimiento, eliminar la skill nueva y repetir la verificacion de status.

## Fuente (si aplica)
Base externa frontend-design + UI/UX Pro Max, adaptada a las decisiones aceptadas del documento ODD.
