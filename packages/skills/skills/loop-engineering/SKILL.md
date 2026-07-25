# Loop Engineering

Disena y ejecuta bucles controlados donde la IA itera hasta cumplir un objetivo verificable sin perder control humano.

## Cuando Usar

- Features con tests, build o checks definidos.
- Bugs donde la correccion puede requerir varios intentos.
- Implementaciones SDD que necesitan actuar, observar y corregir.
- Trabajo TDD o test-first.

## Trigger

Activa esta skill cuando:

- El usuario mencione loop, iterar, corregir hasta pasar, TDD o test-first.
- Exista una tarea con verificacion automatica clara.
- Un test, typecheck, lint o build falle despues de un cambio.

## Ciclo

### 1. Entiende

- Lee el objetivo, criterios de aceptacion y fuentes de verdad.
- Identifica el comando minimo que prueba la tarea actual.
- Define que significa PASS antes de tocar codigo.

### 2. Planifica

- Elige el cambio minimo correcto.
- Define maximo 3 iteraciones por tarea.
- Si aplica TDD, escribe primero el test esperado.

### 3. Actua

- Implementa solo la tarea actual.
- No refactorices fuera del alcance.
- No cambies contratos sin actualizar spec/plan.

### 4. Evalua

- Ejecuta la verificacion minima definida.
- Captura error exacto, archivo, linea y comando.
- Distingue fallo retryable de bloqueo real.

### 5. Ajusta

- Corrige solo la causa del fallo.
- Repite hasta PASS o 3 intentos.
- Si falla 3 veces, documenta bloqueante y escala al humano.

## TDD Integrado

Si se requiere TDD, ver las etapas RED/GREEN/TRIANGULATE/REFACTOR/VERIFY en la skill `tdd-workflow`.

## Condiciones De Salida

- PASS: verificacion relevante pasa y cambio coincide con spec.
- BLOCKED: 3 intentos fallidos, dependencia externa rota o criterio ambiguo.
- ESCALATE: cambio afecta runtime critico, contratos publicos o seguridad fuera del plan.

## Output Esperado

```txt
LOOP RESULT

Task: ...
Iterations: N/3
Verification: PASS/BLOCKED/ESCALATE
Command: ...
Evidence: ...
Next: ...
```
