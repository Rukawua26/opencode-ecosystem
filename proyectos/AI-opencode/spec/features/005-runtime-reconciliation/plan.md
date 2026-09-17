# 005-runtime-reconciliation - Plan

1. Resolver OpenCode por override, PATH y fallback; impedir pins invalidos.
2. Hacer que `verify.sh` use el doctor completo.
3. Eliminar declaraciones de runtime inexistente de `AGENTS.md`, conservando
   politicas activas en forma compacta y rutas reales; corregir la direccion
   publish/sync en `AGENTS.md` y README.
4. Reconciliar specs historicas 001/002 sin reescribir su evidencia.
5. Pinear la version y verificar doctor, config, contexto, timers y drift.

No se ejecuta `publish` ni `sync`: ningun fichero gestionado de la configuracion
cambia en esta feature.
