---
nombre: 20261015-ui-ux-master-interaccion
fecha: 2026-10-15
estado: aplicado
afecta: [skills]
fuente: propio
---

# ui-ux-master: semantica de interaccion y teclado

## Por que
La skill `ui-ux-master` cubria direccion visual, tokens, estados y contraste, pero
no exigia semantica de interaccion ni accesibilidad de teclado/ARIA, el punto
donde mas fallan las interfaces generadas por IA. Evidencia real (dos fragmentos
aportados por el usuario, 2026-10-15, HTML/React):
- Landing con tarjetas de paso como `div` con `cursor-pointer`: sin rol, sin
  teclado, sin `aria-selected`.
- Wizard React con comentarios `<!-- -->` dentro de JSX (invalido), overlay sin
  `role="dialog"` ni `aria-modal`, barra de progreso sin `role="progressbar"`,
  `label` sin `htmlFor`/`id` y botones de seleccion sin `aria-pressed`.
El resto (contraste medido, movil, `alt`) ya lo cubre `web-quality-lite`.

## Antes
Pasos 1-5 y modos sin requisitos de semantica; el modo Auditar solo miraba
jerarquia, contraste y consistencia.

## Despues
Nueva seccion "Interaccion y semantica (comprobar siempre)" con 5 reglas
(elemento nativo, overlays/modal, progreso/seleccion, teclado real y errores
tipicos) y referencia a `web-quality-lite` para contraste/movil/alt. El modo
Auditar incluye semantica y teclado.

## Beneficio
Cierra el hueco de accesibilidad de interaccion sin imponer stack ni añadir
componentes; evita duplicar criterios de `web-quality-lite`. Esperado: menos
defectos de teclado/ARIA en UI generada. No medido aun.

## No regresion
- Version anterior recuperable en Git: commit `8b2ca9a`, blob
  `3108d27d2e6854c8a477fa250829277933568fdc`.
- Se conservan description, nombre, modos y regla de proporcionalidad; sin
  acentos en el contenido; sin Tailwind/React obligatorios.
- Sin dependencias nuevas ni cambios en `web-quality-lite`.

## Verificacion
- `python3 validate-skills.py skills` -> `[ok] 13 skills valid` (rc 0).
- `./opencode-ecosystem sync --apply` -> `[ok] sync aplicado`; `status` ->
  `[ok] sin drift`; `diff` fuente/runtime -> identico.
- `python3 -m unittest discover -s control/tests` -> 340 tests OK, 1 skipped.
- `scripts/qa-gate.sh --strict` -> rc 0. `./verify.sh` -> verde.

## Periodo prudencial
- Observar ~2 semanas o 3 usos reales de la skill.
- Estable: los cambios de UI dejan de reintroducir `div` interactivo, JSX con
  comentarios HTML o modal sin `dialog` cuando el agente usa la skill.
- Rollback: `git checkout 8b2ca9a -- skills/ui-ux-master/SKILL.md` y
  `./opencode-ecosystem sync --apply`.

## Fuente (si aplica)
Propio. Los fragmentos del usuario se usaron como evidencia de defectos, no como
codigo a copiar.
