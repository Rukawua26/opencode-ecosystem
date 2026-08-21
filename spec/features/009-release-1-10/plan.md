# Plan: Release v1.10.0 y cierre documental

1. Sustituir el pin autorreferencial de commits por validacion del tag exacto y
   actualizar sus contratos documentales.
2. Alinear la base de conocimiento y runbooks con el repositorio canonico.
3. Elevar versiones a `1.10.0` y actualizar changelog, README e instaladores.
4. Verificar suites, instaladores, paquetes, dry-run, doctor y fallback Ollama.
5. Resolver los bloqueos Windows y CodeQL observados en el primer push, conservar
   SARIF como artefacto y repetir todos los gates remotos.
6. Completar Organic RDD, fusionar a `main`, solicitar el workflow de release
   con version explicita y comprobar artefactos remotos.

## Archivos previstos

- `README.md`, `README.es.md`, `CHANGELOG.md`
- `package.json`, `package-lock.json`
- `packages/memory-adapter/package.json`, `packages/memory-adapter/README.md`
- `packages/skills/package.json`
- `config/mcp/package.json`, `config/mcp/package-lock.json`
- `install.sh`, `install.ps1`, tests de instalacion y `check-docs.js`
- `.github/workflows/test.yml`, `.github/workflows/codeql.yml`
- `tools/scripts/verify-release-tag.sh`, `tests/release-tag.test.sh`
- `docs/README.md`, `docs/guides/quick-start.md`, `docs/architecture/diagrams.md`
- notas y runbooks OpenCode bajo `/home/miguel/docs/`

## Decisiones

- `1.10.0` es minor porque incorpora comandos publicos de perfiles y skills.
- El tag exacto evita el hash circular sin introducir firmas o servicios nuevos.
- La publicacion es manual y versionada; los pushes normales solo ejecutan CI.
- Acciones por SHA y npm provenance reducen riesgo de supply chain.
- Embeddings no bloquean la release: el runtime soportado sigue siendo textual
  con enriquecimiento semantico solo cuando Ollama ofrece la capacidad.
