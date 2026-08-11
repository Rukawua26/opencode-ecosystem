# Tasks — Incremental Memory Event Export

- [x] T1 Añadir serialización y merge determinista de estados por `event_id`.
- [x] T2 Implementar listado de eventos nuevos/modificados antes del límite final.
- [x] T3 Añadir pruebas del adapter para límite e ID con hash actualizado.
- [x] T4 Implementar `export-events --state` con rutas separadas y escritura atómica.
- [x] T5 Añadir pruebas CLI de primera ejecución, idempotencia, corrupción y privacidad.
- [x] T6 Actualizar README y diagrama de arquitectura.
- [x] T7 Ejecutar verificación completa y corregir regresiones.
- [x] T7a Corregir estabilidad de IDs, aliases de ruta, atomicidad, lock y límite por bytes hallados en review.
- [x] T7b Añadir recuperación de locks muertos y límite simétrico de 64 MiB antes de escribir.
- [x] T8 Completar Organic RDD Tier 3 y `verify.md`.
- [x] T9 Archivar el ciclo SDD aprobado.
