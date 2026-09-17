# 005-runtime-reconciliation - Verify (2026-09-11)

## Resultados

1. **Binario y pin**: `plugin_doctor.sh` resuelve `/usr/bin/opencode`, reporta
   `1.18.29` y coincide con `.opencode-version.pin`. Un override inexistente
   falla con exit distinto de cero.
2. **Doctor completo**: verde, sin el falso plugin literal `*.js`; no hay
   plugins activos que inspeccionar.
3. **Contexto**: piso fijo reducido de ~3850 a **~2831 tokens** (objetivo
   <=3400). Context7 aparece INACTIVO y el doctor reporta la memoria
   Markdown+Bash real por debajo de sus gatillos.
4. **Runtime**: `opencode debug config` exit 0; ram-guard y kairos `active`.
5. **Ecosistema**: `verify.sh` verde y `status` sin drift. No se ejecuto
   publish/sync ni se reinicio OpenCode porque no cambio configuracion gestionada.
6. **Specs**: 001 marca MCP local diferido; 002 registra P5/P6 completados por
   spec 003; no quedan pendientes tecnicos anteriores.

## Errores encontrados y corregidos

1. `plugin_doctor.sh` tenia fija la ruta inexistente `~/.opencode/bin/opencode`.
   Ahora usa override, PATH y fallback; nunca pinea `?`.
2. Sin plugins, el glob literal `*.js` aparecia como plugin personal. Se activo
   `nullglob`.
3. `AGENTS.md` y README indicaban editar ECO y despues `publish`, pero publish
   copia CFG->ECO y podia borrar esos cambios. El flujo ahora distingue
   ECO->CFG (`sync`) de CFG->ECO (`publish`).
4. El context doctor seguia buscando `memory-adapter` y `ollama embed`, ambos
   ausentes. Ahora audita la memoria Markdown+Bash instalada.

## Pendiente humano

- Observar tres sesiones reales con memoria y qa-gate; no se simula como
  evidencia tecnica. Higiene actual por debajo de sus gatillos.
