# ZAP via MCP en proyectos (opcional, bajo demanda)

Estado: documentado. El endpoint real (HTTP vs HTTPS) queda **pendiente de
verificar** hasta instalar ZAP y hacer un smoke-test; hasta entonces la plantilla
lleva `disabled: true`.

## Que es

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

## Pendiente (cuando haya ZAP instalado)

- [ ] Smoke-test del endpoint y del handshake MCP.
- [ ] Confirmar formato del header Authorization frente a la doc.
- [ ] Verificar aislamiento: un proyecto sin la config no lista `zap`.
- [ ] Documentar el resultado en `docs/evolution/`.
