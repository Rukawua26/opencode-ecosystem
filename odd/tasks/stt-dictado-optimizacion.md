# stt-dictado-optimizacion

## Objetivo

Reducir la latencia del dictado por voz en Arch + Hyprland + Fish, sin
sacrificar precision en espanol e ingles tecnico, y corregir los errores
encontrados en el arranque actual.

## Problema y porque

- El servicio `hyprwhspr.service` esta habilitado pero inactivo porque
  `graphical-session.target` no se activa en esta sesion.
- El lanzador actual `hyprwhspr-toggle` no tiene manejo de errores ni
  arranque del servicio, y no informa fallos al usuario.
- El modelo `small` ya esta instalado y el backend `pywhispercpp` es
  funcional, pero no hay evidencia reciente de latencia real.

## Alcance

- Incluye: arranque automatico desde Hyprland, lanzador robusto, ajustes
  de latencia en `config.json`, verificacion con `test.wav`.
- Incluye correccion de dependencias faltantes del venv ya gestionado por
  hyprwhspr cuando la prueba las demuestra.
- No incluye: cambio de motor STT, dependencias nuevas del repositorio,
  cambio de atajos existentes, integraciones con Waybar/Noctalia, ni
  migraciones de esquema.

## Restricciones

- Python stdlib solamente en el repo; no anadir dependencias.
- No tocar memoria viva, receipts, backups ni logs.
- No commitear ni pushear.
- Mantener compatibilidad Wayland y Fish.

## No romper

- `~/.config/hypr/hyprland.conf` debe seguir cargando correctamente.
- `nerd-dictation` debe seguir disponible como alternativa.
- El modelo `small` y el backend `pywhispercpp` deben seguir usables.
- Los atajos existentes `SUPER+SHIFT+D`, `SUPER+SHIFT+N` y
  `SUPER+SHIFT+B` deben seguir funcionando.

## TDD

- Modo: off
- Fuente: default
- Runner: no disponible
- Checks funcionales obligatorios: `hyprwhspr validate`,
  `hyprwhspr test`, `systemctl --user is-active hyprwhspr.service`.

## Tareas

- [x] T1: Anadir arranque automatico de `hyprwhspr.service` en
  `hyprland.conf` para que el servicio este activo en cada sesion.
- [x] T2: Reemplazar `hyprwhspr-toggle` por un lanzador robusto con
  arranque del servicio, espera de hasta 8 s y notificacion de error.
- [x] T3: Ajustar `config.json` para latencia: `keepalive_stream: true`
  y `beam_size: 3`, manteniendo `small` y `es`.
  - Ajuste tras pruebas: `keepalive_stream` vuelve a `false` porque el
    stream keepalive falla en esta maquina con error ALSA -9999.
- [x] T4: Verificar con `hyprwhspr validate`, `hyprwhspr test` y
  `systemctl --user is-active hyprwhspr.service`.
- [x] T5: Reparar `soundfile` en el venv gestionado de hyprwhspr; la
  dependencia faltaba y rompia la transcripcion de archivos.

## Criterios de aceptacion

- `systemctl --user is-active hyprwhspr.service` devuelve `active`.
- `hyprwhspr validate` termina sin errores.
- `hyprwhspr test` termina sin errores.
- El lanzador `hyprwhspr-toggle` alterna el dictado y avisa si hay error.
- La configuracion queda reversible y sin dependencias nuevas.

## Decisiones aceptadas

- Mantener `pywhispercpp` y el modelo `small`.
- Mantener `nerd-dictation` como alternativa.
- No activar servidores WebSocket/gRPC ni otros protocolos todavia.

## Reutilizacion investigada

- Se reutiliza el backend `pywhispercpp` y el modelo `small` ya instalados.
- Se reutiliza `notify-send` para avisos de error.
- Se reutiliza el servicio systemd ya habilitado.

## Evidencia

- `bash -n /home/miguel/.local/bin/hyprwhspr-toggle` -> `sintaxis ok`.
- `systemctl --user is-active hyprwhspr.service` -> `active`.
- `test -S $XDG_RUNTIME_DIR/hyprwhspr/hyprwhspr.sock` -> `socket ok`.
- `hyprwhspr validate` -> `Validation passed`; la advertencia de
  `graphical-session.target` se conserva, pero el servicio arranca desde
  Hyprland.
- `hyprwhspr test` -> `All tests passed!`.
- `hyprwhspr transcribe ... --lang es --clean` -> `exit=0 elapsed=18s`;
  salida `[Música]`.
- `soundfile` quedo instalado en el venv gestionado:
  `soundfile-0.14.0`; antes faltaba y rompia `transcribe`.

## Progreso

- Estado: completado
- Ultima tarea: T5
- Siguiente paso: probar una frase hablada real con `SUPER+SHIFT+D` y
  comparar la latencia percibida.
- Bloqueos: ninguno
