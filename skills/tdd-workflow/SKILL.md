# TDD Workflow

Workflow de desarrollo guiado por tests para features nuevas.

## Cuando Usar

Cuando pidas explicitamente trabajar con TDD o "test-first".

No activar automaticamente; es opcional.

## Flujo

### 1. Analisis
- Entender el requerimiento completamente.
- Identificar el comportamiento esperado.
- Definir casos de borde y errores.

### 2. RED - Escribir Test
- Escribir test que describe el comportamiento deseado.
- El test debe fallar (aun no hay implementacion).

### 3. GREEN - Implementacion Minima
- Escribir el codigo minimo necesario para que el test pase.
- No optimizar ni refactorizar aun.
- Solo hacer que pase.

### 4. REFACTOR
- Mejorar la implementacion.
- Mantener tests pasando.
- Eliminar duplicacion.
- Mejorar nombres.

### 5. VERIFY
- Ejecutar test suite completa.
- Verificar que no hay regresiones.
- Verificar cobertura minima (80%+).

## Output Esperado

```
TDD CYCLE COMPLETE

Fase: RED / GREEN / REFACTOR
Tests: X/Y passed
Cobertura: Z%
Regresiones: 0
Proximo paso: [siguiente test / feature completa]
```
