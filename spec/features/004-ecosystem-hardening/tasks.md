# Tasks: Ecosystem Hardening (Ronda 1 + Ronda 2)

## Ronda 1 — Correcciones de auditoria (10 hallazgos)

- [x] 0. Crear spec/plan SDD 004
- [x] 1. Router MCP reproducible
- [x] 2. Sandbox sin shell injection
- [x] 3. Checkpoints excluye .env
- [x] 4. CI bloqueante
- [x] 5. Instalador seguro (tag pinning + backup)
- [x] 6. Memoria adapter (embeddings de content + LEFT JOIN)
- [x] 7. Doctor verifica router
- [x] 8. Documentacion (sin FTS5 + check-docs.js)
- [x] 9. Verificacion final (51/51 + 23/23 + 42/42)

## Ronda 2 — Pendientes detectados tras revision

- [x] 10. Fix pathToFileURL → fileURLToPath en router
- [x] 11. CI: npm ci --prefix config/mcp antes de test:router
- [x] 12. Test handshake: asertar version dinamica del router
- [x] 13. Instalador: no sobrescribir sin --force (copy_if_ok)
- [x] 14. Instalador: npm ci bloqueante (no || true ni 2>/dev/null)
- [x] 15. Instalador: verificar import del SDK en verify_install
- [x] 16. install.ps1: misma logica de no-sobrescribir + npm ci bloqueante
- [x] 17. Sandbox: eliminar rama sg, extraer helpers testeables
- [x] 18. Sandbox: fix regex metacharacters (\\n literal vs \n)
- [x] 19. Checkpoints: extraer isSkippable/SKIP_PATTERNS a helpers
- [x] 20. Tests reales: sandbox allowlist + metachar (16 tests)
- [x] 21. Tests reales: checkpoints .env/private key/.pem exclusion (13 tests)
- [x] 22. Memoria docs: documentar fallback textual en search_memory_semantic
- [x] 23. Doctor: API keys como opcional (no blocking)
- [x] 24. Limpiar workflow duplicado (check-docs dos veces en test.yml)

## Verificacion Final

- [x] 25. npm run lint (0 errors, 0 warnings)
- [x] 26. npm test (67/67)
- [x] 27. npm run test:router (23/23)
- [x] 28. node --test packages/memory-adapter (42/42)
- [x] 29. npm run check-docs (OK)
- [x] 30. npm run test:install (PASS, SDK verified)
- [x] 31. node tools/scripts/doctor.js (16/17, 1 optional skip)
- [x] 32. verify.md con matriz de cumplimiento
- [x] 33. RDD Tier 3 (start/capture/verify/finalize/gate)
- [x] 34. Commits atomicos por fase
