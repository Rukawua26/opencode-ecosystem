---
nombre: 2026-09-25-readme-diagramas-y-capturas
fecha: 2026-09-25
estado: aplicado
afecta: [docs]
fuente: propio
---

# README: diagramas Mermaid y capturas del panel

## Por que

El README era un inventario de rutas: 94 lineas, sin jerarquia ni forma de
entender que hace el repo. Quien llega no ve el panel, ni el flujo ODD, ni el
plano de control, ni el alcance. Evidencia: la unica sesion de lectura era
recorrer la lista de directorios.

## Antes

Secciones planas (`Flujo oficial`, `Contenido`, `Plano de control`), sin imagen,
sin grafo y sin orden de lectura. `commands/` aparecia descrito aunque el
directorio esta vacio.

## Despues

- Abre con la captura real del panel y declara el perfil del repo en una tabla
  (stdlib, tests, skills, puerto, retencion).
- Tres grafos Mermaid embebidos: arquitectura ECO/CFG, flujo ODD y maquina de
  estados de la tarea del lanzador. La fuente editable queda en
  `docs/architecture/*.mmd`; el README la embebe.
- Secciones con orden de lectura: arranque rapido, anti-wipe, ODD, panel, skills,
  scripts, higiene, contenido, timers, verificacion, ambito, paridad, licencia.
- Tablas donde antes habia listas de 6 lineas; el bloque de autoria de skills
  passa a la seccion `Skills`.
- Correccion de exactitud: `commands/` se declara reservado y vacio, no poblado.

## Beneficio

- Los grafos se renderizan en GitHub sin servicio de terceros, sin SVG generado
  y sin binarios que se queden viejos: son texto que se revisa en el mismo diff
  que el README.
- Dos capturas de 200 KB en total muestran el producto sin ambigüedad.
- 0 dependencias nuevas: el render se comprobo en `/tmp` con mermaid + chromium
  y no queda nada en el repo.

## No regresion

- No se cambio ningun comando, script, skill, config ni permiso.
- Los comandos citados en el README existen y se ejecutaron (`status`, `sync`,
  `publish`, `capture`, `uninstall`, `control.cli task|receipt|doctor`).
- Las cifras del README son las medidas: 159 tests, 10 skills, 3 timers, 8765.
- Base versionada: commit previo `24feac4`; rollback `git revert f22f969`.

## Verificacion

- `node check.mjs docs/architecture/*.mmd` -> 3/3 renderizan (mermaid 11).
- Los 3 bloques extraidos del README -> 3/3 renderizan.
- `python3 readme_check.py` -> ninguna ruta de imagen ni link rota.
- `node audit.js` -> 1 h1, 13 h2, 7 tablas, 3 SVG, 0 restos de markdown.
- GitHub tras el push: `readme` API devuelve `data-type="mermaid"` x3, 2
  `<img>` con alt, 0 fences sin convertir.
- `python3 -m unittest discover -s control/tests` -> 159/159 OK (1 skipped).
- `python3 validate-skills.py skills` -> 10/10; `./opencode-ecosystem status`
  -> `[ok] sin drift`; `./verify.sh` -> `[ok] verify verde`.

## Periodo prudencial

- Duracion: hasta 2026-10-05 o hasta que tres lecturas nuevas del README no
  necesiten preguntar por el flujo.
- Estable si el README no se desincroniza del codigo (cifras y comandos).
- Senal de regresion: un comando citado que ya no exista, o un diagrama que
  contradiga `control/`.
- Rollback: `git revert f22f969`. No toca runtime, asi que el revert es local y
  no exige `sync`.

## Fuente

- `~/docs/sources/gentle-ai-analysis.md` para la seccion de paridad; el resto es
  propio.
