# Spec: Safe Installer Sync and Public Documentation

## Problema

La reinstalacion normal preserva personalizaciones, pero tambien conserva archivos
gestionados obsoletos y no actualiza archivos gestionados existentes. El README
publico contiene evidencia historica y cifras no medidas que distraen del estado
real de v1.9.0. Ademas, no existe una medicion opt-in de respuestas JSON de los
modelos locales.

## Alcance

- Limpiar el README raiz para mostrar solo capacidades actuales y verificables.
- Anadir sincronizacion explicita `--sync` / `-Sync` a ambos instaladores.
- Mantener un manifiesto local de archivos gestionados por el ecosistema.
- Preservar archivos no incluidos en el manifiesto y la configuracion principal.
- Crear backups antes de reemplazar o retirar archivos gestionados.
- Anadir un eval local opt-in de formato JSON, fuera del CI bloqueante.
- Aislar los tests de scaffolders y rechazar nombres que puedan escapar de sus
  rutas o alterar el codigo generado.

## Fuera de Alcance

- Eliminar automaticamente archivos sin un manifiesto previo.
- Reemplazar `opencode.jsonc` personalizado durante `--sync`.
- Convertir security-review en middleware o agregar nuevos bloqueos runtime.
- Comparar con proveedores comerciales o ejecutar modelos en CI.

## Requisitos

### R1 - README publico

El README raiz MUST describir v1.9.0 sin bloques historicos de sesiones locales,
sin porcentajes de ahorro no medidos y sin componentes deshabilitados presentados
como activos.

### R2 - Sincronizacion explicita

Los instaladores MUST aceptar `--sync` en Bash y `-Sync` en PowerShell. La
reinstalacion sin esa opcion MUST conservar el comportamiento actual.

### R3 - Preservacion

`--sync` MUST actualizar archivos presentes en la distribucion, MUST preservar
`opencode.jsonc` y MUST preservar archivos del usuario no listados en el
manifiesto previo.

### R4 - Retirada segura

`--sync` MUST retirar un archivo solo si aparece en el manifiesto previo y ya no
aparece en el manifiesto actual. MUST crear una copia antes de reemplazarlo o
retirarlo, MUST preservar `opencode.jsonc` y el propio manifiesto incluso ante
una entrada manipulada, y MUST limitar los backups sync a 10 ejecuciones.

### R5 - Primera sincronizacion

Si no existe manifiesto previo, `--sync` MUST actualizar los archivos actuales y
crear el manifiesto, pero MUST NOT intentar podar archivos desconocidos.

### R6 - Paridad y pruebas

Bash y PowerShell MUST cubrir instalacion, preservacion, sync, backup y pruning
seguro en sus pruebas de plataforma.

### R7 - Eval local

El repositorio SHOULD ofrecer un comando manual que ejecute casos acotados contra
los modelos locales y reporte cuantas respuestas cumplen JSON y esquema. Este
comando MUST NOT ejecutarse en el CI normal.

### R8 - Mejoras locales verificadas

Las mejoras instaladas de guardrails y metricas MUST incorporarse al repositorio
con tests de comportamiento antes de ejecutar sync, para evitar una regresion del
runtime local.

### R9 - Scaffolders seguros y deterministas

Los scaffolders Bash MUST aceptar solo nombres kebab-case seguros. Sus tests MUST
ejecutarse fuera del checkout, MUST limitar el tiempo de cada proceso y MUST NOT
crear artefactos que otros tests puedan enumerar. Al ser herramientas POSIX, sus
tests MUST ejecutarse solo en plataformas compatibles. El scaffolder de plugins
MUST rechazar palabras reservadas JavaScript y destinos que sean symlinks.

## Escenarios de Aceptacion

### Escenario A - Actualizacion gestionada

Given una instalacion con un archivo gestionado modificado y un archivo custom
When se ejecuta el instalador con sync
Then el archivo gestionado se actualiza con backup y el archivo custom permanece.

### Escenario B - Archivo gestionado retirado

Given un manifiesto previo que contiene un archivo que ya no distribuye el repo
When se ejecuta sync
Then el archivo se respalda, se elimina y desaparece del manifiesto nuevo.

### Escenario C - Primera adopcion

Given una instalacion antigua sin manifiesto
When se ejecuta sync
Then se actualizan archivos actuales, se crea el manifiesto y no se borran
archivos desconocidos.

### Escenario D - README verificable

Given el README raiz
When corre `npm run check-docs`
Then falla ante referencias historicas prohibidas, claims no medidos o una version
distinta de v1.9.0.

### Escenario E - Eval opt-in

Given Ollama y los modelos fijados disponibles
When se ejecuta el eval manual
Then produce JSON con total, validos, fallos y tasa de exito por modelo.

### Escenario F - Nombre de scaffold invalido

Given un nombre con traversal, espacios o sintaxis ejecutable
When se invoca un scaffolder
Then termina con error antes de crear archivos o ejecutar contenido del nombre.

### Escenario G - Suite paralela

Given Vitest ejecuta coverage y enumera los plugins del checkout
When corren los tests de scaffolders
Then sus artefactos existen solo en un directorio temporal unico y no interfieren
con ningun otro archivo de test.
