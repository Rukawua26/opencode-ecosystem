# 003-hygiene-lote-b — verify.md (2026-09-11)

## Criterios vs evidencia
1. **triggers** ✅ `3/2/1 → no dispara` (umbrales 5/200/10).
2. **preview inocuo** ✅ prune/reset preview sin cambios (topics y log intactos antes del test).
3. **prune --apply** ✅ 7 baks falsos → conserva 5 más nuevos, borra 2 viejos; 3 idénticos → conserva 1 (dedup sha256). Limpieza posterior verificada.
4. **reset --confirm** ✅ topics vaciado, log 2 líneas intacto, `MEMORY.md` + `*.sh` intactos (`bash -n kairos.sh` OK).
5. **verify.sh** ✅ exit 0, "verify verde" (triggers + debug config + status + ambos doctores).
6. **sync** ✅ `status sin drift`, `hygiene.sh` en CFG con +x y syntax OK.

## Errores encontrados y corregidos
1. **Permiso denegado** al ejecutar `hygiene.sh`/`verify.sh` — `Write` no da +x. Fix: `chmod +x`.
2. **Gap en `status`**: solo comparaba `ram-guard-lite.sh`, no vio `hygiene.sh` nuevo. Fix: `diff -rq` al dir `scripts/` completo.
