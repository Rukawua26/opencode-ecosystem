# Plan 013

1. **Documentación (ADR-004)**: actualizar `~/docs/sources/gentle-ai-analysis.md`,
   `docs/comparison.md`, `~/docs/_MOC.md`, `~/docs/sources/Sources.md` con los
   baselines nuevos y las decisiones registradas. Cambios solo documentales.
2. **Doctor**: extender `tools/scripts/doctor.js` y `config-inspect.js` con un
   bloque `plugins` (listado de archivos, no contenido). Añadir tests en
   `tests/doctor.test.js`. Sin nuevas dependencias ni procesos.
3. **E2E mínimo**: evaluar cobertura existente (`install.test.sh` ya instala y
   realiza import real del plugin RDD). Documentar decisión; implementar solo
   si hay una brecha no cubierta.
4. **Backups**: medir `~/.config/opencode/plugins-data` y directorios de
   backups con `du`/hash para cuantificar duplicación antes de cualquier
   optimización.
5. **Verificación**: suites completas, CI, `verify.md`, commit+push.

Rechazado por filosofía (ahorro tokens/memoria, i5/8GB, YAGNI): Engram, TUI,
multi-runtime, updater, E2E framework, compresión de backups sin dato.
