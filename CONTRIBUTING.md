# Contributing to OpenCode Ecosystem

Gracias por tu interés en contribuir a OpenCode Ecosystem. Esto es un esfuerzo colaborativo que busca potenciar OpenCode con memoria persistente, SDD, skills y multi-modelo.

## Cómo Contribuir

1. **Fork** el repositorio
2. **Clona** tu fork:
   ```bash
   git clone https://github.com/tu-usuario/opencode-ecosystem.git
   cd opencode-ecosystem
   ```
3. **Crea una rama** para tu feature o fix:
   ```bash
   git checkout -b feature/nombre-de-la-feature
   ```
4. **Instala dependencias**:
   ```bash
   npm install
   ```
5. **Ejecuta tests** antes de hacer commit:
   ```bash
   npm test
   ```
6. **Haz commit** con mensajes claros:
   ```bash
   git commit -m "feat: descripcion clara del cambio"
   ```
7. **Push** a tu fork:
   ```bash
   git push origin feature/nombre-de-la-feature
   ```
8. **Abre un Pull Request** en la rama `main`

## Normas

- Sigue el formato de commit conventional commits
- Añade tests para nuevas funcionalidades
- Documenta cambios significativos
- Mantén el código simple y legible

## Estructura del Proyecto

```
opencode-ecosystem/
├── config/          # Configuración de OpenCode
├── skills/          # Skills exportables
├── packages/        # Paquetes npm (memory-adapter)
├── docs/            # Documentación
├── tests/           # Tests automatizados
├── .github/         # CI/CD, templates
└── spec/            # Especificaciones del proyecto
```

## Preguntas?

Abre un issue en la categoría `question` o contacta con el mantenedor.