# Guia Paso a Paso: SDD (Spec-Driven Development)

Este documento muestra como desarrollar una feature completa usando el flujo SDD del ecosistema OpenCode.

## Caso de Uso: Implementar un Formulario de Login

Imaginemos que necesitamos agregar un formulario de login a un proyecto React existente. Veremos cada fase del flujo SDD.

---

## Fase 1: Especificacion (`/spec`)

**Cuando usar:** Estas planeando una nueva feature que tiene multiples archivos, decisiones de arquitectura o impacto en el sistema.

**Prompt en lenguaje natural:**
```
Necesito agregar un formulario de login a la aplicacion React. 
El usuario debe poder ingresar email y password. 
Si las credenciales son validas, redirigir al dashboard. 
Si son invalidas, mostrar mensaje de error. 
Usar la API existente en /api/auth/login.
```

**Que hace OpenCode:**
1. Carga la skill `sdd-specify`
2. Analiza el codebase para entender:
   - Que librerias usas (React Router, Axios, etc.)
   - Como esta estructurado actualmente el codigo
   - Que convenciones siguen los formularios existentes
3. Guarda contexto previo si hay memoria del proyecto
4. Genera `spec/features/001-login-form/spec.md`

**Caracteristicas de la spec generada:**
- Criterios de aceptacion claros y verificables
- Alcance bien definido (que SI y que NO)
- Analisis de impacto (archivos a tocar)
- Sin ambiguedades para que un agente pueda implementarla

---

## Fase 2: Plan (`/plan-spec`)

**Cuando usar:** La spec esta aprobada y queremos definir el approach tecnico.

**Prompt:**
```
/plan-spec spec/features/001-login-form
```

**Que hace OpenCode:**
1. Carga la skill `sdd-plan`
2. Lee el spec generado
3. Diseña la arquitectura tecnica:
   - Crear componente `LoginForm.jsx` en `src/components/auth/`
   - Usar `useState` para email/password
   - Validacion client-side basica
   - Llamada a `/api/auth/login` con Axios
   - Manejo de errores con `try/catch`
   - Redireccion con `useNavigate` de React Router
4. Genera `spec/features/001-login-form/plan.md`

**Salida tipica del plan:**
```markdown
## Arquitectura
- Componente padre: LoginForm
- Estado local: email, password, loading, error
- Metodos: handleSubmit, validate
- Integraciones: API, Router

## Archivos a Crear
- src/components/auth/LoginForm.jsx
- src/components/auth/LoginForm.css (opcional)
- src/components/auth/__tests__/LoginForm.test.jsx

## Archivos a Modificar
- src/pages/Login.jsx (usar el nuevo componente)

## Dependencias
- react-router-dom (ya instalado)
- axios (ya instalado)
```

---

## Fase 3: Tareas (`/tasks-spec`)

**Cuando usar:** Tenemos el plan y queremos descomponer en tareas atomicas.

**Prompt:**
```
/tasks-spec spec/features/001-login-form
```

**Que hace OpenCode:**
1. Genera tareas pequenas y verificables en `spec/features/001-login-form/tasks.md`:

```markdown
## Tareas
1. [ ] Crear `src/components/auth/LoginForm.jsx` con estado inicial
2. [ ] Agregar inputs controlados para email y password
3. [ ] Implementar validacion basica
4. [ ] Agregar funcion `handleSubmit` con llamada a /api/auth/login
5. [ ] Manejar estado de loading y errores
6. [ ] Integrar redireccion a /dashboard en exito
7. [ ] Agregar estilos basicos (CSS o clases existentes)
8. [ ] Escribir tests basicos con Vitest
9. [ ] Verificar accesibilidad basica (labels, roles)
```

**Cada tarea es atomica**: un archivo, un cambio puntual, un test.

---

## Fase 4: Implementacion (`/implement-spec`)

**Cuando usar:** Queremos ejecutar las tareas.

**Prompt:**
```
/implement-spec spec/features/001-login-form
```

**Que hace OpenCode:**
1. Para cada tarea en `tasks.md`:
   - Lee el contexto necesario (plan.md, archivos del codebase)
   - Implementa el cambio
   - Verifica que no rompio tests existentes
   - Marca la tarea como completada
2. Reporta problemas si los hubo
3. Abre checkpoints automaticos por si necesitas revertir

**Resultado:** Todos los archivos implementados, tests pasando, tareas marcadas como hechas en `tasks.md`.

---

## Fase 5: Verificacion (`/verify-spec`)

**Cuando usar:** La implementacion esta terminada y queremos verificar que cumple la spec.

**Prompt:**
```
/verify-spec spec/features/001-login-form
```

**Que hace OpenCode:**
1. Lee la spec original
2. Compara implementacion contra criterios de aceptacion
3. Corre tests
4. Verifica accesibilidad, performance, seguridad
5. Genera un reporte de verificacion en `verify.md`

**Salida tipica:**
```markdown
## Criterios Cumplidos
- [x] Usuario puede ingresar email y password
- [x] Validacion de formato email basica
- [x] Redireccion a /dashboard en exito
- [x] Mensaje de error en fallo

## Issues Encontrados
- [ ] Falta reset del estado al desmontar (posible memory leak)
- [ ] Sin proteccion CSRF

## Recomendaciones
- Considerar agregar timeout a la peticion
- Considerar rate-limiting en login
```

---

## Multi-Modelo Automatico

Detras de escena, cada fase usa el modelo optimo segun `sdd_multi_model` en tu `opencode.jsonc`:

| Fase | Modelo | Razon |
|---|---|---|
| `spec` | Gemini Flash | Alto razonamiento |
| `plan` | Gemini Flash | Diseno tecnico |
| `tasks` | GPT-5.4-mini | Descomposicion |
| `implement` | GPT-5.4 | Codigo robusto |
| `verify` | GPT-5.4 | Deteccion de bugs |

Si tu modelo primario falla, usa el fallback configurado automaticamente.

---

## Tips y Buenas Practicas

1. **Una feature a la vez**: No mezcles features en una sola spec
2. **Spec es contrato**: Si cambia el alcance, actualiza spec.md antes
3. **Verifica antes de mergear**: No skip `/verify-spec`
4. **Usa memoria**: Las decisiones de hoy son contexto para manana
5. **Commits pequenos**: despues de cada tarea o bloque logico

---

## Comandos Resumidos

```bash
/spec                            # Crear nueva spec (prompt en lenguaje natural)
/plan-spec spec/features/001-X   # Planear implementacion
/tasks-spec spec/features/001-X  # Generar tareas
/implement-spec spec/features/001-X  # Implementar tareas
/verify-spec spec/features/001-X     # Verificar contra criterios
/opencode-doctor                 # Diagnostico del ecosistema
```
