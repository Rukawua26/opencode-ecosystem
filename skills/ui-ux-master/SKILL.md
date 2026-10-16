---
name: ui-ux-master
description: Diseno y calidad visual de interfaces web. Usar cuando el usuario pida disenar, construir, auditar o refinar componentes, landing pages, dashboards o interfaces web en React, Vue, HTML/CSS o Tailwind, y para definir tokens, paletas, tipografia o accesibilidad.
---

# ui-ux-master

## Flujo de trabajo
1. Entiende el contexto: producto, publico, tarea principal y stack. Si el proyecto ya tiene marca, tokens o componentes, respetalos antes de proponer otra estetica.
2. Define la direccion visual antes de codificar: concepto estetico claro (ej. neobrutalismo, minimalismo suizo, dark lujo, industrial B/N), paleta con roles explicitos (superficie, texto, borde, estado, acento) y tipografia con caracter (display con presencia + lectura limpia). Evita componentes genericos estilo plantilla.
3. Disena la experiencia completa: jerarquia, navegacion, contenido realista, adaptacion a movil, escritorio y teclado; estados de carga, vacio, error, deshabilitado y foco visible donde correspondan, no por obligacion.
4. Implementa con el sistema existente: reutiliza componentes y tokens del proyecto; crea solo los que falten, sin imponer Tailwind, React ni dependencias nuevas. Escalas rem y espaciado en rejilla 4px/8px cuando definas tokens nuevos.
5. Comprueba el resultado: revisa la interfaz renderizada en varios tamanos, interacciones, foco de teclado y contraste medido. No declares cumplimiento WCAG sin verificarlo.

## Interaccion y semantica (comprobar siempre)
- Elemento nativo antes que `div` con `onClick`: `button`, `a`, `label` asociada
  con `htmlFor`/`id`; superposiciones con `dialog`.
- Overlays/modal: rol `dialog`, `aria-modal`, foco inicial y atrapado, cierre con
  `Escape`; anuncia el cambio de paso (`aria-live`).
- Progreso y seleccion: `role="progressbar"` con valor, `aria-pressed` o
  `tablist`/`tab` con `aria-selected`; nunca solo color.
- Teclado real y `:focus-visible`, no solo `hover`. Errores tipicos: comentarios
  `<!-- -->` dentro de JSX, interactivo sin teclado, input sin `label` asociada.
- Contraste, movil y `alt` se miden con `web-quality-lite`; no los dupliques.

## Modos (intenciones)
- Disenar o construir (predeterminado): identidad visual + implementacion, proporcionales a la peticion.
- Definir sistema: tokens, escalas y guias de estilo cuando el proyecto lo necesita; sin codigo UI innecesario.
- Auditar: evalua jerarquia, contraste, consistencia, semantica y teclado; entrega hallazgos priorizados primero y no refactorices sin permiso.

## Regla de proporcionalidad
Una peticion pequena produce una respuesta pequena; una pagina completa incluye identidad, tokens, implementacion y comprobaciones. Nunca exijas ficha de marca, tokens o estados que no vienen al caso.
