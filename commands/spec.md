---
description: Inicia una feature SDD: preflight, indagacion y spec.md. Sin codigo.
---

Flujo SDD para la feature "$ARGUMENTS". Si no hay nombre, pregunta el nombre y el problema a resolver antes de avanzar.

REGLAS:
- Prohibido escribir o modificar codigo de produccion en este comando.
- Artefactos en `spec/features/NNN-nombre/` de este proyecto; detecta el siguiente numero NNN libre.

TAREAS:
1. Carga la skill `ultraplan-lite` y ejecuta su preflight: una sola pregunta agrupada (modo interactivo/auto + confirmacion de alcance + verificacion esperada). Detente y espera la respuesta.
2. Indagacion: haz las preguntas concretas que falten para cerrar vacios (contratos de entrada/salida, manejo de errores, limites). Una a la vez; STOP tras cada pregunta.
3. Redacta `spec/features/NNN-nombre/spec.md` con objetivos, alcance, criterios de aceptacion y fuera de alcance.
4. Reporta la ruta de la spec y espera aprobacion antes de `/plan-spec`.
