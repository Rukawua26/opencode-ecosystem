# Plan: Dry Run and Structured Doctor

## Enfoque

1. Mantener el manifiesto como unica fuente de ownership.
2. Anadir un logger de operaciones dry-run dentro de las funciones actuales de
   copia, backup y pruning, no como simulador separado.
3. Usar un archivo temporal de manifest solo en ejecuciones reales; dry-run
   mantiene las entradas proyectadas en memoria.
4. En distribucion local, enumerar las fuentes reales. En ejecucion remota sin
   fuentes, reportar solo el clone y diferir el plan detallado.
5. Separar recoleccion y render del doctor para que texto y JSON usen los mismos
   resultados.
6. Validar el manifest sin hashes y declarar `modified: unknown`.

## Decisiones

- No crear `state.json`: duplicaria version y ownership sin necesidad actual.
- No cambiar el formato del manifest: hashes requieren una migracion separada.
- Dry-run no ejecuta verificaciones del destino simulado porque producirian
  falsos negativos; reporta `defer-verification`.
- Las comprobaciones de symlink y traversal siguen activas en preview.
- JSON usa arrays ordenados e IDs estables; no expone valores de API keys.

## Archivos

| Archivo | Cambio |
|---|---|
| `install.sh` | `--dry-run`, operaciones y cero mutaciones |
| `install.ps1` | Paridad `-DryRun` |
| `tools/scripts/doctor.js` | Colector comun, JSON y manifest |
| `tests/install.test.sh` | Invariancia y plan Bash |
| `tests/install.test.ps1` | Invariancia y plan Windows |
| `tests/doctor.test.js` | Contrato JSON y regresion humana |
| `package.json` | Script focalizado de doctor si aporta valor |
| `README.md` | Uso y limites verificables |

## Riesgos y Mitigaciones

- Divergencia preview/apply: instrumentar funciones existentes y probar ambos
  sobre las mismas fixtures.
- Escritura accidental: snapshot recursivo antes/despues y subprocess shims.
- Pruning falso sin sources: diferir plan detallado cuando no hay repo local.
- Manifest hostil: validar antes de resolver destinos y no seguir symlinks.
- JSON inestable: esquema v1, IDs fijos y orden lexicografico.
- PowerShell local ausente: cobertura equivalente y gate CI Windows.

## Verificacion

- `bash -n install.sh tests/install.test.sh`
- `npm test`
- `npm run test:coverage`
- `npm run test:install`
- `npm run test:install:windows` en CI Windows
- `npm run test:router`
- `node --test packages/memory-adapter/tests/*.test.js`
- `npm run lint`
- `npm run check-docs`
- `npm audit --audit-level=high`
- `git diff --check`
- Organic RDD Tier 3 por instalador y diagnostico de seguridad.
