# 004-gentle-round2 — Spec

## Problema
Segunda vuelta de `gentle-ai` v2.7.0 (`main df21d32b`, sin cambios): faltan privacy default, descubrimiento de skills al inicio de sesión, regla workspace-vs-global, Context7 opt-in documentado, desinstalación inversa y verificación de capabilities de modelos locales.

## Alcance
- ENTRA: A (capabilities, solo lectura+anotación), B `share: disabled` (votado: nunca comparte), C `uninstall` selectivo, D Context7 `enabled:false`, E regla workspace/global, F línea SessionStart-index, G pin-doc.
- FUERA: overlay 11 agentes, background launchers, TUI/binario, Engram, GGA, themes/personas, telemetría, Minisign, model-variants, judgment-day, E2E con modelo, configurar provider Ollama (hallazgo A: no existe; cablearlo cambia runtime → fuera de alcance).

## Criterios de aceptación
1. `opencode models --verbose` confirma: sin provider ollama (anotado, no configurado).
2. `debug config`: `share: disabled`, Context7 presente pero deshabilitado, permission intacto.
3. `uninstall` validado en copia temporal (restaura todo); `bash -n` OK.
4. `status sin drift`, `./verify.sh` verde, piso <3.8k tok.
