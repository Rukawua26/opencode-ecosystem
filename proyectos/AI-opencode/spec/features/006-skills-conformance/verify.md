# 006-skills-conformance - Verify (2026-09-11)

## Evidencia

1. **Contrato**: cinco nombres cumplen `^[a-z0-9]+(-[a-z0-9]+)*$`, coinciden
   con su directorio y sus descriptions tienen 1-1024 caracteres, explican que
   hacen y contienen `Usar` como trigger.
2. **Prueba aislada**: un HOME/XDG_CONFIG_HOME temporal con la ruta oficial
   `~/.config/opencode/skills/` cargo exactamente las cinco skills propias.
3. **Runtime**: `opencode debug skill` carga una sola copia de cada skill desde
   `~/.config/opencode/skills/<name>/SKILL.md`, mas `customize-opencode` integrada.
4. **Indice**: no existe ningun `SKILL_INDEX.md`; AGENTS.md usa la tool nativa
   `skill` y no obliga a una lectura de inicio.
5. **Integridad**: `opencode debug config` valido, `verify.sh` verde, timers
   activos y `opencode-ecosystem status` sin drift.
6. **Contexto**: piso fijo ~2819 tokens, menor que los ~2831 previos.

## Correcciones semanticas

- `qa-gate` refleja que solo `catch {}` bloquea en strict; los demas hallazgos avisan.
- `code-forge-fix-lite` ya no presupone modelos locales y solo conserva memoria durable.
- `context-compressor` prohibe valores de entorno o secretos.
- `git-atomic-committer` exige peticion explicita y protege cambios ajenos.
- `ultraplan-lite` respeta permisos de Plan Mode y aprobacion humana.

## Errores encontrados y corregidos

1. La primera prueba temporal cambio `HOME`, pero OpenCode conservo el config
   real mediante XDG y cargo las skills singulares. Se fijo tambien
   `XDG_CONFIG_HOME`; la prueba plural paso antes de migrar el runtime.
2. La primera redaccion de AGENTS.md subio el piso fijo ~3 tokens. Se compacto
   la instruccion nativa y el piso final bajo ~12 tokens respecto al baseline.

## Accion humana

- Reiniciar la sesion de OpenCode para que esta sesion deje de conservar las
  definiciones de skills cargadas al inicio. Procesos nuevos ya pasan la prueba.
