---
nombre: 20261014-fiabilidad-y-coherencia
fecha: 2026-10-14
estado: en_observacion
afecta: [scripts, docs]
fuente: propio
---

# Fiabilidad y coherencia

## Por que
La auditoria detecto memoria viva eliminable por manifiestos antiguos, errores
de copia ignorados, sustitucion destructiva de skills, cron fuera de status y
documentacion que prometia compactacion RAM y servidor sin mutaciones.

## Antes
CLI sin guardas suficientes ante errores; status no comparaba cron. Consultas
systemd fallidas podian conservar actividad inferida. README omitia ui-ux-master
y no diferenciaba archivo DCP de consumidor efectivo.

## Despues
T1 protege memoria/manifiestos y propaga fallos; publish prepara y valida skills
con rollback acotado. T2 compara cron y conserva desconocidos systemd sin verde
inferido. T3 alinea docs con codigo, sin activar DCP/ZAP ni cambiar RAM guard.
La aclaracion ZAP es aditiva: conserva entero el trabajo previo. Las notas de
compactacion mantienen su historial y agregan solo evidencia posterior.

## Beneficio
Menos falsos exitos y riesgo de borrado; cobertura/limites operativos explicitos.
No se atribuye ahorro medido de RAM/tokens ni atomicidad global.

## No regresion
- Base Git recuperable: `8bc6069231768db00841dd679655bd168695b5f7` para CLI,
  collect y docs rastreadas; sin commits/ramas nuevos. T1/T2 y sus verificaciones
  previas se conservan. No restaurar archivos completos sobre trabajo ajeno.
- README tenia el lanzador previo: se conserva su seccion completa sin cambios.
  ZAP tenia diff ajeno: solo se inserta un bloque identificado tras `Que es`.
- Los documentos de compactacion aun no versionados se conservan completos como
  prefijos: evolucion 4118 bytes, SHA-256
  `e5bdcdbd5e68e87f88cfdfc6532738070b498e8539c854c101370878c67d93d9`;
  ODD 4655 bytes, `7e5e4518e44613944421da6191e641a51f868d4c0e24d296be25f3847e2e1fee`.
  Solo se anade evidencia, no se pierde contenido previo recuperable.
- No cambios T3 en configs, scripts gestionados, skills, politica ODD/RAM,
  timers, modelos, memoria viva, receipts, backups ni logs manuales. No sync:
  CLI raiz/collect/server/docs no son gestionados; status real ya era verde.

## Verificacion
- `python3 -m unittest discover -s control/tests`: 340 tests OK, 1 skipped.
- `python3 validate-skills.py skills`: 13 validas.
- `./verify.sh`: exit 0, todos los controles obligatorios verdes, incluido
  plugin doctor; escribe su informe canonico de metadatos fuera del repo.
- `scripts/qa-gate.sh --strict`: exit 0, sin staged; no certifica unstaged.
- Config efectiva: consulta oficial `opencode api get /api/config` filtrada
  en memoria, sin volcar stdout ni secretos; comparacion/hash y status final
  registrados en el documento ODD. Un primer intento asumio objeto y encontro
  lista de fuentes: fallo local de extraccion, corregido sin mutar configuracion.
- Lentes reliability/risk focales: sin hallazgos reales nuevos en T1/T2;
  tests aislados con HOME temporal y systemd simulado, sin sleeps/reloj real.

## Periodo prudencial
- Mantener la base Git y contenido previo hasta varias operaciones autorizadas
  sin regresiones; no provocar mutaciones reales para fabricar evidencia.
- Reabrir ante falsos exitos, perdida de memoria o desconocidos saludables.
- Rollback solo de hunks propios tras revision/aprobacion; nunca restaurar
  README/ZAP/configs completos ni borrar los archivos nuevos ajenos. Eliminar
  una nota aditiva solo si se demuestra incorrecta; conservar historial valido.
- Verificacion independiente integrada T4 corresponde al padre y sigue pendiente.

## Fuente (si aplica)
Codigo y evidencia local. Decision minima respecto a Gentle: saneamiento primero;
no se incorpora codigo, runtime, framework ni nueva investigacion. Cambiar reglas
ODD o resolver su contradiccion requiere aprobacion separada, fuera de T3.
