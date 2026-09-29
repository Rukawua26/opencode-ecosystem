---
nombre: 2026-09-28-monitor-ejecucion-observable
fecha: 2026-09-28
estado: en_observacion
afecta: [docs, scripts]
fuente: propio
---

# Seguimiento observable del runner

## Por que
El usuario necesitaba ver donde se detiene una ejecucion y comparar tiempos;
el mapa muestra conexiones estaticas y el enlace de traza de Resumen abria
un panel en una pestaña oculta.

## Antes
La tarjeta en Resumen tenia estado/lease; la traza estaba en Actividad. No
se medía por separado la duración de la fase determinista.

## Despues
Vista En vivo con traza navegable, checkpoints acotados en `events` y metricas
agregadas de 30 dias en `/api/execution-metrics` (solo runner).

## Beneficio
Localizacion del ultimo hito observable y comparacion de tiempos por agente
sin nuevos procesos ni dependencias. No afirma visibilidad de sesiones ajenas.

## No regresion
- Estado previo recuperable del HEAD versionado; cambios existentes del usuario
  en frontend/tests se conservaron.
- Sin migracion de SQLite, sin stdout ni prompts en la nueva telemetria.
- Mapa, cola, contrato ODD, seguridad localhost y polling existente no cambian.
- Los contadores por componente del primer intento se retiraron: atribuian
  tareas a tipos ("agente") en vez de a nombres de agente.

## Verificacion
`python3 -m unittest discover -s control/tests`: 181 tests OK (1 skip opt-in);
7/7 pruebas de navegador sobre servidor temporal sin tocar el servicio instalado.
`python3 validate-skills.py skills`: 10 validas. `./opencode-ecosystem status`:
`[ok] sin drift`. `./verify.sh`: `[ok] verify verde`.
`scripts/qa-gate.sh --strict`: exit 0. `git diff --check`: limpio.
El test E2E contra el servicio instalado anterior fallo por 404 del endpoint
nuevo; se aislo el test, no se reinicio el servicio.

## Periodo prudencial
Observar varios ciclos reales del runner y comprobar que la vista no confunde
`waiting` con fallo. Si aparece anomalia, revertir solo los cambios de esta
feature con el diff respecto al HEAD, sin tocar modificaciones ajenas.

## Fuente (si aplica)
Implementacion propia sobre `control/runner.py`, `control/trace.py` y SQLite existente.
