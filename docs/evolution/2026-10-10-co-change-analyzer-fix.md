---
nombre: 2026-10-10-co-change-analyzer-fix
fecha: 2026-10-10
estado: verificado
afecta: [scripts, docs]
fuente: propio
---

# Fix co-change-analyzer: co-cambios reales del fichero pedido

## Por que
`scripts/co-change-analyzer.sh` aceptaba `<archivo>` como argumento, lo validaba
contra vacio, pero **lo ignoraba**: hacía `git log --name-only` global y mostraba
los ficheros más versionados del repo, no los co-cambios del fichero pedido.
Confirmado empíricamente: salida idéntica con `memory/kairos.sh` y
`scripts/qa-gate.sh`. La herramienta no hacía lo que dice su uso y su entrada en
el README ("Sugiere qué revisar junto tras un cambio").

## Antes
```bash
git log --name-only --pretty=format: 2>/dev/null | grep -vE "^\s*$" | sort | uniq -c | sort -rn | head -5 || true
```
Ranking global, sin usar `$F`.

## Despues
```bash
N=100
git rev-list -n "$N" HEAD -- "$F" 2>/dev/null \
  | xargs -r git show --format= --name-only 2>/dev/null \
  | grep -vE '^[[:space:]]*$' \
  | grep -vxF "$F" \
  | sort | uniq -c | sort -rn | head -5 || true
```
Co-cambios reales: ficheros presentes en los mismos commits que `$F` (excluyendo
`$F`), acotado a los últimos 100 commits que lo tocaron. 3 procesos git
(`rev-list`, `xargs`, `show`), no uno por commit.

## Beneficio
- La herramienta hace lo que promete: co-cambios del fichero pedido.
- Salida distinta y significativa por fichero (verificado).
- Coste acotado (3 procesos) en la máquina modesta.

## No regresion
- Base reversible en Git: versión anterior commiteada en `a2f77e4` (el cambio
  actual está sin commit; `git checkout -- scripts/co-change-analyzer.sh` revierte).
- Formato de salida igual (conteo + ruta, top 5); sigue siendo advisory manual,
  sin cablear a hooks.
- Sin dependencias nuevas; solo git + coreutils.

## Verificacion
- `bash -n scripts/co-change-analyzer.sh` -> OK.
- Salida distinta por fichero: `memory/kairos.sh` (verify.sh, validate-skills.py,
  skills...) vs `control/actions.py` (control/web/index.html, tests...).
- Ficheros que comparten commit (`memory/kairos.sh` y
  `scripts/co-change-analyzer.sh`, ambos en `a2f77e4`) dan la misma salida:
  correcto, son co-cambios reales de ese commit.
- Sin argumento -> `uso: ...` y exit 0.
- Suite completa `python3 -m unittest discover -s control/tests` -> 233 tests OK
  (1 skipped). `validate-skills.py skills` -> 13 valid. `status` -> sin drift.
- Baseline de `~/docs/sources/gentle-ai-analysis.md` actualizada a v4.0.0
  (2026-10-10) segun ADR-004, con enlaces en `_MOC.md` y `Sources.md`.

## Periodo prudencial
- 7 dias. Estable si la salida sigue siendo co-cambios reales y acotada.
- Revertir si: el pipeline se vuelve lento en repos grandes o produce salidas
  engañosas (entonces revisar el umbral `N` o el filtro).
- Rollback: `git checkout -- scripts/co-change-analyzer.sh`.

## Fuente (si aplica)
Fix propio; idea de co-cambios reales alineada con la revision gentle-ai v4.0.0
(`~/docs/sources/gentle-ai-analysis.md`, Revision 2026-10-10).
