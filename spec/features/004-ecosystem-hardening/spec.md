# Feature 004: Ecosystem Hardening

## Objetivo
Corregir los 10 hallazgos de auditoria: SDK MCP ausente del package.json, sandbox shell injection, checkpoints expone .env, CI no bloqueante, instalador inseguro, embeddings incompletos, FTS5 inexistente, workflows duplicados, doctor sin router check, y diagramas con claims falsos.

## Requisitos (RFC 2119)

### MUST
- El router MCP debe iniciar desde una instalacion limpia sin dependencias instaladas manualmente.
- El sandbox no debe usar `shell: true` ni interpolar entrada de usuario en strings de shell.
- `checkpoints.js` no debe copiar `.env` ni archivos de credenciales a backups.
- CI debe bloquear releases cuando lint, tests, o memory-adapter tests fallen.
- El instalador debe respaldar archivos existentes antes de sobrescribir y.pin a tag, no HEAD.
- `saveDecision` debe incluir `content` en el texto de embedding.
- Busqueda semantica debe devolver filas sin embedding via fallback textual.
- `doctor.js` debe verificar el SDK del router y el handshake MCP.
- Diagramas y READMEs no deben afirmar que existe FTS5 cuando no existe.

### SHOULD
- Workflows de release no deben duplicar publicacion a npm.
- Dependabot no debe usar `--admin` para auto-merge.
- `mcp-server.js` debe derivar la version de `package.json`, no hardcodearla.
- Export a Obsidian debe evitar colisiones de nombres de archivo.

### MAY
- Anadir check-docs.js para evaluaciones deterministas de diagramas y contratos.

## Escenarios de Aceptacion (Given/When/Then)

1. **Instalacion limpia del router**: Given una maquina sin `~/.config/opencode/mcp/node_modules`, When `install.sh` corre, Then `local-model-router.js` importa `@modelcontextprotocol/sdk` sin error.

2. **Sandbox sin shell injection**: Given un `image` con `; rm -rf /`, When `sandbox_exec` corre, Then Docker recibe la imagen como argumento separado, no como string interpolado.

3. **Checkpoints excluye .env**: Given un `.env` en el directorio de config, When `snapshotConfigFull` corre, Then `.env` no aparece en ningun backup.

4. **CI bloqueante**: Given un PR que rompe lint, When CI corre, Then el job falla y bloquea el merge.

5. **Embeddings de contenido**: Given una decision con contenido unico en `content`, When `search_memory_semantic` busca por ese contenido, Then la decision aparece en resultados.

6. **Fallback textual**: Given una decision sin embedding (Ollama no disponible), When `search_memory_semantic` corre, Then la busqueda devuelve resultados via `LIKE`.

7. **Doctor verifica router**: Given una instalacion donde el SDK falta, When `doctor` corre, Then reporta `[FAIL] local-model-router SDK`.

8. **Sin claims FTS5**: Given los diagramas y READMEs, When `check-docs.js` corre, Then no encuentra la cadena "FTS5".
