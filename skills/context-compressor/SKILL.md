---
name: context-compressor
description: Contexto grande, CONTEXT_MAP.md y presion de tokens o RAM. Usar para mapear entrypoints, exports y estado global sin leer todo el repo.
---

# context-compressor
Entrega en chat un mapa con exports publicos, entrypoints, estado global y nombres de variables de entorno.
Nunca incluyas valores de variables ni secretos. Omite `node_modules`, `dist`, `.git` y limita el mapa a 100 lineas.
Escribe `CONTEXT_MAP.md` solo tras consentimiento explicito del usuario.
