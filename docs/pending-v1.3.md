# Pendientes de v1.3

Actualizado: 2026-07-25.

## 1. Aprobar y fusionar PR #6

- PR: https://github.com/Rukawua26/opencode-ecosystem/pull/6
- Estado: ✅ fusionada en main (`44bb3dd`).

## 2. Publicar el paquete npm

- Paquete: `@rukawua26/opencode-memory-adapter@1.3.1`.
- Estado: ✅ publicado exitosamente.
- Paquete: `@rukawua26/opencode-skills@1.3.0`.
- Estado: ✅ publicado exitosamente.
- Releases: https://github.com/Rukawua26/opencode-ecosystem/releases

## 3. Rotar el PAT de GitHub

- PAT revocado el 2026-07-25.
- Estado: ✅ Nuevo PAT configurado en secret `ECOSYSTEMAPUBLISH2`.
- Usado por: semantic-release (git push), Dependabot auto-merge.

## 4. Redisenio visual del README

- PR #8 fusionada en main (`e060c87`).
- Estado: ✅ Hero SVG, diagramas Mermaid, badges vibrantes, cards de componentes.
- Badge de GitHub Pages anadido (PR #21).

## 5. Actualizar Actions (Node 20 deprecation warning)

- Estado: ✅ completado.
- `actions/checkout@v4.2.2` → `v7.0.1`
- `actions/setup-node@v4` → `v7`
- `github/codeql-action@v3` → `v4`
- `softprops/action-gh-release@v2` → `v3`

## 6. Fase 1 - Quick Wins (PR #21)

- Estado: ✅ completado.
- Root package.json version bump 1.3.0 → 1.3.1.
- npm audit fix aplicado.
- Badge GitHub Pages en README.

## 7. Fase 2 - Automatizacion (PR #22, #23, #24, #25)

- Estado: ✅ completado.
- Dependabot auto-merge workflow.
- Semantic-release funcional (crea releases automaticamente).
- Releases automaticos: v1.4.0, v1.4.1.

## 8. Fase 3 - Verificacion (PR #26)

- Estado: ✅ completado.
- GitHub Pages cargando correctamente (docsify).
- npm packages verificados.
- CI verde en main, 0 PRs abiertas.

## Verificacion completada

- Lint: PASS.
- Vitest: 7 pruebas PASS.
- Memory adapter y MCP: 22 pruebas PASS.
- Hooks: PASS.
- Instalador: PASS en Ubuntu, Alpine y macOS.
- Auditoria npm: vulnerabilidades restantes son dependencias bundled de npm (no fixables).
- Revision funcional independiente: PASS.
- Revision de seguridad independiente: PASS.
- CI con Actions actualizadas: PASS.
- GitHub Pages: PASS (https://rukawua26.github.io/opencode-ecosystem/).
- Semantic Release: PASS (v1.4.1 latest).
- Dependabot Auto-Merge: PASS (configurado).
