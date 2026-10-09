---
name: web-quality-lite
description: Estandar de calidad web de 20 puntos (legal, cookies, HTTPS, SEO, accesibilidad, rendimiento, conversion y medicion). Usar cuando se inicie, audite o entregue un proyecto web para decidir que criterios aplican y comprobar evidencias antes de cerrar.
---

# web-quality-lite

## Cuando entra
- Al iniciar un proyecto web: define que criterios **aplican** antes de construir.
- Antes de entregar: comprueba los aplicables con evidencia real.
- No se ejecuta por defecto; se invoca por nombre o se aplica al trabajar en webs.

## Estados de cada criterio
- `verificado` — con evidencia concreta (archivo, salida de comando, medida).
- `pendiente` — aplica pero falta por hacer.
- `no aplicable` — con motivo corto (ej. panel privado sin SEO).
- `revision humana` — legal/textos/contenido que el agente no certifica.

Nunca declares un punto verificado sin evidencia ni "20/20" sin comprobarlo.
Nunca fuerces un criterio cuando no aplica: el valor es la honestidad, no la marca.

## Los 20 criterios, agrupados
1. **Legal y privacidad** (revision humana del contenido, el texto NO lo redacta el agente)
   - Aviso legal
   - Politica de privacidad
   - Aviso de cookies (solo si hay cookies no tecnicas)
2. **Seguridad basica**
   - Forzar HTTPS (redireccion + HSTS en produccion)
   - Formularios protegidos contra spam (honeypot/captcha/rate-limit)
3. **SEO e identidad** (solo si la web es publica)
   - Meta titulos y descripciones por pagina
   - Datos estructurados (schema.org acorde al tipo de contenido)
   - Sitemap y robots.txt
   - Ficha de Google (solo negocios elegibles; `no aplicable` si no)
   - Favicon
4. **Accesibilidad y experiencia**
   - Texto alternativo en imagenes con significado
   - Contraste de colores medido (complementa `ui-ux-master`, no lo sustituye)
   - Se ve bien en movil (comprobado en vista estrecha real)
   - Pagina 404 personalizada
   - Enlaces rotos arreglados
5. **Rendimiento**
   - Imagenes comprimidas y con dimensiones
   - Velocidad de carga razonable (medir, no asumir)
6. **Conversion y medicion** (decision del proyecto, nunca instalar sin autorizacion)
   - Boton de WhatsApp visible (si forma parte del negocio)
   - Analitica instalada (si el proyectos la quiere y con aviso de cookies)
   - Una llamada a la accion principal clara (no prohibir acciones secundarias)

## Regla extra: seguridad del lado del stack
Los 20 puntos dejan fuera lo interno. Anade siempre: autenticacion, permisos
(RLS/autorizacion por defecto denegada), secretos fuera del bundle y validacion
de entradas. Para probar seguridad en vivo, ZAP va aparte (ver `docs/zap-mcp.md`
del ecosistema) y solo con autorizacion.

## Regla de proporcionalidad
Landing: revisados los criterios visibles. Web app con login: enfatiza seguridad
y formularios. Proyecto interno sin publico: legal/SEO suelen ser `no aplicable`.
Un cambio pequeno no vuelve a auditar los 20: solo lo que el cambio toca.

## Entrega
Termina con una tabla corta: criterio, estado, evidencia o motivo. Los
`pendiente` y los `revision humana` se listan para que el humano decida.
