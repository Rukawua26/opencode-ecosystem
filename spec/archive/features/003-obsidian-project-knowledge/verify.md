# Verification: Obsidian Project Knowledge

## Verdict

**PASS** — implementación y outputs verificados el 2026-08-11.

- Receipt Tier 3 aprobado: `r_1786468441333_5e917471-2be1-4d40-8835-c52d04c86d4c`
- Candidate ID: `c4d8a0615c914fe2a806564d412eee853669844be404f7d75ce7810dd3b8f9ab`
- Gate: `pass` (`receipt_approved`)

## Matriz de cumplimiento

| Requisito | Estado | Evidencia |
|---|---|---|
| REQ-001 Descubrimiento acotado | PASS | 13 proyectos top-level detectados mediante marcadores; no recursivo |
| REQ-002 Privacidad y límites | PASS | stdlib, 128 KiB por archivo, ocultos/symlinks/medios ignorados |
| REQ-003 Escritura segura | PASS | dry-run por defecto, `--apply`, create-only, notas curadas con hashes intactos |
| REQ-004 Metadatos determinísticos | PASS | 11 notas nuevas con frontmatter requerido, stack/resumen/área sin LLM |
| REQ-005 Relaciones útiles | PASS | tokens completos en README/AGENTS, aristas dirigidas y links `[[stem\|alias]]` |
| REQ-006 Canvas nativo | PASS | 13 file nodes, 5 grupos, 17 aristas, IDs únicos, cero endpoints colgantes |
| REQ-007 Grafo existente | PASS | `_graph_gen.py --vault`, HTML escapado y escrituras atómicas; segunda ejecución sin cambios |
| REQ-008 Skill OpenCode | PASS | skill válido en fuente, paquete npm y despliegue global |
| REQ-009 Fuentes no confiables | PASS | contrato ignora instrucciones/comandos y limita prompts |
| REQ-010 Sin sobrescritura | PASS | destino confinado al vault, preview, symlinks fail-closed y create-only |
| REQ-011 Integración/despliegue | PASS | tres copias byte-idénticas; instalador reporta 21 skills |
| REQ-012 Eficiencia | PASS | catálogo sin LLM/daemon; ingest limita a 5 notas y una síntesis local |

## Verificación ejecutada

| Comando/chequeo | Resultado |
|---|---|
| `npm test` | PASS — 6 archivos, 51 tests |
| `npm run lint` | PASS |
| `npm run test:install` | PASS — 21 skills, 10/10 checks |
| `npm run test:hooks` | PASS |
| `python3 -m unittest ~/docs/scripts/test_discover_projects.py` | PASS — 11 tests |
| Segunda ejecución real `discover_projects.py --apply` | 0 notas, Canvas/MOC/HTML sin cambios |
| Validación JSON Canvas | 13 proyectos, 17 aristas, IDs/endpoints válidos |
| Validación de wikilinks generados | todos apuntan a stems existentes |
| Hashes `pbot.md`, `vozart.md`, `opencode-config-backup.md` | sin cambios |

## Hallazgos corregidos

- Falsos positivos y dirección incorrecta en referencias.
- Wikilinks rotos cuando nombre y filename diferían.
- Resúmenes `---` por frontmatter de README.
- Plantillas incluidas en el grafo.
- XSS almacenado potencial en `grafo.html`.
- Escrituras no atómicas de MOC/HTML.
- Generador que ignoraba `--vault` y ejecutaba un wrapper del vault.
- Argumentos shell y destinos insuficientemente confinados en el skill.
- Symlinks de nota colgantes y marcador MOC ausente ahora fallan antes de escribir.

## Estado operativo

- El Canvas está disponible en `~/docs/canvases/Mapa de Proyectos.canvas`.
- La tabla filtrable está disponible en `~/docs/Projects.base`.
- El grafo Mermaid está en `~/docs/_MOC.md`; la vista HTML está en `~/docs/grafo.html`.
- El skill está desplegado en `~/.opencode/skills/obsidian-ingest/SKILL.md`.
- OpenCode debe reiniciarse una vez para cargar el skill nuevo.
