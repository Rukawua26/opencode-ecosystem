# 006-skills-conformance - Plan

1. Corregir las cinco skills en `~/opencode-ecosystem/skills/`.
2. Validar ese contenido en un HOME temporal con la ruta plural documentada.
3. Actualizar managed_list/status/sync/publish para `$CFG/skills`.
4. Aplicar sync, confirmar descubrimiento plural y retirar los ficheros
   gestionados de la ruta singular.
5. Eliminar el indice manual y actualizar AGENTS.md/README.
6. Verificar nombres, descripciones, unicidad, config, drift y piso de contexto.

La fuente del ecosistema permite reconstruir la ruta activa si la migracion
falla; no se elimina contenido personal desconocido.
