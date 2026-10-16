# Base reversible de la ampliacion sync

Seccion `cmd_sync` previa a la ampliacion autorizada (el resto del ejecutable
no se modifica). El ejecutable completo previo, con trabajo ajeno aun sin
commit, tenia SHA-256
`65e865e2dc58c6d7b3d61f4de8c1556f60c9621c18044962185473762b4514b2`.
Para rollback restaurar solo esta funcion, no el archivo desde HEAD:

```bash
cmd_sync() { # sync --apply : ECO -> CFG con backup; jsonc solo con config-apply --apply
  local apply="${1:-}"
  if [ "$apply" != "--apply" ]; then echo "uso: $0 sync --apply"; return 2; fi
  python3 "$ECO/validate-skills.py" "$ECO/skills" || return 1
  local tree
  for tree in "$CFG" "$ECO/configs" "$ECO/skills" "$ECO/scripts" "$ECO/memory" "$ECO/commands"; do
    safe_tree "$tree" || return 1
  done
  mkdir -p "$CFG/scripts" "$CFG/skills" "$CFG/memory/topics" "$CFG/commands" || return 1
  for tree in opencode.jsonc dcp.jsonc cron-jobs.json; do
    backup_dest "$CFG/$tree" || return 1
    cp "$ECO/configs/$tree" "$CFG/$tree" || return 1
  done
  cp -r "$ECO/skills/." "$CFG/skills/" || return 1
  cp "$ECO"/scripts/*.sh "$CFG/scripts/" || return 1
  chmod +x "$CFG/scripts/"*.sh || return 1
  if [ -d "$ECO/commands" ]; then
    for f in "$ECO"/commands/*.md; do
      [ -e "$f" ] || continue
      backup_dest "$CFG/commands/$(basename "$f")" || return 1
      cp "$f" "$CFG/commands/" || return 1
    done
  fi
  # Scripts de memoria gestionados: copia siempre desde la fuente (con backup),
  # para que el runtime no pueda divergir en silencio del repo.
  for s in kairos.sh autodream.sh; do
    backup_dest "$CFG/memory/$s" || return 1
    cp "$ECO/memory/$s" "$CFG/memory/$s" || return 1
  done
  # Memoria viva (MEMORY.md) y logs/topics: se sembran solo si faltan; nunca se
  # sobrescribe un archivo existente, porque son estado del usuario.
  if [ ! -e "$CFG/memory/MEMORY.md" ]; then
    cp "$ECO/memory/MEMORY.md" "$CFG/memory/MEMORY.md" || return 1
  fi
  chmod +x "$CFG/memory/kairos.sh" "$CFG/memory/autodream.sh" || return 1
  managed_list > "$MANAGED" || return 1
  echo "[ok] sync aplicado"
}
```
