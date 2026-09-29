---
name: supabase-apply-lite
description: Migracion, despliegue de Edge Function y verificacion en el proyecto remoto de Supabase. Usar cuando una peticion autorizada exija tocar el esquema o una funcion edge en el remoto y dejar evidencia verificable.
---

# supabase-apply-lite

1. **Autorizacion**: solo con peticion explicita del humano. Implementar un plan autoriza tocar codigo local; aplicar una migracion o desplegar una funcion edge son pasos aparte que se piden y se aprueban por separado. Lee el proposito del cambio, nunca credenciales ni tokens.

2. **Pre-flight read-only**: antes de escribir, `list_migrations` + `list_tables` (o `get_edge_function` si el cambio es una funcion) para fijar el estado actual: columnas, indices, politicas, `prosrc` de las funciones y cuerpos vigentes. Si el cuerpo remoto difiere del fichero (correcciones hechas a mano en el SQL editor), para y pregunta: no sobrescribas a ciegas.

3. **Aplicacion idempotente**: `apply_migration` con nombre descriptivo y cuerpo repetible (`begin; ... commit;`, `create or replace`, `add column if not exists`, bloques con guardian de existencia). Nada de credenciales, `drop` en cascada ni escritura de datos de usuario desde el agente.

4. **Verificacion read-only en el remoto**: relee lo creado con `execute_sql` (SELECT) o `list_tables` y contrastalo con lo esperado: nombres de funciones/politicas/indices, definiciones de constraint, y recuento de filas sensibles antes y despues. Vuelve a leer las politicas completas; no basta con que la migracion devuelva exito.

5. **Edge Function**: `get_edge_function` para confirmar el codigo activo es identico al local, `list_edge_functions` para estado `ACTIVE` y `verify_jwt`. Tras `deploy_edge_function`, repite `get_edge_function`: deploy exitoso no prueba que el contenido sea el correcto.

6. **Smoke test HTTP**: una llamada real (`curl`/`fetch`) contra `get_project_url` que ejerce el camino completo, validando status y cuerpo JSON. Si la llamada debia ser rechazada, comprueba ademas que no hubo efectos laterales (fila o registro esperado = 0 nuevas). Tras desplegar, `query_logs` si necesitas confirmar la invocacion.

7. **Evidencia y cierre**: registra fecha, project_ref, herramienta, comando y resultado exacto en el documento `odd/tasks/<feature>.md`. Nunca pegues `service_role`, claves JWT ni `.env`. Si algo no cuadra, revierte con una migracion compensatoria o restaura el cuerpo anterior antes de continuar.
