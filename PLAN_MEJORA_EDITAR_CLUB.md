# Plan de Mejora: Template "Editar Club"

## Información Recopilada

### 1. Archivo Actual: `club_editar.html`
- Diseño básico con estructura simple
- Card sin sombra ni efectos modernos
- Sin header elegante
- Formularios con estilos Bootstrap básicos
- Sidebar de información simple
- Botones tradicionales

### 2. Archivo Referencia: `club_enviar_revision.html`
- **Page-header**: Gradiente azul con acentos cyan y efectos decorativos
- **Card principal**: border-radius 20px, box-shadow elegante
- **Animaciones**: fadeInUp con delays
- **Info-cards**: Con hover effects y gradient headers
- **Badges modernos**: border-radius 20px con gradientes
- **Botones**: Estilo "btn-action" con gradientes y transiciones
- **Sistema de colores**: Variables CSS (--blue-main, --accent-cyan, --success, etc.)
- **Checklist y Summary items**: Con iconos y efectos hover
- **Tip cards**: Con estilos visuales atractivos

---

## Plan de Implementación

### Objetivo
Mejorar el diseño de `club_editar.html` para que sea consistente con `club_enviar_revision.html` y el dashboard, sin romper la funcionalidad actual.

### Pasos de Implementación:

1. **Agregar bloque `extra_css`** con:
   - Variables CSS (--blue-main, --blue-dark, --accent-cyan, --success, --warning)
   - Estilos para page-header con gradiente y efectos decorativos
   - Estilos para main-card (sombra, border-radius 20px)
   - Estilos para info-card con hover
   - Estilos para badges modernos
   - Estilos para btn-action (botones modernos)
   - Animaciones fadeInUp con delays
   - Mejoras en formulario (inputs con mejor styling)
   - Estilos para sidebar cards

2. **Actualizar estructura HTML**:
   - Agregar page-header moderno
   - Envolver card principal con clase main-card
   - Mejorar headers de secciones con iconos
   - Actualizar sidebar con estilos modernos
   - Actualizar botones a estilo moderno

3. **Preservar funcionalidad**:
   - Mantener todos los campos del formulario
   - Mantener lógica de estados
   - Mantener acciones disponibles según estado

---

## Archivos a Editar

| Archivo | Acción |
|---------|--------|
| `SistemaRegistro/registry/templates/registry/club_editar.html` | Editar completamente el diseño |

---

## Resultados Esperados

- ✅ Diseño consistente con "Enviar Club a Revisión"
- ✅ Diseño consistente con el dashboard
- ✅ UX mejorado con animaciones y efectos
- ✅ Funcionalidad intacta
- ✅ Sistema visual moderno y profesional

