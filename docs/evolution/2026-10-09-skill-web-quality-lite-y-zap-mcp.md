---
nombre: 2026-10-09-skill-web-quality-lite-y-zap-mcp
fecha: 2026-10-09
estado: aplicado
afecta: [skills, docs]
fuente: propio
---

# Skill web-quality-lite + guia de ZAP MCP por proyecto

## Por que
Al crear webs se repetian los mismos requisitos basicos (legal, cookies, HTTPS,
SEO, accesibilidad, rendimiento, conversion) sin una lista comun ni evidencias;
ademas, ZAP no se podia manejar desde OpenCode sin dejar un proceso pesado
siempre arrancado en una maquina de 8GB. El humano aporto una lista de 20
puntos y aprobo el plan en sesion.

## Antes
- Sin estandar de calidad web; cada proyecto arrancaba sin referencia comun.
- ZAP solo se usaba a mano, fuera del flujo del agente.

## Despues
- Nueva skill `web-quality-lite` con los 20 criterios agrupados, estados
  honestos (verificado/pendiente/no aplicable/revision humana) y una regla
  extra de seguridad de stack. Se carga bajo demanda, sin coste de contexto
  cuando no hace falta.
- `docs/zap-mcp.md` con la plantilla de MCP de ZAP **por proyecto**
  (`disabled: true`, clave por `{env:ZAP_MCP_KEY}`, sin `--global`), reglas de
  uso y pendientes de verificacion del endpoint.
- README actualizado: 13 skills.

## Beneficio
- Contexto: los 20 puntos solo entran cuando se invoca la skill.
- RAM: ZAP no corre por defecto; el MCP solo existe donde el proyecto lo pida.
- Reutilizacion: proximas webs heredan el estandar sin repetir decisiones.

## No regresion
- Las 12 skills anteriores permanecen intactas y validando.
- Ninguna configuracion global conecta con ZAP.
- Estado previo recuperable: `git status` muestra solo ficheros nuevos
  (skill, doc, ODD, evolution) y lineas anadidas en README; revertir =
  borrar esos ficheros y deshacer 3 ediciones menores del README.

## Verificacion
- `python3 validate-skills.py skills` -> OK (13 skills).
- `python3 -m unittest discover -s control/tests` -> OK (skips esperados).
- `./opencode-ecosystem sync --apply` -> instala web-quality-lite en runtime.
- `./opencode-ecosystem status` -> [ok] sin drift.
- `ls ~/.config/opencode/skills/web-quality-lite` -> SKILL.md presente.
- `./verify.sh` -> verde; `scripts/qa-gate.sh --strict` -> 0 (sin staged, no aplicable).
- Endpoint MCP de ZAP (HTTP vs Secure Only): pendiente de smoke-test con ZAP
  instalado; documentado en `docs/zap-mcp.md`.

## Periodo prudencial
- Estable cuando se use la skill en un proyecto real y el smoke-test de ZAP
  confirme el endpoint; se actualizare entonces `docs/zap-mcp.md`.
- Rollback: `rm -rf skills/web-quality-lite docs/zap-mcp.md` y deshacer las
  3 lineas del README; `web-quality-lite` desaparece del runtime en el sync.
- Senal de fallo: validate-skills/verify dejan de pasar o el MCP global se
  conecta por accidente en proyectos ajenos.

## Fuente (si aplica)
No aplica; redaccion propia a partir de la lista del humano, la doc oficial de
OpenCode V2 (mcp-servers) y la doc oficial del add-on MCP Integration de ZAP.
