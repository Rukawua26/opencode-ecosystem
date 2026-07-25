# Accessibility Audit

Auditoria estatica de accesibilidad para cambios frontend. Solo chequeos que se pueden verificar sin browser ni screen reader.

## Cuando Usar

- Cambios en componentes React, HTML, CSS o themes.
- Antes de cerrar una feature frontend.
- Como paso condicional dentro de verification-loop.

## Trigger

Activa esta skill cuando el diff contenga `.tsx`, `.jsx`, `.html` o `.css`.

## Checklist

### 1. Semantic HTML
- `<div>` con comportamiento interactivo usa `<button>`, `<a>` o role ARIA
- `<img>` siempre tiene `alt` (descriptivo o `alt=""` si decorativo)
- Headings siguen jerarquia (h1 → h2 → h3) sin saltos

### 2. Keyboard Navigation
- Elementos con `onClick` tienen `onKeyDown` equivalente (Enter/Space)
- `tabIndex` usado solo cuando necesario (0 o -1, nunca positivos)
- Focus visible (no `outline: none` sin alternativa)

### 3. ARIA Integrity
- Todo `aria-labelledby` / `aria-describedby` apunta a ID existente
- Roles ARIA no duplican semantica nativa (no `role="button"` en `<button>`)
- Estados ARIA (`aria-expanded`, `aria-selected`) se actualizan en el codigo

### 4. Color Contrast (solo si valores en codigo)
- Si hay colores inline o en theme vars, contrast ratio ≥ 4.5:1 (texto) / 3:1 (large text)
- No usar solo color para transmitir informacion (agregar icono o texto)

## Output Esperado

```
A11Y AUDIT: PASS/FAIL

Semantic:   OK / X issues
Keyboard:   OK / X issues
ARIA:       OK / X issues
Contrast:   OK / X issues (SKIP si solo tailwind/tokens)

Issues: archivo:linea → WCAG criterio → fix sugerido
```

Si hay issues CRITICAL: corregir antes de cerrar la feature.