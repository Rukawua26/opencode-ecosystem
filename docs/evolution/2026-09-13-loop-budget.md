---
nombre: 2026-09-13-loop-budget
fecha: 2026-09-13
estado: en_observacion # propuesto | aplicado | en_observacion | verificado | revertido
afecta: [skills] # skills | configs | scripts | memoria | git | reglas | docs
fuente: video # propio | gentle-ai | noffolo | otro-repo | video (curso Gentleman Programming)
---

# Presupuesto de correccion en code-forge-fix-lite (loop budget)

## Por que
`code-forge-fix-lite` guiaba reproducir -> causa raiz -> fix -> verificar, pero no
tenia limite de intentos ni protocolo de escalacion. Si un fix fallaba repetidamente,
nada obligaba al agente a detenerse y pedir ayuda: el bucle podia seguir en silencio
gastando tokens y RAM (i5-1235U, 8 GB). Evidencia: analisis del fragmento 1:00-1:30
del curso de Gentleman Programming; el hueco real es de nuestro skill, no del video.

## Antes
Cuatro pasos sin presupuesto: ante fallos repetidos del fix, el agente podia iterar
indefinidamente sin escalar al humano.

## Despues
Paso 4 nuevo: maximo 3 intentos de fix por bug; si fallan, se detiene el bucle, se
resume la causa raiz con evidencia y se pide intervencion humana. El paso de
`observations.log` pasa a ser el paso 5 (mismo contenido).

## Beneficio
- Tope de gasto por bug: maximo 3 ciclos de fix/verificar antes de escalar.
- Sintomas de bloqueo se reportan en vez de ocultarse tras N iteraciones.

## No regresion
- Los 4 pasos originales siguen intactos (trazado, test, fix minimo, verificacion).
- El paso de observations.log conserva texto y regla de aprobacion; solo cambia de numero.
- La description de la skill no cambia: los triggers de carga quedan iguales.

## Verificacion
- `python3 ~/opencode-ecosystem/validate-skills.py ~/opencode-ecosystem/skills` -> `[ok] 9 skills valid`.
- `./opencode-ecosystem sync --apply` -> sin drift.
- `opencode debug skill` -> code-forge-fix-lite carga con el paso 4 nuevo.
- Base reversible: commit `0acc29a` contiene el estado anterior en Git.

## Periodo prudencial
- Vigilancia hasta 2026-09-27 (mismo ciclo que la alineacion gentle-ai).
- Senal de estabilidad: al menos un bug real resuelto sin exceder 3 intentos y sin
  falsas escalaciones (escalar cuando aun habia margen razonable).
- Senal de revertir: escalaciones prematuras constantes o bloqueos no detectados.
- Rollback: `git revert` del commit de este cambio, validar y `sync --apply`.

## Fuente
- Curso de desarrollo con IA (Gentleman Programming, fragmento 1:00-1:30): loop
  engineering con maximo 3 intentos y escalacion al humano.
- **DEJADO del mismo video**: persona "mentor gentleman" (tokens de piso fijo sin
  valor medido), estructura plana `.opencode/specs/` (nuestro `spec/features/` es
  superset), Skill Harvester auto-generada (viola consentimiento fail-closed;
  ver `~/docs/sources/curso-skills-gentleman-analysis.md`).
