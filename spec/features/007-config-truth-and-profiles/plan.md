# Plan: Config Truth and Profiles

## Enfoque

1. Crear un inspector JSONC pequeno compartido por doctor y reporte de perfiles.
2. Anadir informacion aditiva al JSON del doctor sin nuevos checks obligatorios.
3. Mantener launchers shell pequenos y validar archivos antes de `exec`.
4. Instalar herramientas con el manifiesto y dry-run existentes.
5. Probar status, JSON, perfil invalido e instalacion multiplataforma.

## Archivos

| Archivo | Cambio |
|---|---|
| `tools/scripts/config-inspect.js` | Parse e inspeccion JSONC compartida |
| `tools/scripts/doctor.js` | Resumen de configuracion y perfiles |
| `tools/scripts/profile.js` | Estado humano/JSON de perfiles |
| `tools/scripts/opencode-*.sh` | Menu y launchers Bash |
| `install.sh`, `install.ps1` | Instalacion gestionada |
| `tests/doctor.test.js` | Contrato config aditivo |
| `tests/profile.test.js` | Launchers y status |

## Verificacion

- `npm test`
- `npm run test:install`
- `npm run test:install:windows`
- `npm run lint`
- `npm run check-docs`
- Organic RDD Tier 2/3 por configuracion e instaladores.
