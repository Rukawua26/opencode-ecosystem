---
name: security-review
description: Review application changes for concrete security vulnerabilities, exposed secrets, unsafe data flows, and missing security tests.
---

# Security Review

Checklist de seguridad para codigo que maneje auth, APIs, inputs de usuario, archivos, secretos, pagos o datos sensibles.

## Cuando Usar

- Implementando autenticacion o autorizacion
- Manejando input de usuario o file uploads
- Creando nuevos endpoints de API
- Trabajando con secretos o credenciales
- Implementando pagos
- Almacenando o transmitiendo datos sensibles
- Integrando APIs de terceros

## Trigger

Activa esta skill solo cuando el cambio toque:

- auth, permisos, tokens, sesiones, CORS, CSP, cookies, credenciales
- secretos, `.env`, datos sensibles, pagos, billing, encriptacion, hashing
- Una posible vulnerabilidad de seguridad explicita (inyeccion, XSS, CSRF, SSRF, IDOR, path traversal)

## Checklist

### 1. Secrets
- No hay API keys, tokens ni passwords hardcodeados
- Todo secreto en environment variables
- Verificacion de existencia al iniciar
- `.env.local` en `.gitignore`

### 2. Input Validation
- Todo input de usuario validado con esquema (Zod, etc.)
- File uploads: tamanio, tipo y extension limitados
- No usar input de usuario directo en queries
- Errores de validacion no filtran informacion sensible

### 3. SQL / NoSQL Injection
- Queries parametrizadas (no concatenacion de strings)
- ORM o query builder usado correctamente
- No usar raw queries sin sanitizar

### 4. XSS
- Input de usuario escapado antes de renderizar
- Content-Security-Policy configurada
- No usar `dangerouslySetInnerHTML` sin sanitizar

### 5. Auth / AuthZ
- Tokens en httpOnly cookies (no localStorage)
- Verificacion de autorizacion antes de operaciones sensibles
- Rate limiting en endpoints
- Roles y permisos verificados

### 6. Error Handling
- Errores no filtran datos sensibles
- Stack traces no expuestos en produccion
- Mensajes de error genericos para el cliente

### 7. Dependencies
- Dependencias actualizadas sin vulnerabilidades conocidas
- No usar librerias deprecadas o sin mantenimiento

### 8. MCP Security (Tool Poisoning + Least Privilege)
- Metadata de tools sin instrucciones ocultas (HTML comments, zero-width chars, base64)
- Permisos declarados coinciden con lo que el codigo realmente usa (no wildcards `*`)
- Sin Unicode deception (homoglyphs, RTL overrides en nombres de parametros)
- Descripcion del tool coincide con su comportamiento real

### 9. Taint Tracking (flujo de datos peligroso)
- Input de usuario no llega a exec/eval/subprocess sin sanitizar
- Variables intermedias no canalizan datos sensibles a sinks externos
- Credenciales no fluyen hacia outputs de red

### 10. Memory Poisoning
- Skills/modulos no inyectan contenido persistente entre sesiones
- Estado del agente no se manipula sin autorizacion
- Memoria persistente no se usa para persistir reglas de seguridad

## Formato de Salida

```
SECURITY REVIEW: PASS/FAIL

Secrets:     OK / X issues
Input:       OK / X issues
Injection:   OK / X issues
XSS:         OK / X issues
Auth:        OK / X issues
Errors:      OK / X issues
Deps:        OK / X issues
MCP:         OK / X issues
Taint:       OK / X issues
Memory:      OK / X issues

Issues to fix: (listar con severidad y ubicacion)
```

Si hay issues CRITICAL, DETENERSE y arreglarlos antes de continuar.
