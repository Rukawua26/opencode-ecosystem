# AGENTS.md — opencode-ecosystem

Reglas especificas de este repositorio. Complementan (no sustituyen) `~/AGENTS.md`.

## Stack y estilo

- Python stdlib solamente; no añadir dependencias sin autorizacion explicita.
- i5-1235U / 8GB: nada de procesos permanentes pesados ni polling agresivo.
- Espanol en docs, skills y mensajes; sin acentos en el contenido de skills.

## Verificacion obligatoria

- Tests: `python3 -m unittest discover -s control/tests`.
- Skills: `python3 validate-skills.py skills`.
- Runtime: `./opencode-ecosystem status` debe terminar en `[ok] sin drift`.
- Cierre: `./verify.sh` verde y `scripts/qa-gate.sh --strict` exit 0.

## Limites duros

- No migrar el esquema SQLite (`control/db.py`) sin autorizacion explicita.
- No persistir stdout completo de agentes; solo resumenes acotados.
- No tocar memoria viva (`~/.config/opencode/memory/`), receipts, backups ni logs como parte de features ordinarias.
- No commitear, mergear, pushear ni crear PR sin peticion explicita.
- Worktrees: nunca borrarlos con `--force` y nunca automaticamente.

## Reutilizacion

- Antes de crear una funcion, helper, formato o modulo, buscar la
  implementacion equivalente existente (`rg` dirigido) y reutilizarla.
- Si no se reutiliza, justificar brevemente en el documento ODD.
