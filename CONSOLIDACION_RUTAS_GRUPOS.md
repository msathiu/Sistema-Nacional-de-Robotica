# Consolidación de Rutas de Grupos - Documentación

## Fecha: 2026-02-22

## Problema Identificado

Existían **DOS sistemas paralelos** para la gestión de grupos/escuadrones:

### Sistema 1 - `users/views.py` (mis_grupos)
- **URL:** `/grupos/mis-grupos/`
- **Template:** `users/mis_grupos.html`
- **Funcionalidades:** Crear, editar, eliminar grupos en una sola vista con modales
- **Diseño:** Moderno glassmorphism

### Sistema 2 - `registry/views_institucional.py`
- **URLs:** 
  - `/registry/grupos/` (lista)
  - `/registry/grupos/crear/` (crear)
  - `/registry/grupos/<id>/` (ver)
  - `/registry/grupos/<id>/editar/` (editar)
  - `/registry/grupos/<id>/eliminar/` (eliminar)
- **Templates:** `grupos_lista.html`, `grupo_crear.html`, etc.
- **Funcionalidades:** Separadas por vista individual

## Solución Implementada

### Decisión: Consolidar en `mis_grupos`

Se eligió `mis_grupos` como la ruta única porque:
1. Es la interfaz principal que el usuario ya conoce
2. Tiene un diseño más moderno
3. Maneja crear, editar y eliminar en una sola vista con modales
4. Está en el menú principal del dashboard

## Cambios Realizados

### 1. Redirecciones en `registry/urls.py`

```python
from django.views.generic import RedirectView

# Gestión de Grupos - REDIRECCIONES a mis_grupos (consolidación)
path("grupos/", RedirectView.as_view(pattern_name='mis_grupos', permanent=False), name="grupos_institucion"),
path("grupos/crear/", RedirectView.as_view(pattern_name='mis_grupos', permanent=False), name="crear_grupo"),
```

### 2. Templates Actualizados

| Template | Cambio |
|----------|--------|
| `inscribir_grupo_evento_club.html` | `grupos_institucion` → `mis_grupos` |
| `inscribir_grupo.html` | `crear_grupo` → `mis_grupos` |
| `dashboard_institucional_new.html` | `grupos_institucion` → `mis_grupos` |
| `dashboard_institucional_new.html` | `crear_grupo` → `mis_grupos` |
| `grupo_editar.html` | `grupos_institucion` → `mis_grupos` (2 lugares) |
| `grupo_crear.html` | `grupos_institucion` → `mis_grupos` (2 lugares) |
| `grupo_detalle.html` | `grupos_institucion` → `mis_grupos` (2 lugares) |
| `grupos_lista.html` | `crear_grupo` → `mis_grupos` (2 lugares) |
| `evento_club_detalle.html` | Botón "Inscribir Grupo" → "Asociar Grupo Creado" |

### 3. Cambio de Mensajería

- **Antes:** "Crear Grupo"
- **Después:** "Asociar Grupo Creado" / "Ir a Mis Grupos"

## Flujo Actualizado

```
Usuario crea evento de club → Evento aprobado
         ↓
Usuario quiere inscribir grupo
         ↓
    ¿Tiene grupos editables?
         ↓
    SÍ → Seleccionar grupo → Asociar al evento
    NO → Redirigir a "Mis Grupos" → Crear grupo/escuadrón
```

## Rutas Finales

| Funcionalidad | Ruta | Vista |
|--------------|------|-------|
| Listar grupos | `/grupos/mis-grupos/` | `users.views.mis_grupos` |
| Crear grupo | `/grupos/mis-grupos/` (modal) | `users.views.mis_grupos` |
| Editar grupo | `/grupos/mis-grupos/` (modal) | `users.views.mis_grupos` |
| Eliminar grupo | `/grupos/mis-grupos/` (modal) | `users.views.mis_grupos` |
| Ver detalle grupo | `/registry/grupos/<id>/` | `views_institucional.ver_grupo` |
| Asociar a evento | `/registry/eventos-club/<id>/inscribir-grupo/` | `views_eventos.inscribir_grupo_evento_club` |

## Compatibilidad

Las rutas antiguas (`/registry/grupos/` y `/registry/grupos/crear/`) ahora redirigen automáticamente a `/grupos/mis-grupos/` para mantener compatibilidad con enlaces existentes.

## Beneficios

1. **Consistencia:** Un solo punto de entrada para gestión de grupos
2. **UX mejorada:** El usuario no se confunde con múltiples rutas
3. **Mantenimiento:** Menos código duplicado que mantener
4. **Navegación clara:** Flujo lógico desde eventos → asociar grupos

## Notas Técnicas

- Las vistas `ver_grupo`, `editar_grupo` y `eliminar_grupo` en `views_institucional.py` se mantienen para funcionalidades específicas
- Los templates de registry (`grupo_editar.html`, `grupo_detalle.html`) se actualizan para usar `mis_grupos` en breadcrumbs y botones de volver
- La redirección es temporal (permanent=False) para permitir cambios futuros si es necesario
