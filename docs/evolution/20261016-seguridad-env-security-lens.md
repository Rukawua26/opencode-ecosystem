---
nombre: 20261016-seguridad-env-security-lens
fecha: 2026-10-16
estado: aplicado
afecta: [skills, configs, docs]
fuente: propio
---

# Seguridad: cerrar lectura de .env y añadir security-lens

## Por que
Auditoria de 2026-10-15: en `configs/opencode.jsonc`, la deny-list de `read`
no incluia `**/.env*` (solo `edit` lo denegaba), por lo que un agente podia
leer un `.env`. Ademas `**/secrets/*` solo cubre un nivel. El dominio de
seguridad solo tenia revision por patrones fijos (`qa-gate`, que se declara
"no es SAST") y no existia una lente de revision de seguridad del diff.

## Antes
- `read` deniega: `~/.ssh`, `*.pem`, `*.key`, aws/gh/credentials, `secrets/*`, `*.p12/pfx`.
- `edit` deniega ademas `**/.env*`.
- 13 skills; las 4R son risk, resilience, reliability, readability.

## Despues
- `read` deniega tambien `**/.env*` y `**/secrets/**`.
- Nueva skill `security-lens` (lente 4R, informa y nunca bloquea): barrido
  acotado al diff para inyeccion, deserializacion, HTML sin escapar, TLS/CORS
  abiertos, SQL o rutas construidas con datos externos, y revision de authz.
- README actualizado a 14 skills y 5 lentes.

## Beneficio
- Cierra una lectura no prevista de secretos sin tocar el resto de reglas.
- Da a la revision de seguridad un criterio propio sin crear agentes nuevos
  (coste 0 al arranque).

## No regresion
- Reglas previas intactas; solo se añaden dos entradas `deny` en `read`.
- Base reversible: commit `93b7d56` (configuracion y skills previas).
- Sin cambios en permisos de `odd-worker` ni `odd-verifier`.
- `.env.example` tambien queda denegado en lectura: es conservador a proposito.

## Verificacion
- `python3 validate-skills.py skills` -> `[ok] 14 skills valid`.
- `./opencode-ecosystem sync --apply` tras auditar que el drift era solo las
  dos reglas y la skill nueva; luego `status` -> `[ok] sin drift`.
- `opencode debug config` muestra `**/.env*` y `**/secrets/**` en `read` y `edit`
  (solo lineas de reglas, sin volcar otros valores).
- `python3 -m unittest discover -s control/tests` -> 342 tests OK, 1 skipped.
- `scripts/qa-gate.sh --strict` -> rc 0. `./verify.sh` -> verde.
- Limite: la configuracion efectiva confirma la regla, pero no se ha probado
  una lectura real denegada por un agente.

## Periodo prudencial
- Observar 2 semanas o 3 revisiones con `security-lens` antes de decidir si
  se crea `security-verifier` (subagente read-only, fase 2, no aplicada).
- Rollback: `git checkout 93b7d56 -- configs/opencode.jsonc`, `rm -r skills/security-lens`,
  `./opencode-ecosystem sync --apply`.

## Fuente (si aplica)
Propio.
