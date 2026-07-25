# Medicion de ahorro de tokens

Las cifras de ahorro son hipotesis hasta compararlas con metricas reales.

## Linea base

Antes de cambiar el flujo, ejecuta:

```bash
opencode-metrics 7 > baseline.json
```

No publiques `baseline.json` si contiene nombres de modelos o datos que no
quieras compartir.

## Periodo de prueba

Durante siete dias:

1. Declara `mode:chat`, `mode:operate`, `mode:build` o `mode:verify` cuando aporte contexto.
2. Usa una plantilla de `prompts` solo para tareas recurrentes.
3. Usa Context7 cuando una API externa pueda estar desactualizada.
4. Genera diagramas solo cuando reemplacen una explicacion larga.
5. No habilites conectores de negocio durante la prueba.

## Comparacion

Al terminar:

```bash
opencode-metrics 7 > experiment.json
```

Compara:

- `input_tokens / messages`
- `output_tokens / messages`
- `failures / messages`
- `compactions / sessions`
- costo por modelo
- delegaciones por sesion

## Decision

Conserva una optimizacion si reduce tokens o fallos sin aumentar el tiempo neto.
No agregues `memory-lite` mientras el memory adapter nativo funcione. Activa un
conector de negocio solo ante una necesidad concreta y midelo durante 30 dias.
