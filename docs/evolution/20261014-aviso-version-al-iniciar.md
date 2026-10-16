---
nombre: 20261014-aviso-version-al-iniciar
fecha: 2026-10-14
estado: en_observacion
afecta: [scripts, docs]
fuente: propio
---

# Lanzador explicito con aviso de version

## Por que
El pin se comprobaba solo al invocar plugin_doctor; abrir OpenCode no avisaba.

## Antes
El binario directo abria sin comparar versiones. Sigue disponible igual.

## Despues
`~/opencode-ecosystem/opencode-checked` consulta version local con timeout de
3 segundos y compara el pin existente. Pregunta solo sin argumentos y con TTY.
Aceptar solo registra una respuesta en pantalla: el agente no la recibe.
No hay prompts inyectados, comandos de revision ni cambios automaticos.
Tras reapertura de T1 por el verificador, el probe usa pipe con lectura acumulada
maxima de 257 bytes (rechaza mas de 256), sin archivo temporal ni captura a disco.
El plazo monotonic global de 3 segundos cubre lectura y espera de salida;
al exceder salida o plazo se mata y recolecta el proceso.
OSError/UnicodeError al leer la respuesta implican rechazo, aviso fijo sin
detalles de excepcion y apertura normal, sin consentimiento.

## Beneficio
Aviso optativo, sin dependencias, red, polling ni proceso residente adicional.

## No regresion
- Base reversible Git: `8bc6069231768db00841dd679655bd168695b5f7` contiene
  README anterior; lanzador y tests son nuevos y pueden retirarse selectivamente.
- Antes de editar: configs/opencode.jsonc y docs/zap-mcp.md ya modificados;
  documentos de compactacion y ODD ya presentes. Se preservan sin restaurarlos.
- CLI directa, argumentos con espacios y estado de salida se conservan.
- No se usa sync: copia configuracion y crea backups, innecesarios para T1.

## Verificacion
Ver evidencia de comandos y resultados de T1 en
`odd/tasks/aviso-version-al-iniciar.md`. Tests aislados, sin pin ni binario real.
QA strict sin staged no audita las nuevas lineas; revision manual adicional.
Regresiones aisladas con productor continuo en bloques de 1 MiB, timeout con
stdout abierto, y fallos de lectura que conservan exec; args/exit siguen cubiertos.
Reapertura: 15 tests focales OK; suite completa 309 tests OK (1 omitido),
13 skills validas, status sin drift, verify verde y QA strict exit 0.

## Periodo prudencial
- Mantener en observacion durante las proximas aperturas humanas y un cambio de
  version real; tests no equivalen a verificacion visual de TUI.
- Estable si avisa solo cuando corresponde y no altera argumentos ni permisos.
- Si bloquea o induce consentimiento falso, dejar de usar este comando y volver
  a `opencode` directo; retirar solo los archivos nuevos y la seccion README.
- La base Git permanece recuperable, sin commits ni borrado de trabajo ajeno.

## Fuente (si aplica)
Propio: contrato de pin de plugin_doctor y patron timeout de control/cli.py.
