# Pendientes de v1.3

Actualizado: 2026-07-25.

## 1. Aprobar y fusionar PR #6

- PR: https://github.com/Rukawua26/opencode-ecosystem/pull/6
- Estado: fusionada en main (`44bb3dd`).

## 2. Publicar el paquete npm

- Paquete: `@rukawua26/opencode-memory-adapter@1.3.0`.
- Estado: publicado exitosamente.
- Release: https://github.com/Rukawua26/opencode-ecosystem/releases/tag/v1.3.0

## 3. Rotar el PAT de GitHub

- PAT revocado el 2026-07-25.
- Generar uno nuevo con los permisos minimos necesarios.
- No almacenar el nuevo valor en archivos, commits, logs ni documentacion.

## 4. Redisenio visual del README

- PR #8 fusionada en main (`e060c87`).
- Hero SVG, diagramas Mermaid, badges vibrantes, cards de componentes.

## 5. Actualizar Actions (Node 20 deprecation warning)

- Estado: completado.
- `actions/checkout@v4` → `actions/checkout@v4.2.2`
- `actions/setup-node@v4` → `actions/setup-node@v4.1.0`

## Verificacion completada

- Lint: PASS.
- Vitest: 7 pruebas PASS.
- Memory adapter y MCP: 22 pruebas PASS.
- Hooks: PASS.
- Instalador: PASS en Ubuntu, Alpine y macOS.
- Auditoria npm: 0 vulnerabilidades.
- Revision funcional independiente: PASS.
- Revision de seguridad independiente: PASS.
- CI con Actions actualizadas: PASS.
