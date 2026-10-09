# calidad-web-y-zap-mcp

Estado: en progreso
Autorizado por: el humano (09 oct 2026, tras plan aprobado en chat)

## Objetivo
Incorporar el estandar de calidad web de 20 puntos al ecosistema para todo
proyecto web nuevo o existente, y preparar la integracion opcional de ZAP via
MCP oficial, habilitada solo por proyecto.

## Problema y por que
Sin criterios centralizados, cada web nueva nace sin revisar legal, SEO,
accesibilidad, rendimiento ni seguridad. Ademas, no existia via para que el
agente conduzca ZAP sin instalarlo globalmente (RAM 8GB, filosofia de ahorro).

## Alcance
- Skill `web-quality-lite` en `skills/web-quality-lite/SKILL.md`.
- Guia + plantilla de MCP de ZAP por proyecto en `docs/zap-mcp.md`.
- Fila en la tabla de skills de `README.md` y conteo 12 -> 13.
- Documento de evolucion en `docs/evolution/2026-10-09-skill-web-quality-lite-y-zap-mcp.md`.
- Validaciones del repo y sync al runtime.

## Excluye
- Instalar ZAP o Docker; arrancar ningun escaneo.
- Configurar MCP de ZAP globalmente ni en proyectos concretos.
- Auditoria de webs reales (eso viene cuando el usuario pida revisar una web).
- Commits/push (prohibido sin peticion explicita).

## Restricciones
- Espanol sin acentos en skills; Python stdlib; sin procesos permanentes.
- No tocar el trabajo ajeno sin commit ya presente en el arbol.
- ZAP: solo localhost, clave por variable de entorno, disabled por defecto,
  escaneo activo siempre con autorizacion explicita y alcance acotado.

## No romper
- Las 12 skills existentes deben seguir validando.
- `./verify.sh` verde y `scripts/qa-gate.sh --strict` exit 0.
- Cambios ajenos sin commit no se tocan.

## TDD
Modo: off
Fuente: default
Runner: no disponible (solo documentacion y SKILL.md; se valida con validate-skills.py e verify.sh)

## Tareas
- [x] T1 Crear `skills/web-quality-lite/SKILL.md`
- [x] T2 Crear `docs/zap-mcp.md` con guia y plantilla por proyecto
- [x] T3 Actualizar tabla de skills en `README.md` (12 -> 13)
- [x] T4 Documento de evolucion en `docs/evolution/`
- [x] T5 Validar: validate-skills, unittest, sync --apply, status sin drift, verify.sh, qa-gate strict
- [x] T6 Actualizar conteo de skills en `~/AGENTS.md`

## Criterios de aceptacion
- `python3 validate-skills.py skills` OK incluyendo web-quality-lite.
- `~/.config/opencode/skills/web-quality-lite/` existe tras sync.
- `./opencode-ecosystem status` termina en "[ok] sin drift".
- `./verify.sh` verde; `scripts/qa-gate.sh --strict` exit 0.
- Ninguna configuracion global emite conexion a ZAP por defecto.

## Reutilizacion investigada
- `ui-ux-master` cubre diseno, tokens, foco y contraste medido: se referencia,
  no se duplica.
- `qa-gate` sigue siendo la puerta anti-slop del closing; no se toca.
- Estructura y estilo de skills tomados de las existentes (frontmatter +
  cuerpo breve en espanol sin acentos).

## Decisiones aceptadas
- Skill (bajo demanda) en vez de regla con los 20 puntos embebidos: ahorra contexto.
- MCP de ZAP: plantilla documentada, nada global; el smoke-test del endpoint
  (HTTP vs Secure Only HTTPS) queda pendiente hasta tener ZAP instalado.
- Delegacion odd-worker omitida: cambio 100% de documentacion, sin codigo.

## Evidencia
- T5 validate-skills: passed. `python3 validate-skills.py skills` -> "[ok] 13 skills valid".
- T5 unittest: passed. `python3 -m unittest discover -s control/tests` -> OK, 233 tests, 1 skip esperado.
- T5 sync + status: passed. `sync --apply` ok (backups .bak creados) y `status` -> "[ok] sin drift".
  `~/.config/opencode/skills/web-quality-lite/SKILL.md` presente en runtime.
- T5 qa-gate --strict: passed. RC=0 (sin staged: no aplicable; rutas sensibles comprobadas).
- T5 verify.sh: failed en la primera pasada por `plugin_doctor` rc=1: error PREEXISTENTE
  no relacionado con este cambio — deriva de version pineada de OpenCode
  (pin 2.0.22 vs binario 2.0.26), sin plugins .js ni hooks activos. Solucion
  documentada por el propio script: `~/tools/plugin_doctor.sh pin` tras
  comprobar que la sesion actual funciona con la 2.0.26. Tras pinear,
  `plugin_doctor.sh` -> "RESULTADO: plugins sanos" y `./verify.sh` -> verde
  (ligero warn informativo de hygiene triggers, preexistente, no bloqueante).
- Endpoint/TLS del MCP de ZAP: pending (requiere ZAP instalado; marcado en docs/zap-mcp.md).

## Progreso
- Ultima tarea: T6.
- Siguiente paso: fuera de este documento — instalar ZAP y hacer el smoke-test cuando el usuario lo decida.
- Bloqueos: ninguno.
