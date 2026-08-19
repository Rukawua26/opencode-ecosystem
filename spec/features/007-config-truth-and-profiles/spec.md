# Spec: Config Truth and Profiles

## Problema

La configuracion distribuida, los perfiles instalados y la documentacion pueden
divergirse sin una senal operativa. Los launchers de perfil existen en algunas
maquinas, pero no forman parte reproducible de la distribucion, y falta un
launcher directo para `light`.

## Alcance

- Extender `opencode-doctor --json` con un resumen read-only de config y perfiles.
- Reportar configuracion activa, modelos, plugins y MCP sin exponer secretos.
- Instalar launchers reproducibles para `work`, `personal`, `light` y el menu.
- Mantener el contrato JSON v1 y los checks obligatorios existentes.

## Fuera De Alcance

- Activar perfiles SDD generados o cambiar modelos en caliente.
- Reparar o sobrescribir automaticamente `opencode.jsonc`.
- Convertir `sdd_multi_model` en una extension no soportada por OpenCode.
- Introducir TUI, Go o gestores de perfiles externos.

## Requisitos

### R1 - Diagnostico read-only

El doctor MUST inspeccionar config principal y perfiles sin escribir archivos ni
mostrar valores de credenciales.

### R2 - Contrato compatible

El JSON MUST mantener `schemaVersion: 1`, checks y exit codes existentes. El
resumen de configuracion MUST ser un campo aditivo y determinista.

### R3 - Perfiles reproducibles

La distribucion MUST instalar `opencode-profile`, `opencode-work`,
`opencode-personal` y `opencode-light` en Bash y PowerShell.

### R4 - Fallo explicito

Un perfil inexistente o invalido MUST fallar antes de iniciar OpenCode. El modo
status MUST ser read-only y MUST funcionar sin iniciar OpenCode.

## Escenarios De Aceptacion

### Escenario A - Config valida

Given una instalacion con perfiles validos
When se ejecuta `opencode-doctor --json`
Then reporta modelos, plugins, MCP y perfil activo en orden determinista.

### Escenario B - Config experimental

Given una config que declara `sdd_multi_model`
When se inspecciona
Then se informa como declaracion sin consumidor confirmado y no se activa.

### Escenario C - Perfil light

Given una instalacion completa
When se usa `opencode-light`
Then exporta el perfil y effort low antes de ejecutar OpenCode.
