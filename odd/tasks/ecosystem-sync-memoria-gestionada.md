# Contrato de sync/status para scripts de memoria (ecosystem-sync-memoria-gestionada)

## Objetivo
Cerrar la brecha de despliegue de `memory/kairos.sh` y `memory/autodream.sh`:
el runtime podía divergir de la fuente de verdad sin que `status` lo detectara y
sin que `sync --apply` lo corrigiera, obligando a copias manuales.

## Problema y por que
`opencode-ecosystem` copiaba `memory/kairos.sh`, `memory/autodream.sh` y
`MEMORY.md` a `~/.config/opencode/memory/` **solo si no existían**
(`[ -e ] || cp`). Además, `cmd_status` no comparaba esos dos scripts, así que
podía reportar `[ok] sin drift` aunque el runtime estuviera desactualizado.
Quien lo sufre: cualquier sesión que confíe en la señal de memoria o en el
`status` del ecosistema. Se evidenció en la feature memoria-señal (2026-09-29),
cuando hubo que copiar `kairos.sh`/`autodream.sh` a mano y el `status` no daba
aviso del desfase.

## Alcance
### Incluye
- `opencode-ecosystem`: `cmd_status` detecta drift en `memory/kairos.sh` y
  `memory/autodream.sh`.
- `opencode-ecosystem`: `cmd_sync --apply` copia siempre esos dos scripts desde
  la fuente, con backup reversible (`backup_dest`).
- Test de regresión `control/tests/test_ecosystem_sync.py` con HOME temporal.

### Excluye
- Re-pinear la versión de OpenCode (drift `v2.0.21` vs `v2.0.18` es ajeno al
  ecosistema y requiere autorización).
- Tocar memoria viva (`MEMORY.md` real, `observations.log`, `topics/`,
  `ram-guard.log`).
- `publish`, `capture`, `uninstall`, scheduler `configs/cron-jobs.json`.
- Migrar `control/db.py`, skills nuevas, dependencias.

## Restricciones
- Python stdlib solo (los tests); bash existente en el script.
- i5-1235U / 8GB: pruebas bajo un `HOME` temporal, sin tocar la memoria viva.
- Sin regresion: `status` y `sync` mantienen su contrato para el resto de
  ficheros gestionados; `MEMORY.md` vivo nunca se sobrescribe.
- Gate Git humano: no commit, push, PR ni merge sin petición explícita.

## TDD
- Modo: off (script bash sin runner de tests unitarios propios)
- Fuente: default — política de proyecto exige `control/tests` para comportamiento
- Runner: `python3 -m unittest control.tests.test_ecosystem_sync` (checks
  funcionales obligatorios) + suite completa + `verify.sh`

## Tareas
- [x] T1 — Definir propiedad: `kairos.sh`/`autodream.sh` gestionados;
      `MEMORY.md`, logs y `topics/` privados e intocables.
- [x] T2 — Test de regresión con HOME temporal que reproduce el bug (RED antes
      del fix, 3 fallos).
- [x] T3 — Fix mínimo en `opencode-ecosystem` (status + sync con backup, sin
      sobrescribir memoria viva).
- [x] T4 — Documentación: este ODD + `docs/evolution/2026-10-01-ecosystem-sync-memoria-gestionada.md`.
- [x] T5 — Verificación completa (suite, validate-skills, status, verify.sh) y
      propagación al runtime con `sync --apply`.

## Decisiones aceptadas
- 2026-10-01: tratar `memory/kairos.sh` y `memory/autodream.sh` como scripts
  gestionados (se copian siempre con backup); `MEMORY.md` se siembra solo si
  falta y nunca se sobrescribe (es estado del usuario).
- 2026-10-01: no re-pinear OpenCode por el drift de `plugin_doctor`; es un
  cambio ajeno al ecosistema (actualización del binario).

## Reutilización investigada
- Se reutiliza `backup_dest` ya existente en `opencode-ecosystem`; no se
  inventa una función nueva de backup.
- Se aprovecha el patrón de test con `HOME` temporal ya usado para el sandbox de
  `autodream.sh` en la feature memoria-señal.

## Evidencia
- T1 — Estado: passed. Clasificación reflejada en el diff de `opencode-ecosystem`.
- T2 — Estado: passed (RED). `python3 -m unittest control.tests.test_ecosystem_sync`
  mostró 3 fallos antes del fix (status no detecta drift en kairos/autodream;
  sync no corrige kairos).
- T3 — Estado: passed. Tras el fix, los 7 tests del módulo pasan (OK).
- T4 — Estado: passed. ODD y evolution doc escritos.
- T5 — Estado: passed. Suite completa 189/189 OK (1 skipped), 12 skills válidas,
  `status` -> `[ok] sin drift`, `sync --apply` con backups y `diff` runtime==fuente
  para `kairos.sh`, `autodream.sh`, `ram-guard-lite.sh` y `MEMORY.md`.
  Nota: `verify.sh` reporta `[fail] plugin_doctor` por drift de versión de
  OpenCode `v2.0.21` vs pinchada `v2.0.18` (preexistente, no causado por este
  cambio); resto de pasos de `verify.sh` en verde.

## Progreso
- Estado: verificado.
- Última tarea: T5.
- Siguiente paso: observación 7 días (sync/status siguen sin drift y sin
  sobrescribir memoria viva).
- Bloqueos: ninguno.
