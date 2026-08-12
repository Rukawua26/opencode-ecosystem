# Plan: Safe Installer Sync and Public Documentation

## Enfoque

1. Reducir el README raiz a instalacion, novedades, componentes activos,
   arquitectura real, verificacion y enlaces vigentes.
2. Endurecer `check-docs.js` para rechazar contenido historico o no medido en la
   portada publica.
3. Generar un manifiesto de destinos gestionados con dos raices logicas:
   `opencode/` y `skills/`.
4. En modo sync, respaldar cada destino antes de sobrescribir y retirar solo las
   entradas del manifiesto anterior ausentes del actual.
5. Escribir el manifiesto nuevo de forma atomica al terminar la instalacion.
6. Replicar el contrato en PowerShell y ampliar ambos tests de instalacion.
7. Agregar un eval Node sin dependencias que valide JSON y esquema con los modelos
   locales fijados por el router. Mantenerlo fuera del workflow CI.
8. Integrar primero las mejoras locales de guardrails y metricas con tests de
   comportamiento para no degradarlas durante sync.
9. Ejecutar sync local tras pasar tests para llevar el runtime de 1.8.0 a 1.9.0
   sin tocar la configuracion principal personalizada.

## Decisiones

- `--sync` es opt-in; no se cambia la semantica conservadora por defecto.
- La primera sincronizacion no poda porque no existe evidencia fiable de
  propiedad sobre archivos antiguos.
- El manifiesto contiene rutas relativas, no rutas absolutas, para evitar acoplar
  una instalacion a un HOME concreto.
- `opencode.jsonc` queda fuera del manifiesto sincronizable.
- El eval mide estructura, no calidad semantica ni proveedores comerciales.

## Archivos

| Archivo | Cambio |
|---|---|
| `README.md` | Reescritura de portada publica actual |
| `tools/scripts/check-docs.js` | Contratos de README vigentes |
| `install.sh` | `--sync`, manifiesto, backup y pruning seguro |
| `install.ps1` | Paridad `-Sync` |
| `tests/install.test.sh` | Casos sync y manifest |
| `tests/install.test.ps1` | Casos sync y manifest en Windows |
| `tools/evals/local-model-structure.js` | Eval manual JSON/esquema |
| `package.json` | Script opt-in del eval |
| `docs/architecture/installer-sync.mmd` | Flujo de sync documentado |

## Riesgos y Mitigaciones

- Manifest manipulado: validar prefijo y rechazar traversal antes de resolver.
- Perdida de customizaciones: no borrar rutas desconocidas y respaldar todo
  destino gestionado que cambie.
- Acumulacion de backups: conservar solo las ultimas 10 ejecuciones sync y
  documentar restauracion manual.
- Fallo parcial: escribir el manifiesto solo despues de copiar, instalar y
  verificar correctamente.
- Costo local: eval manual, dataset pequeno y sin ejecucion automatica.

## Verificacion

- `bash -n install.sh tests/install.test.sh`
- `npm run test:install`
- `npm run test:install:windows` en CI Windows
- `npm run check-docs`
- `npm run lint`
- `npm test`
- `npm run test:router`
- `node --test packages/memory-adapter/tests/*.test.js`
- `npm audit`
- Organic RDD segun tier detectado
