# 001-ecosystem-lite — verify.md (2026-09-11)

## Criterios vs evidencia
1. **Config válida, solo modelos 1-3B** ✅ `opencode debug config` OK (snapshot/compaction/watcher); `opencode --version 1.18.29`; `ollama list` confirma qwen2.5-coder:1.5b/3b, llama3.2:1b/3b, deepseek-r1:1.5b. Sin MCP locales inexistentes (romperían arranque).
2. **Doctores verdes** ✅ `plugin_doctor.sh --no-binary`: "plugins sanos"; `query_context.py doctor`: piso fijo ~3253 tok, sin MCP, exit 0.
3. **Scripts ejecutables** ✅ `bash -n` OK en kairos/autodream/ram-guard/qa-gate; timers systemd `active (waiting)`, triggers 5min/30min; `ram-guard` exit 0, `kairos /tmp` anexa a observations.log, `autodream` consolida a `topics/inbox-*.md`.
4. **qa-gate** ✅ warn exit 0 siempre; `--strict` exit 1 con `catch(e){}` en staged (verificado en /tmp/qa-test; el 0 inicial fue por cwd=/home/miguel sin staged — comportamiento correcto).
5. **Fuente de verdad sin drift** ✅ `opencode-ecosystem status` → "[ok] sin drift"; `sync --apply` con backups `.bak-FECHA`; `.env/observations.log/topics/` excluidos del sync.
6. **ADR-004** ✅ `~/docs/sources/noffolo-ecosystem-analysis.md` (TOMAMOS/DEJAMOS + baseline main@2026-09-11 + protocolo re-verificación).

## Falso positivo descartado
- `JSON.parse` directo de `opencode.jsonc` falla por comentarios `//` — esperado (JSONC válido para opencode, verificado con `opencode debug config`).
- `plugin_doctor` línea "personal: *.js" — glob sin ficheros, inocuo (no hay plugins instalados aún).

## Pendiente humano
- `plugin_doctor.sh pin` tras reiniciar OpenCode (el doctor usa `~/.opencode/bin/opencode` y el binario real es `/usr/bin/opencode` — drift conocido, no bloqueante).
- Reiniciar OpenCode para cargar nueva config; 3 sesiones reales para validar memoria.
- Backup original en `/tmp/opencode-backup-20260911`.
