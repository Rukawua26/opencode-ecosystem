# 003-hygiene-lote-b — Spec

## Problema
Deuda lenta sin freno: `.bak` por cada sync (3 hoy), `observations.log` y `topics/` sin poda ni reset, validación post-cambio manual (4 comandos a mano). Sin herramientas, la higiene depende de memoria humana.

## Alcance
- ENTRA: `scripts/hygiene.sh {triggers|prune|reset}` + `verify.sh` (raíz ECO, no sincronizado).
- FUERA: timers automáticos, P4 (anexo condicional), recorte AGENTS.md, MCPs, multi-perfil.

## Criterios de aceptación
1. `hygiene.sh triggers` imprime `.bak` vs 5, log vs 200, topics vs 10; hoy 3/2/1 → "no dispara".
2. `prune`/`reset` en preview no modifican nada (checksum antes/después iguales); `--apply`/`--confirm` ejecutan.
3. `prune --apply` con 7 baks de prueba conserva los 5 más nuevos; dedup por sha256 no duplica borrado.
4. `reset --confirm` preserva `MEMORY.md` y `*.sh`; trunca log a 50 líneas.
5. `verify.sh` exit 0 en verde, ≠0 con drift; `status sin drift` tras publish+sync.
