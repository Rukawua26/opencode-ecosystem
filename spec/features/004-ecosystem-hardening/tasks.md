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
- [x] 9. Verificacion final inicial (51/51 + 23/23 + 42/42)

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

## Ronda 3 — Hallazgos de Organic RDD

- [x] 25. Mensajes de validacion del sandbox consistentes en ingles
- [x] 26. Query semantica vacia normalizada y sin fallback contaminado
- [x] 27. Fallback textual case-insensitive sin reconstruir query desde `%...%`
- [x] 28. Patron `.env` unico para Unix, Windows y variantes `.env-*`
- [x] 29. Reinstalacion normal preserva agentes, skills, perfiles y herramientas
- [x] 30. Reinstalacion `--force` prueba backup antes de reemplazar
- [x] 31. Memory adapter omite `npm install` porque no tiene dependencias runtime

## Verificacion Final

- [x] 32. npm run lint (0 errors, 0 warnings)
- [x] 33. npm test (67/67)
- [x] 34. npm run test:router (23/23)
- [x] 35. node --test packages/memory-adapter (43/43)
- [x] 36. npm run check-docs (OK)
- [x] 37. npm run test:hooks (PASS)
- [x] 38. npm run test:install (PASS, preserve + rollback + SDK)
- [x] 39. node tools/scripts/doctor.js (16/17, provider opcional)
- [x] 40. verify.md con matriz de cumplimiento
- [x] 41. RDD Tier 3 aprobado y gate PASS
- [x] 42. Commits atomicos por fase
