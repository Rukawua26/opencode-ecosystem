# Feature: Contrato ODD de reutilizacion y aceptacion

## Objetivo

Endurecer el flujo ODD a partir del analisis del video 7CZLMLnfIiw: el plan es
el contrato, la reutilizacion se busca antes de crear y los criterios de
aceptacion son explicitos. Worktree manual como capacidad opcional documentada.

## Problema y por que

Un agente sin plan ni reglas puede crear duplicados porque no busco lo ya
existente. Los documentos ODD actuales no exigen seccion "No romper" ni
registro de reutilizacion, y ningun AGENTS.md local protege las reglas del repo.

## Alcance

Incluye:
- secciones No romper / Criterios de aceptacion / Reutilizacion investigada en
  `organic-workflow-lite`;
- regla de busqueda de reutilizacion en `odd-worker` y check en `odd-verifier`;
- `AGENTS.md` especifico del repo;
- piloto en worktree manual validando el nuevo contrato;
- documentacion del procedimiento manual en `control/README.md`.

Excluye:
- modo worktree automatizado en el runner (sin evidencia de necesidad);
- migracion SQLite, nuevos campos, limpieza automatica, `--force`;
- commits automaticos del worker o merges.

## No romper

- 108 tests actuales del control-plane deben seguir pasando.
- Contrato `SUMMARY`/`QUESTION`/`RESULT` y estado `waiting` intactos.
- `./opencode-ecosystem status` sin drift al final.

## TDD

- Modo: off
- Fuente: default
- Runner: `python3 -m unittest discover -s control/tests`
- Checks funcionales obligatorios (piloto real worker/verifier en worktree).

## Tareas

- [x] T1 Secciones No romper / criterios / reutilizacion en organic-workflow-lite.
- [x] T2 Regla de busqueda de reutilizacion en odd-worker.
- [x] T3 Check de reutilizacion/No romper en odd-verifier.
- [x] T4 AGENTS.md especifico del ecosistema.
- [ ] T5 Piloto: worktree manual + worker + verifier + integracion decidida.

## Criterios de aceptacion

- [ ] Skills validas y sin drift tras sync.
- [ ] Tests del control-plane verdes.
- [ ] Piloto: el worker documenta la reutilizacion investigada.
- [ ] El verifier contrasta sin falsos positivos.
- [ ] Worktree manual eliminado sin `--force` y checkout principal intacto.

## Decisiones aceptadas

- D1: worktree manual/documentado, no automatizado en el runner (YAGNI, falta
  trigger real de tareas paralelas).
- D2: sin nueva columna SQLite; la evidencia de reutilizacion vive en el doc ODD.
- D3: el worker no modifica el documento ODD del plane al salvarse en worktree;
  el orquestador consolida la evidencia tras la revision humana.

## Reutilizacion investigada

- Flujo de delegacion existente: `control/runner.py` (workspace por tarea).
- Plantilla ODD existente: `skills/organic-workflow-lite/SKILL.md` punto 4.
- No se crea skill nueva: se endurece la existente.

## Evidencia

- T1-T4: Estado: passed. `validate-skills` 10/10, sync sin drift, 108/108 tests.
  Nota: una sesion paralela revirtio la primera aplicacion via `publish --yes`;
  reaplicado y commitado en esta sesion (prioridad confirmada por el humano).
- T5: pending.

## Progreso

- Estado: en_curso
- Ultima tarea: T4
- Siguiente paso: T5 piloto en worktree manual
- Bloqueos: piloto T5 requiere base Git limpia; quedan cambios ajenos (Etapa 10A)
  sin commit en el arbol — decision humana pendiente sobre como proceder.
