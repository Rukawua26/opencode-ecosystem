# Plan: Ecosystem Hardening

## Arquitectura

No se anade runtime nuevo ni dependencias adicionales. Los fixes son puntuales y minimos:

1. **Router MCP**: Declarar `@modelcontextprotocol/sdk` en `config/mcp/package.json` e instalarlo con `npm ci --omit=dev`. El instalador copia el MCP y ejecuta `npm install` en `~/.config/opencode/mcp/`.
2. **Sandbox**: Reemplazar `spawnSync('sg', ['docker', '-c', ...], { shell: true })` por arrays de argumentos sin shell. Validar imagen con allowlist.
3. **Checkpoints**: Anadir `.env`/credenciales a `SKIP_PATTERNS`. Permisos `0700`/`0600` en backups.
4. **CI**: Quitar `continue-on-error`. Incluir tests del router. Unificar `release.yml` y `semantic-release.yml`.
5. **Instalador**: Pin a tag, backups antes de sobrescribir, sin `|| true` en copias criticas.
6. **Memoria**: Incluir `content` en embeddings. `LEFT JOIN` para filas sin embedding.
7. **Doctor**: Verificar SDK del router.
8. **Documentacion**: Corregir FTS5, separar capas en diagramas.

## Alternativas Descartadas

- **FTS5 real**: Requiere tablas virtuales y SQLite compilado con FTS5. La memoria local es pequenia; `LIKE` + embeddings es suficiente y mas simple.
- **Daemon Ollama permanente**: Consume RAM. El timer systemd es mas eficiente.
- **Bus de eventos**: Anade complejidad sin resolver un problema real.
- **Tests que arrancan Ollama en CI**: No deterministas y consumen recursos. Probar contratos, no runtime.

## Archivos Afectados

| Archivo | Cambio |
|---|---|
| `config/mcp/package.json` | Nuevo: declarar SDK |
| `config/mcp/package-lock.json` | Nuevo: lockfile |
| `config/mcp/local-model-router.js` | Version dinamica |
| `config/mcp/local-model-router.test.js` | Rutas relativas |
| `config/plugins/sandbox.js` | Sin shell, allowlist |
| `config/plugins/checkpoints.js` | Excluir .env |
| `install.sh` | Tag pin, backup, npm install MCP |
| `install.ps1` | Tag pin, backup, npm install MCP |
| `vitest.config.js` | Incluir tests del router |
| `package.json` | `test:router` script |
| `.github/workflows/test.yml` | Sin continue-on-error, router tests |
| `.github/workflows/release.yml` | Eliminar (duplicado) |
| `.github/workflows/semantic-release.yml` | Unificar release |
| `.github/workflows/dependabot-automerge.yml` | Sin `--admin` |
| `packages/memory-adapter/src/adapter.js` | Embeddings de content + LEFT JOIN |
| `packages/memory-adapter/src/mcp-server.js` | Version dinamica |
| `tools/scripts/doctor.js` | Verificar SDK router |
| `tools/scripts/check-docs.js` | Nuevo: checks deterministas |
| `docs/architecture/overview.md` | Sin FTS5, separar capas |
| `docs/architecture/diagrams.md` | Sin FTS5 |
| `README.md` | Sin FTS5 |
| `README.es.md` | Sin FTS5 |
| `packages/memory-adapter/README.md` | Sin FTS5 |
