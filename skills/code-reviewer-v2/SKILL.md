# Code Reviewer V2

Revision estructurada enfocada en bugs, regresiones, seguridad, performance y cobertura, no preferencias de estilo.

## Cuando Usar

- Despues de implementar una feature significativa.
- Antes de PR o deploy.
- Cuando un cambio toque runtime critico, seguridad, datos o contratos publicos.
- Como rol Verificador en flujo multiagente.

## Trigger

Activa esta skill cuando:

- El usuario pida review.
- Haya cambios en `core/`, `server/`, `api`, auth, config o infra.
- El cambio incluya migraciones, contratos, riesgo financiero, nuevos endpoints, file uploads o cambios en integraciones externas.

## Checklist

### 1. Correctness

- El cambio cumple spec/plan/tasks.
- No agrega comportamiento fuera del alcance.
- Maneja casos borde y errores esperados.

### 2. Seguridad

- No filtra secretos ni datos sensibles.
- Valida inputs externos.
- No debilita auth, permisos, CORS, CSP o rate limits.

### 3. Runtime / Performance

- No introduce loops no acotados, polling agresivo o retries no idempotentes.
- No degrada paths criticos.
- Mantiene separacion de modos/entornos.

### 4. Mantenibilidad

- Cambio minimo y localizado.
- Nombres y contratos reales existen.
- No hay refactor oportunista fuera del alcance.

### 5. Tests / Verificacion

- Tests cubren comportamiento nuevo o bug corregido.
- Build/typecheck/lint pasan segun tech-stack.md.
- Fallos quedan reportados, no ocultos.

## Output Esperado

Findings ordenados por leverage (impact ÷ esfuerzo × confianza):

```txt
FINDINGS

| # | Archivo | Finding | Categoria | Severidad | Leverage | Fix |
|---|---------|---------|-----------|-----------|----------|-----|

Rejected:
- [ID] finding - razon (no volver a reportar)

Residual risk / Verification gaps:
- ...
```
