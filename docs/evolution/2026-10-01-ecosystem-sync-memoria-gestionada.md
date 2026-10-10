---
nombre: 2026-10-01-ecosystem-sync-memoria-gestionada
fecha: 2026-10-01
estado: verificado
afecta: [scripts, memoria]
fuente: propio
---

# Contrato de sync/status para scripts de memoria

## Por que
`opencode-ecosystem` copiaba `memory/kairos.sh`, `memory/autodream.sh` y
`MEMORY.md` al runtime **solo si no existían**, y `cmd_status` no comparaba los
dos scripts de memoria. Resultado: el runtime podía divergir de la fuente de
verdad sin que `status` diera `[drift]`, obligando a copias manuales. Se
evidenció en la feature memoria-señal (2026-09-29), donde hubo que copiar
`kairos.sh`/`autodream.sh` a mano.

## Antes
- `cmd_status` no comparaba `memory/kairos.sh` ni `memory/autodream.sh`.
- `cmd_sync --apply`: `for s in kairos.sh autodream.sh MEMORY.md; do [ -e ... ] || cp ...; done`
  (copiaba solo si faltaba, sin backup).
- `MEMORY.md` se trataba igual que los scripts (se sembraba solo si faltaba).

## Despues
- `cmd_status` reporta `[drift] memory/kairos.sh` y `[drift] memory/autodream.sh`
  cuando diffieren, y ya no da `[ok] sin drift` en ese caso.
- `cmd_sync --apply` copia siempre `kairos.sh` y `autodream.sh` desde la fuente
  con backup `backup_dest` (`.bak-AAAA-MM-DD`).
- `MEMORY.md` solo se siembra si falta; **nunca** se sobrescribe una versión
  existente (estado del usuario). `logs/` y `topics/` intactos.

## Beneficio
- `status` ya no puede mentir: detecta el desfase de los scripts de memoria.
- `sync --apply` garantiza runtime == fuente para los scripts gestionados, con
  rollback (`.bak-FECHA`).
- Se elimina la copia manual y la divergencia silenciosa.

## No regresion
- Base reversible: árbol en Git. El cambio es mejor o igual que el anterior.
- `status`/`sync` siguen gestionando lo mismo para configs, skills, scripts y
  commands (solo se añade la comparación/copia de 2 scripts de memoria).
- `MEMORY.md`, `observations.log`, `topics/`, `ram-guard.log` y backups siguen
  siendo no gestionados / no sobrescritos por `sync`.
- Permisos ejecutables de `kairos.sh`/`autodream.sh` preservados.

## Verificacion
- `python3 -m unittest control.tests.test_ecosystem_sync` -> 7/7 OK (RED antes
  del fix con 3 fallos).
- `python3 -m unittest discover -s control/tests` -> 189 tests OK (1 skipped).
- `python3 validate-skills.py skills` -> `[ok] 12 skills valid`.
- `./opencode-ecosystem status` -> `[ok] sin drift` (antes y despues).
- `./opencode-ecosystem sync --apply` -> backups y `diff` runtime==fuente para
  `kairos.sh`, `autodream.sh`, `ram-guard-lite.sh` y `MEMORY.md`.
- `scripts/qa-gate.sh --strict` -> exit 0.
- `./verify.sh` -> `[fail] plugin_doctor` **solo** por drift de versión de
  OpenCode `v2.0.21` vs pinchada `v2.0.18`; ajeno a este cambio (actualización
  del binario, no re-pineado sin autorización). Resto de pasos en verde.

## Periodo prudencial
- 7 días. Estable si `status` sigue `[ok] sin drift` y `sync --apply` no
  sobrescribe `MEMORY.md`/logs/topics.
- Señal de revertir: `sync` pisa la memoria viva, o `status` deja de detectar
  drift en los scripts de memoria.
- Rollback: revertir `opencode-ecosystem` desde Git, `sync --apply`, `status`
  verde y `verify.sh` verde (salvo el fail ajeno de `plugin_doctor`).

## Fuente (si aplica)
Determinado por análisis de `opencode-ecosystem` (propio); paridad conceptual con
gentle-ai v4 (manifiesto/ámbito/permisos) ya cubierta por nuestro enfoque lite.
