---
name: debug-bugs
description: Diagnose and fix software bugs through reproduction, evidence gathering, root-cause analysis, minimal changes, and regression verification.
---

# Debug: Cazar Bugs Imposibles

Protocolo estructurado para bugs intermitentes/complejos.

## Cuando Usar

Bug intermitente, race condition, error no reproducible, fallo en CI que no falla local, o bug que aparece solo en producción.

## Trigger

Activa esta skill cuando:

- El error sea intermitente, no reproducible o dependiente de timing/concurrencia.
- CI falle pero local pase, o local falle pero CI pase.
- El usuario pegue un traceback/log y pida diagnostico de causa raiz.
- La solucion probable requiera hipotesis, reproduccion minima y validacion.

## Protocolo

### 1. Aislar al mínimo
- Reducir el escenario al mínimo eliminando variables (input fijo, sin red, sin archivos externos).
- Reproducir en `sandbox_exec` para entorno limpio y aislado.

### 2. Registrar todo antes de cambiar
- Capturar logs completos, estado del sistema, traza del error.
- Usar `tool_output` completo, evitar truncado.

### 3. Sospechar concurrencia primero
- Si el error es intermitente → probablemente race condition.
- Revisar: async/await faltantes, mutabilidad compartida sin locks, timers, eventos, callbacks sin manejo de errores.

### 4. Una hipótesis por vez
- Escribir test mínimo que confirme o refute la hipótesis.
- No cambiar más de una variable entre intentos.

### 5. Reparación conservadora
- Arreglar la causa raíz, no el síntoma.
- Validar: el bug no se reproduce + tests existentes siguen pasando.

## Output Esperado

```
HIPOTESIS: ...
PRUEBA: <tool/comando>
RESULTADO: confirmada/refutada
CAUSA RAÍZ: ...
SOLUCIÓN: <cambio mínimo>
VALIDACIÓN: bug no reproducible + tests OK
```

> **Nota**: Incluye verificación post-fix (antes skill `verification-loop` separada): tras la solución, ejecuta tests enfocados, diffs y criterios de aceptación antes de reportar completado.
