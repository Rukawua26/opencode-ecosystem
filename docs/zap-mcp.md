# ZAP via MCP en proyectos (opcional, bajo demanda)

Estado: verificado en este proyecto (2026-10-12). ZAP 2.17 daemon con MCP
0.4.0 responde en `http://127.0.0.1:8282`; handshake MCP correcto y rechazo
sin clave. La plantilla del proyecto queda habilitada (`disabled` ausente) y
solo se activa cuando el daemon está arrancado.

## Que es

> Aclaración aditiva (2026-10-14): la verificación anterior es histórica y de
> un proyecto concreto, no una comprobación actual ni una activación global.
> La plantilla genérica de abajo conserva `disabled: true`; no representa la
> configuración local habilitada descrita arriba. El fallo de sustitución de
> entorno registrado más abajo corresponde al entorno del servicio observado,
> no demuestra que la sintaxis sea inválida en todos los entornos. El header
> directo es un antecedente, no una recomendación de guardar claves en Git;
> no copiar claves a terminales compartidos, historial, informes o ejemplos.
> La clave MCP y la API key de ZAP son distintas: `api.key` del ejemplo de
> arranque no acredita configurar la security key MCP. Antes de usar, verificar
> por separado autenticación MCP y alcance local autorizado. Esta revisión no
> ha arrancado ZAP ni repetido su handshake ni modificado configuración.

El complemento oficial **MCP Integration** de ZAP expone un servidor MCP en
`http://localhost:8282` con herramientas (spider, ajax spider, active scan,
generar informe), recursos (`zap://alerts`, `zap://history/{id}`) y prompts
(`zap_baseline_scan`, `zap_full_scan`). OpenCode puede conectarse como cliente
MCP **solo desde los proyectos que lo configuren**.

- Doc oficial: https://www.zaproxy.org/docs/desktop/addons/mcp-integration/
- Herramientas: https://www.zaproxy.org/docs/desktop/addons/mcp-integration/mcp-tools/

## Por que por proyecto y no global

- RAM i5/8GB: ZAP queda apagado salvo que lo necesites; si no hay servidor en
  `localhost:8282`, una conexion global fallaria en todos los proyectos.
- Contexto: cada MCP anade herramientas al catalogo; solo donde haga falta.
- Seguridad: el acceso al MCP de ZAP da control total sobre ZAP; jamas se
  expone fuera de `localhost` ni en repos de terceros.
- En OpenCode, `opencode mcp add` sin `--global` escribe la config del
  proyecto actual; `--global` la pondria en toda tu instalacion. **No usar
  `--global` para ZAP.**

## Pasos para un proyecto concreto

1. Instala ZAP (tarball oficial o imagen; decide el humano) y su complemento
   MCP Integration desde el Marketplace de add-ons de ZAP.
2. Arranca ZAP (daemon o escritorio) con el MCP habilitado, puerto 8282 y una
   **security key** generada.
3. Exporta la clave en la sesion donde lances OpenCode: `export ZAP_MCP_KEY=...`.
   Nunca en un fichero versionado ni en la config JSON.
4. En el proyecto, crea/edita `opencode.jsonc` (o
   `.opencode/opencode.jsonc`) con la plantilla de abajo.
5. Dentro de OpenCode: `/mcps` -> selecciona `zap` -> conectar.
   Antes de usar, verifica con `zap_version`.
6. Al terminar: desconecta en `/mcps` (o deja `disabled: true` de nuevo) y
   para ZAP.

## Plantilla por proyecto

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "zap": {
        "type": "remote",
        "url": "http://localhost:8282",
        "oauth": false,
        "disabled": true,
        "headers": {
          "Authorization": "{env:ZAP_MCP_KEY}"
        }
      }
    }
  }
}
```

Notas:
- `Authorization` lleva **el valor exacto de la security key**, sin prefijo
  `Bearer` automatico. Si ZAP la tiene deshabilitada, omite `headers`.
- La doc de ZAP advierte que la opcion **Secure Only** (activada por defecto)
  rechaza HTTP con 403. Si al conectar falla, el smoke-test consiste en probar
  `http` y luego revisar la opcion en Options -> MCP Integration; no desactives
  seguridad sin entender el motivo.
- ZAP dentro de Docker requiere publicar el puerto a `localhost`; el daemon de
  esta maquina viene parado por defecto.

## Reglas de uso

- Conectar MCP **no escanea nada** por si solo.
- Target explicito siempre: spider/baseline solo contra URLs de tu propiedad.
- Escaneo activo y full scan: autorizacion adicional por escrito, alcance
  acotado (dominio, exclusiones como logout/pagos/escritura) y preferiblemente
  staging con datos de prueba.
- Auditorias desde un proyecto cualquiera: la config vive en el proyecto desde
  el que **auditas**, no en el objetivo.
- La clave nunca va a Git ni a informes; en logs y pantallas, redactada.
- Esta integracion complementa a `web-quality-lite`: aquella lista criterios,
  ZAP aporta evidencia de seguridad para el punto "seguridad basica".

## Verificación (2026-10-12)

- [x] Smoke-test del endpoint y del handshake MCP: `initialize` devuelve
  `serverInfo: ZAP MCP Server 0.4.0`.
- [x] Header `Authorization` con la clave exacta, sin prefijo `Bearer`; sin clave
  responde `Invalid or missing security key`.
- [x] Arranque daemon verificado en los puertos 8080 y 8282, MCP listener en
  `127.0.0.1:8282`; `opencode mcp list` muestra `zap connected` y
  `zap_version` responde `2.17.0`.
- [x] Aislamiento: `opencode mcp list` solo muestra `zap` en este proyecto.
- [x] El reemplazo `{env:ZAP_MCP_KEY}` en `opencode.json` **no funciona** para
  este servidor remoto: OpenCode no tenía la variable en el entorno del
  servicio y la conexión fallaba con 401. Solución aplicada: registrar el header
  directo con `opencode mcp add zap --url http://127.0.0.1:8282 --header
  "Authorization=<clave>"`. La clave viaja solo en la configuración local del
  proyecto, nunca en Git ni en informes.
- [ ] Documentar el resultado en `docs/evolution/` del ecosistema (sigue pendiente
  de versionar el ecosistema, fuera del repo de la app).

## Arranque y parada del daemon

```bash
# arrancar (mismo directorio home ~/.ZAP, puertos 8080/8282)
/home/miguel/tools/zap/zap.sh -daemon -port 8080 \
  -config mcp.securityKeyEnabled=true -config mcp.enabled=true \
  -config mcp.port=8282 -config mcp.secureOnly=false \
  -config api.key=<api-key>

# verificar
opencode mcp list

# parar
pkill -f 'zap-2.17.0.jar'
```

Si el daemon ya está en otro puerto o con otra clave, `opencode mcp add` vuelve a
registrar el server del proyecto con la URL y el header correctos.
