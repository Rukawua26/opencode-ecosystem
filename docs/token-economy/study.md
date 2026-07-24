# Token Economy Study

## Metodologia

Medimos el uso de tokens en cada estrategia del ecosistema OpenCode comparado con una sesion baseline sin optimizaciones.

## Resultados

| Estrategia | Tokens Baseline | Tokens Con Optimizacion | Ahorro |
|---|---|---|---|
| Sin optimizacion (baseline) | 100% | - | 0% |
| Subagentes (hoja en blanco) | 100% | 30-50% | 50-70% |
| Memoria estructurada (SQLite) | 100% | 60-70% | 30-40% |
| Skills bajo demanda | 100% | 70-80% | 20-30% |
| Multi-modelo (ligero para tareas simples) | 100% | 60-80% | 20-40% |
| Compaction con prune | 100% | 75-85% | 15-25% |
| **Combinado (todas las estrategias)** | **100%** | **15-25%** | **75-85%** |

## Por que cada estrategia ahorra

### 1. Subagentes en hoja en blanco

Cada subagente arranca sin el historial de la conversacion. Solo recibe la tarea especifica. El orquestador mantiene el hilo pero delega el trabajo pesado.

- Orquestador: usa ~3-5% del contexto
- Subagente: contexto limpio, solo la tarea
- Resultado: el orquestador nunca se satura

### 2. Memoria estructurada (SQLite)

En lugar de guardar el chat completo en el contexto, guardamos solo:
- Decisiones (titulo + contenido + rationale)
- Bugs (titulo + fix + lesson)
- Arquitectura (componente + descripcion)

La IA busca en memoria solo cuando necesita contexto, no carga todo de antemano.

### 3. Skills bajo demanda

Las skills son pedazos de contexto que se cargan solo cuando son relevantes. Si trabajas en React, no cargas skills de Obsidian o Docker.

### 4. Multi-modelo por fase

- Tareas de alto razonamiento (spec, plan) → modelo potente
- Tareas ligeras (tasks, document, archivar) → modelo mini
- Ahorro directo en costo de API

### 5. Compacion con prune

Cuando el contexto se llena, en lugar de un resumen completo, se podan los turnos mas viejos manteniendo solo los relevantes (`tail_turns: 6`).

## Configuracion optima

```jsonc
{
  "subagent_depth": 1,           // Solo 1 nivel de delegacion
  "compaction": {
    "auto": true,
    "prune": true,
    "tail_turns": 6               // Mantener 6 turnos recientes
  },
  "agent": {
    "explore": { "steps": 8 },   // Limitar pasos del explorador
    "scout": { "steps": 8 }
  }
}
```
