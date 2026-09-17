# 011-routing-proporcional-rdd — Verify

- Fecha: 2026-09-14
- Verificador: subagente `sdd-verify` (contexto fresco, read-only, primera verificación independiente de lote)

## Resultado: SIN HALLAZGOS BLOQUEANTES

| Criterio | Resultado | Evidencia |
|---|---|---|
| Pin `sdd-implement` → luna + low | ✓ | `configs/opencode.jsonc:81-82` (`model` + `variant`, y modelo declarado en `provider.openai.models`) |
| `sdd-verify` hereda sesión (sin pin) | ✓ | `configs/opencode.jsonc:87-93`: solo mode/hidden/description/prompt/permission |
| Ciclo RDD en `/implement-spec` | ✓ | `commands/implement-spec.md:7-8`: sdd-verify UNA vez, máx. 1 corrección acotada, segundo rechazo = STOP, sin loop-until-clean, frontmatter intacto |
| Fuera de alcance respetado | ✓ | Sin `profiles*`, sin skill nueva (9 skills), sin pin en sdd-verify |
| Doc de evolución fiel | ✓ | antes/después coinciden con estado real; No-regresión refleja los DEJAMOS de la spec |

## SUGGESTION (resuelta en el mismo lote)
- `verify.md` no existía al momento de la verificación — esperable: la verificación independiente precede a su registro. Registrado con este documento.

## Prueba dogfood del flujo SDD (señal de estabilidad)
- `/spec` (simulado por orquestador): preflight agrupado ejecutado con tool `question` (modo Interactivo + verificación al cerrar lote). ✓
- `/implement-spec`: T1 y T2 delegadas a `sdd-implement` con contrato de resultado. ✓
- **Fallo detectado y corregido durante la prueba** (valida el gate): intento 1 de T2 devolvió `task_result` vacío y no modificó el fichero; el gate lo detectó (status ausente, artefacto no encontrado) y el reintento 2 con feedback correctivo pasó. Sin loop-until-clean (1 re-run).
- **Error propio corregido**: el backup por fichero de commands generaba `.bak-*` dentro de `$CFG/commands/` y producía drift permanente en `status`; corregido con `diff -rq -x '*.bak-*'` en el CLI.
- `/verify-spec` (simulado): `sdd-verify` respondió con evidencia por criterio y `Sin hallazgos bloqueantes`. ✓

## Pendiente del humano
- ~~Reiniciar OpenCode para que el pin luna+low de `sdd-implement` surta efecto~~ RESUELTO (2026-09-14): verificado con `opencode debug agent sdd-implement` → `openai/gpt-5.6-luna` + `variant: low`; `sdd-verify` hereda sesión.
- Periodo de observación hasta 2026-09-28.

## Hallazgo menor (resuelto 2026-09-14)
- `spec/constitution/` referenciada en AGENTS.md no existía → resuelto con lectura condicional: AGENTS.md línea 12 ahora lee `working-agreement.md` y `tech-stack.md` **solo si existen**; siempre lee `spec.md`/`plan.md`/`tasks.md`. No se crearon archivos vacíos (YAGNI).
