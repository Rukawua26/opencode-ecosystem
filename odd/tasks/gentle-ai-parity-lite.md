# Paridad conceptual gentle-ai v3.4 (paridad ligera)

## Objetivo

Acercar `opencode-ecosystem` al comportamiento conceptual de gentle-ai v3.4.0 manteniendo nuestra filosofia: autorizacion humana, ODD-lite, ahorro de memoria/tokens y ausencia de maquinaria innecesaria.

## Problema y por que

Gentle-AI publico v3.2.1-v3.4.0 tras nuestra ultima alineacion. Lo relevante es la disciplina de parl: delegacion obligatoria para trabajo sustancial, evidencia fall-closed, transiciones exactas y OpenCode V2 consciente de version. Hoy la disciplina esta descrita pero no esta completamente endurecida ni verificada por tests. Quien lo sufre: cualquier feature delegada, bloqueada, reanudada o con salida incompleta.

## Alcance

### Incluye

- Contrato ODD de delegacion y verificacion para trabajo sustancial.
- Fail-closed de resultados y continuaciones.
- Literalidad de `next_transition` con consumo explicito y bloqueo seguro.
- Recibos/evidencia ligera reutilizando eventos existentes.
- Pruebas evolucion y nota de analisis de origen.

### Excluye

- Migracion del esquema SQLite.
- RDD completo, receipts criptograficos, lineage, snapshots, worktrees ni store-reset.
- Engram, telemetria VictoriaMetrics, RTK, TUI, Gentle Shell, binario Go.
- Commits automaticos, ramas, push, PR o release.
- Nuevos procesos, daemons, dependencias externas o memoria adicional.

## Restricciones

- Python stdlib solamente.
- i5-1235U/8GB: cero procesos permanentes ni polling agresivo.
- Espanol en docs/skills y sin acentos en contenido de skills.
- No persistir stdout completo ni secretos.
- Cierre Git solo si el humano lo pide explicitamente.

## No romper

- 108/108 tests actuales y style de control.
- `validate-skills.py skills`, `./verify.sh`, `qa-gate.sh --strict`.
- `status` sin drift tras sincronizar skills.
- API/panel sin prompts, workspace ni comandos expuestos.
- Workflows y configuraciones existentes que no se tocan.

## TDD

- Modo: on
- Fuente: usuario (iterar hasta terminar y corregir errores)
- Runner: `python3 -m unittest discover -s control/tests` + checks funcionales

## Tareas

- [x] T1 - Documentar contrato de paridad en skill y control documental.
- [x] T2 - Endurecer runner fail-closed, next_transition y evidencia minima.
- [x] T3 - Hacer obligatoria la delegacion ODD sustancial con ruta unica worker/verifier.
- [x] T4 - Añadir rebuild/version-aware ligero de OpenCode cuando la capacidad exista (sin proceso nuevo).
- [x] T5 - Dogfood: tarea pequena inline, tarea sustancial delegada, bloqueo, reanudacion y continuacion invalida.
- [x] T6 - Documentar evolution + revision del analisis gentle-ai y cerrar con verify/qa-gate.

## Criterios de aceptacion

- Una tarea sustancial ODD pasa siempre por `odd-worker`; una exitosa encadena `odd-verifier`.
- RESULT ausente o invalido nunca termina en `done`.
- `next_transition` se ejecuta verbatim; si falta o es invalido, queda `waiting`, nunca `dead` por inferencia.
- Errores de proveedor/cuota no consumen intentos funcionales.
- Los recibos/eventos permiten reconstruir estado sin stdout completo.
- Sin migracion SQLite ni dependencias nuevas.
- Verificaciones finales verdes y sin drift.

## Decisiones aceptadas

- 2026-09-21: adoptar paridad conceptual minima, no mecanica.
- 2026-09-21: reutilizar recibos y estados existentes en lugar de migrar SQLite.
- 2026-09-21: no activar RDD, telemetria, Engram ni entrega automatica.

## Reutilizacion investigada

- Runner existente: cola atomica, leases, estados, encadenamiento worker->verifier, scrub de salida.
- Recibo existente: `record_receipt` como evento acotado.
- Skill existente: `organic-workflow-lite` como contrato documental.
- Alternativas descartadas: RDD completo y nueva tabla/columnas SQLite por YAGNI.

## Evidencia

- T0 base - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests`; `python3 validate-skills.py skills`; `./opencode-ecosystem status`
  - Resultado: 108/108 OK; 10 skills valid; sin drift
- T1 - Estado: passed
  - Comando: edicion de `skills/organic-workflow-lite/SKILL.md` (items 7-8), `configs/opencode.jsonc` (prompts worker/verifier) y `control/README.md` (reglas del lanzador)
  - Resultado: contrato escrito: delegacion obligatoria para trabajo sustancial, SUMMARY/QUESTION obligatorios, NEXT_TRANSITION verbatim
- T2 - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests`
  - Resultado: 115/115 OK tras RED de 7 tests nuevos (fail-closed SUMMARY/QUESTION, recibo exacto, verifier encadenado, NEXT_TRANSITION ejecutado verbatim y fallo -> pending)
  - Nota: errata autodetectada y corregida — se propuso columna SQLite para la transicion; se revirtio para respetar "no migrar esquema" y la transicion pasa por el contrato acotado de stdout
- T3 - Estado: passed
  - Comando: revision de `skills/organic-workflow-lite/SKILL.md` item 7 + prompts `odd-worker`/`odd-verifier` en `configs/opencode.jsonc` + `control/README.md`; `./opencode-ecosystem sync --apply && ./opencode-ecosystem status`
  - Resultado: `[ok] 10 skills valid`, `[ok] sync aplicado`, `[ok] sin drift`
- T4 - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests` (test `test_opencode_missing_fails_explicit_as_infra`)
  - Resultado: 116/116 OK; binario ausente falla explicito como infra, sin capacidad nueva delegable (upstream usa Go/TUI que no adoptamos)
- T5 - Estado: passed
  - Comando: `python3 -m unittest discover -s control/tests`
  - Resultado: dogfood por escenarios reales del runner: pequena inline (qa-gate sin contrato -> done), sustancial delegada (worker -> verifier encadenado), bloqueo con QUESTION -> waiting sin consumir intento, blocked sin QUESTION -> contrato, NEXT_TRANSITION invalido -> pending (error_kind=transition), recibo exacto por tarea done
- T6 - Estado: passed
  - Comando: `./verify.sh && ./scripts/qa-gate.sh --strict`
  - Resultado: `[ok] verify verde`, qa-gate exit 0; evolution doc `docs/evolution/2026-09-21-paridad-gentle-ai-lite.md` y seccion nueva en `~/docs/sources/gentle-ai-analysis.md`

## Progreso

- Estado: completada; en observacion hasta 2026-10-05 o 2 features sustanciales delegadas con dogfood real
- Ultima tarea terminada: T6
- Siguiente paso: dogfood con proveedor real en el proximo trabajo sustancial; si los recibos no reconstruyen la ejecucion, abrir T7
- Bloqueos: ninguno
