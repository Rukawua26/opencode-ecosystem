# Verify: Config Truth and Profiles

## Veredicto

PASS local en Bash y PowerShell 7.5.3 portable; Windows nativo queda cubierto por CI.

## Matriz

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 Diagnostico read-only | PASS | Doctor y profile tests comparan estado antes/despues; no exponen valores de `.env` |
| R2 Contrato compatible | PASS | JSON sigue schema v1; config es aditiva; checks obligatorios permanecen 18/18 |
| R3 Perfiles reproducibles | PASS Bash/PowerShell | Cuatro launchers instalados y gestionados por manifest |
| R4 Fallo explicito | PASS | Perfil ausente, JSONC invalido y comentario bloque sin cerrar fallan antes de `exec` |
| Escenario A | PASS | Reporte ordenado de main, perfiles, modelos, plugins y MCP |
| Escenario B | PASS | `sdd_multi_model` se detecta como legado experimental y fue retirado de la config distribuida |
| Escenario C | PASS Bash/PowerShell | `light` fija `OPENCODE_CONFIG` y effort `low`; test con binario OpenCode simulado |

## Verificacion

- `npm test`: 105/105 PASS en 13 archivos.
- Tests focalizados de doctor, perfiles y registry: 21/21 PASS.
- `npm run test:coverage`: PASS; 93.61% statements, 77.48% branches,
  100% functions y 96.63% lines sobre modulos instrumentados.
- `npm run test:install`: PASS, incluidos dry-run, sync, force, manifest,
  backups y rechazo de symlinks en sync/force.
- `npm run test:install:windows`: PASS con PowerShell 7.5.3 portable cuyo
  SHA-256 oficial fue verificado antes de extraer.
- `npm run lint`: PASS.
- `npm run check-docs`: PASS.
- `npm run test:router`: 23/23 PASS.
- Memory adapter: 43/43 PASS.
- `npm audit --audit-level=high`: 0 vulnerabilidades.
- `git diff --check`: PASS.
- `opencode debug config --pure` con la config distribuida: schema aceptado.

## Hallazgos Corregidos

1. Los checks nuevos del doctor eran obligatorios y cambiaban exits historicos;
   ahora son informativos y el detalle permanece en `config`.
2. Una ruta alternativa bajo un perfil podia validar el archivo canonico; ahora
   se inspecciona exactamente `OPENCODE_CONFIG`.
3. `sdd_multi_model` no pertenece al esquema oficial y no tenia consumidor; se
   retiro de la config y de las afirmaciones de routing automatico.
4. `--force` solo validaba symlinks en sync; ahora toda escritura gestionada
   valida componentes desde HOME.
5. En Windows, los wrappers fijan Node y PowerShell por ruta absoluta y el doctor
   excluye el directorio actual al resolver comandos.

## Limitaciones

- La ejecucion PowerShell local usa el runtime Linux portable; CI conserva la
  comprobacion nativa Windows.
- La sesion OpenCode actual debe reiniciarse para recargar archivos de config o
  plugins; los comandos externos instalados no necesitan reinicio.
