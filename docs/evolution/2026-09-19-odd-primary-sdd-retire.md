---
nombre: 2026-09-19-odd-primary-sdd-retire
fecha: 2026-09-19
estado: en_observacion
afecta: [skills, configs, reglas, docs]
fuente: gentle-ai
---

# ODD primario y retirada del SDD activo

## Por que

ODD-lite ya era el flujo predeterminado, pero seis comandos, dos subagentes y
reglas SDD mantenian dos caminos activos. El runner tampoco distinguia una tarea
bloqueada de una completada cuando el agente terminaba con codigo cero. Evidencia:
video de Gentleman Programming del 2026-09-18, inventario local y piloto del
control-plane.

## Antes

- SDD activo mediante seis comandos y `sdd-implement`/`sdd-verify`.
- ODD sustancial usaba un documento unico, pero el runner seguia acoplado a SDD.
- Exit 0 siempre terminaba en `done`, incluso si el agente declaraba bloqueo.
- Config de agentes dependia de traduccion legacy (`agent`, `prompt`, `permission`).

## Despues

- ODD es el unico flujo activo; specs antiguas quedan como historial read-only.
- `odd-worker` implementa una tarea atomica y `odd-verifier` verifica en contexto fresco.
- Contrato acotado `SUMMARY`/`QUESTION`/`RESULT` sin persistir stdout completo.
- `RESULT: blocked` produce `waiting`, libera lease y no consume intento.
- Config de agentes usa sintaxis OpenCode V2 (`agents`, `system`, `permissions`).
- Los seis comandos y los agentes SDD fueron retirados.

## Beneficio

- Un solo flujo y un solo artefacto recuperable por feature.
- Menos prompts, comandos y reglas activas.
- Bloqueos humanos visibles y reintentables sin perder intentos funcionales.
- Sin plugins, sockets, nuevas dependencias ni migracion SQLite.

## No regresion

- Base reversible: commit previo `9a4ef7f` en `~/opencode-ecosystem` y backups
  generados por `sync --apply` en `~/.config/opencode`.
- Se conservan lease, timeout, reintentos, dead-letter, politica de modelos,
  sensibilidad y verificacion determinista.
- Se conservan specs legacy, historial de evolucion y registros SDD antiguos.
- No se crean ramas, commits, pushes ni PR automaticamente.

## Verificacion

- `python3 -m unittest discover -s control/tests`: 88/88 OK.
- `python3 validate-skills.py skills`: 10/10 validas.
- `git diff --check`: OK.
- Piloto real: #7 odd-worker done, #8 odd-verifier done, marcador
  `ODD_PILOT_OK`; #9 waiting con attempts=0, decision D6, reintento done;
  #10 odd-verifier done.
- `sync --apply` y `status`: runtime propagado, sin drift y sin comandos SDD.
- `opencode debug config`: `odd-worker`, `odd-verifier`, `title`; sin agentes SDD.
- `qa-gate.sh --strict`: exit 0; `verify.sh`: verde; `plugin_doctor.sh`: sano.
- Control doctor: ok, 3/3 timers, cola sin pending/waiting/running ni errores.
- Higiene: recomienda prune de 4 backups y reset de observations; no se aplica por
  quedar fuera del alcance funcional de esta evolucion.

## Periodo prudencial

- Mantener `estado: en_observacion` durante varias tareas ODD reales o 2 semanas.
- Estable si no aparecen comandos SDD, `waiting` conserva intentos y el encadenado
  worker/verifier no produce falsos positivos.
- Revertir si ODD bloquea trabajo valido, pierde decisiones o no encadena verifier.
- Rollback: restaurar desde Git/backups, `sync --apply` y reiniciar OpenCode.

## Fuente

- `~/docs/sources/gentle-ai-analysis.md` y video `MbKl8KD9pKY` (2026-09-18).
