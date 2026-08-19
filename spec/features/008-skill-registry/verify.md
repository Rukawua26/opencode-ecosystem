# Verify: Skill Registry Index-First

## Veredicto

PASS local en Bash y PowerShell 7.5.3 portable.

## Matriz

| Requisito | Estado | Evidencia |
|---|---|---|
| R1 Indice minimo | PASS | Cada entrada contiene solo name, description, path y root; orden y duplicados deterministas |
| R2 Seguridad | PASS | Solo `SKILL.md`, prefijo maximo 64 KiB, frontmatter limitado, symlinks directos/ancestros rechazados |
| R3 Escritura explicita | PASS | Status, JSON y search conservan bytes del indice; solo refresh escribe atomico 0600 |
| R4 Busqueda acotada | PASS | Search usa el indice y sanea controles de terminal |
| Escenario A | PASS | Refresh indexa metadata valida y reporta duplicados/invalidos |
| Escenario B | PASS | Operaciones read-only verificadas por test |
| Escenario C | PASS Linux | Symlinks de skill, raiz, indice y ancestros no se siguen |

## Verificacion

- `tests/skills-registry.test.js`: refresh, read-only, missing index, search,
  metadata exacta, YAML invalido, permisos y symlinks PASS.
- Suite completa, lint, check-docs, install Bash, audit y diff: PASS; evidencia
  agregada en `spec/features/007-config-truth-and-profiles/verify.md`.

## Hallazgos Corregidos

1. El primer scanner leia todo el cuerpo; ahora lee como maximo 64 KiB y exige
   el cierre del frontmatter en ese prefijo.
2. Se elimino `relativePath` para respetar el contrato minimo.
3. Se rechazan scalars YAML complejos/malformados y comentarios JSONC sin cerrar.
4. Se validan symlinks en todos los componentes desde HOME, no solo en el nodo final.
5. La salida de busqueda elimina controles C0/C1 y secuencias ESC.
6. El primer refresh activo detecto cinco skills distribuidas sin frontmatter;
   se anadio metadata minima identica en la distribucion y el paquete npm.

## Limitaciones

- El parser soporta deliberadamente el subconjunto de frontmatter necesario:
  strings simples, quoted strings y bloques `>`/`|`; no pretende implementar YAML completo.
- No hay watcher ni refresco automatico; es una decision de ahorro de memoria.
