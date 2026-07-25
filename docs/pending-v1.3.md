# Pendientes de v1.3

Estado registrado: 2026-07-24.

## 1. Aprobar y fusionar PR #6

- PR: https://github.com/Rukawua26/opencode-ecosystem/pull/6
- Estado: abierta, fusionable y con todos los checks en verde.
- Bloqueo: `main` requiere una aprobacion humana externa.
- Regla: no omitir ni desactivar la proteccion para fusionarla.

## 2. Publicar el paquete npm

- Paquete: `@rukawua26/opencode-memory-adapter@1.3.0`.
- Bloqueo: pendiente fusionar el cambio de nombre scoped porque
  `opencode-memory-adapter` ya pertenece a otro mantenedor en npm.
- Accion: fusionar el fix del nombre, confirmar `NPM_TOKEN` y ejecutar el
  workflow de release para la etiqueta `v1.3.0`.

## 3. Rotar el PAT de GitHub

- PAT revocado el 2026-07-25.
- Generar uno nuevo con los permisos minimos necesarios.
- No almacenar el nuevo valor en archivos, commits, logs ni documentacion.

## Verificacion completada

- Lint: PASS.
- Vitest: 7 pruebas PASS.
- Memory adapter y MCP: 22 pruebas PASS.
- Hooks: PASS.
- Instalador: PASS en Ubuntu, Alpine y macOS.
- Auditoria npm: 0 vulnerabilidades.
- Revision funcional independiente: PASS.
- Revision de seguridad independiente: PASS.
