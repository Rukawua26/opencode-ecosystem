# 007-skill-authoring-guard - Plan

1. Crear `validate-skills.py` en la raiz del ecosistema con Python stdlib.
2. Invocarlo antes de cualquier mutacion en sync/publish y desde verify.sh.
3. Documentar el flujo y añadir una politica compacta a AGENTS.md.
4. Probar fixtures validas e invalidas en `/tmp` sin tocar el runtime.
5. Probar fail-closed de sync/publish en HOME aislado.
6. Verificar skills activas, config, doctores, timers, drift y contexto.
