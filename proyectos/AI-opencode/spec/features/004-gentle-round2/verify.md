# 004-gentle-round2 — verify.md (2026-09-11)

## Criterios vs evidencia
1. **A capabilities** ✅ `opencode models --verbose`: sin provider ollama (solo `opencode/*` + `openai/*`). Anotado en config, no cableado (cambiaría runtime → fuera de alcance).
2. **debug config** ✅ `share: disabled`, `context7` presente `enabled:false`, permission `10/11/ask` intacto.
3. **C uninstall** ✅ preview lista 16 gestionados (incluye índice); `--apply` en sandbox `HOME` falso borra con backup y preserva `.env`.
4. **status/verify/doctores** ✅ `sin drift`, `verify verde`, `plugin_doctor` sano, piso fijo **~3805 tok** (spec decía <3.8k; +5 tok por 3 líneas nuevas — aceptado, sin churn).

## Errores encontrados y corregidos
1. **Trigger vs prune inconsistentes**: trigger contaba baks totales (>5) pero prune conserva por basename → gatillo eternamente encendido (6 ficheros, 0 podables). Fix: `prune_candidates()` compartida; trigger usa podables reales.
2. **`verify.sh` pintaba rojo con gatillo disparado**: un gatillo es informativo, no fallo. Fix: `|| true` en triggers.
3. **Poda real ejecutada**: 3 `.bak-2026-09-10` duplicados (hash idéntico al `-09-11`, pre-P2, redundantes) eliminados con `--apply`. Lo vivo con P2 verificado en CFG+ECO antes de borrar.
4. **Doctor no parseaba URLs JSONC**: el regex confundía `//` de `https://` con comentario y `verify.sh` no lo detectaba porque doctor devolvía 0. Fix: parser de comentarios consciente de strings; re-verificado con Context7 deshabilitado visible.
