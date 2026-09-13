---
name: git-atomic-committer
description: Commit, staged diff y estilo de mensajes del repo. Usar cuando un cambio deba dividirse en commits atomicos sin mezclar trabajo ajeno.
---

# git-atomic-committer
1. Solo crea commits si el usuario lo pide explicitamente.
2. Revisa `git status`, el diff completo y el log reciente antes de preparar grupos.
3. Stagea solo ficheros intencionados; nunca reviertas ni incluyas cambios ajenos.
4. Separa por unidad de trabajo: tests y docs viajan en el mismo commit que el codigo que verifican o describen. Infere el estilo de mensaje del `git log` del repo; usa Conventional Commits `tipo(alcance): mensaje` solo si el repo ya los usa, con task ID si existe. El mensaje explica el resultado, no la lista de ficheros.
5. No mezcles refactor y feature en el mismo commit.
