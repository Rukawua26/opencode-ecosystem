# Token Economy: Hipotesis Y Medicion

Las estrategias del ecosistema pueden reducir contexto, coste o repeticiones,
pero no existe un porcentaje universal verificado. El efecto depende del modelo,
la tarea, el tamano del repositorio y la disciplina del flujo.

## Hipotesis

| Estrategia | Senal que debe mejorar |
|---|---|
| Subagentes con contexto acotado | Menos tokens de entrada por subtarea |
| Memoria estructurada | Menos historial bruto cargado |
| Skills bajo demanda | Menos contexto estatico por conversacion |
| Modelo ligero para tareas simples | Menor coste por mensaje |
| Compaction con prune | Menos crecimiento del contexto largo |

## Como Validarlas

1. Guarda una linea base con `opencode-metrics 7`.
2. Cambia una estrategia cada vez.
3. Mide durante un periodo comparable.
4. Compara tokens por mensaje, fallos, tiempo, compactaciones y loops.
5. Conserva el cambio solo si mejora el resultado neto.

El procedimiento detallado esta en [`measurement.md`](measurement.md).

## Configuracion Actual

```jsonc
{
  "subagent_depth": 1,
  "compaction": {
    "auto": true,
    "prune": true,
    "tail_turns": 6
  },
  "agent": {
    "explore": { "steps": 8 },
    "scout": { "steps": 8 }
  }
}
```
