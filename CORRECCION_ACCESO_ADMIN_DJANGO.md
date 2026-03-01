# Corrección de Acceso al Admin de Django

## Problema Identificado

El usuario institucional (y otros roles como `tecnologico` y `fed_central`) podían acceder al panel de administración de Django (`/admin/`), lo cual representa un problema de seguridad.

## Solución Implementada

Se ha modificado la arquitectura de permisos para que **SOLO el superusuario** pueda acceder al panel de administración de Django.

### Archivos Modificados

#### 1. `SistemaRegistro/users/middleware.py`

**Cambios en `RoleBasedAccessMiddleware`:**

- `ADMIN_ALLOWED_ROLES`: Cambiado de `['superuser', 'tecnologico', 'fed_central']` a `['superuser']`
- Actualizado `ROLE_ROUTE_PERMISSIONS`:
  - `fed_central`: Removido `/admin/` de `allowed_prefixes` y agregado a `denied_prefixes`
  - `tecnologico`: Removido `/admin/` de `allowed_prefixes` y agregado a `denied_prefixes`
  - `superuser`: Solo puede acceder a `/admin/`, todas las demás rutas están denegadas
- Actualizado `_get_user_dashboard()`:
  - `tecnologico` y `fed_central` ahora redirigen al dashboard general, no al admin

**`SuperuserAdminOnlyMiddleware`** (sin cambios, ya funcionaba correctamente):
- Restringe al superusuario para que solo pueda acceder a `/admin/`
- Redirige cualquier otra ruta al admin

#### 2. `SistemaRegistro/users/decorators.py`

**Cambios en `admin_access_required`:**

```python
# ANTES
ADMIN_ALLOWED_ROLES = ['superuser', 'tecnologico', 'fed_central']

# DESPUÉS
# Solo permitir si es superuser de Django
if request.user.is_superuser and request.user.is_staff:
    return view_func(request, *args, **kwargs)
```

## Matriz de Permisos Final

| Rol | Acceso al Admin Django | Rutas Permitidas |
|-----|------------------------|------------------|
| **superuser** | ✅ SÍ | Solo `/admin/` |
| **tecnologico** | ❌ NO | `/federacion/`, `/instituciones/`, `/sedes/`, `/participantes/`, `/eventos/`, `/perfil/` |
| **fed_central** | ❌ NO | `/federacion/`, `/instituciones/`, `/sedes/`, `/participantes/`, `/eventos/`, `/perfil/` |
| **fed_regional** | ❌ NO | `/federacion/`, `/instituciones/`, `/participantes/`, `/eventos/`, `/perfil/` |
| **institucional** | ❌ NO | `/institucion/`, `/participantes/`, `/eventos/`, `/grupos/`, `/mis-grupos/`, `/perfil/` |
| **participante** | ❌ NO | `/participante/`, `/eventos/`, `/grupos/`, `/mis-grupos/`, `/perfil/` |

## Flujo de Protección

### Para usuarios NO superuser intentando acceder a `/admin/`:

1. `RoleBasedAccessMiddleware` detecta que la ruta es `/admin/`
2. Verifica si el usuario está en `ADMIN_ALLOWED_ROLES` (solo `superuser`)
3. Si no está permitido, muestra mensaje de error y redirige al dashboard correspondiente

### Para superusuario intentando acceder a rutas normales:

1. `SuperuserAdminOnlyMiddleware` detecta que el usuario es superuser
2. Verifica si la ruta está dentro de las permitidas (solo `/admin/`)
3. Si no está permitido, muestra mensaje de advertencia y redirige a `/admin/`

## Vistas Protegidas

Las siguientes vistas utilizan el decorador `@admin_access_required`:

- `admin_dashboard` (`/admin/dashboard/`)
- `ver_logs_sistema` (`/admin/logs/`)

Ambas vistas ahora solo son accesibles por superusuarios.

## Pruebas Recomendadas

1. **Institucional**: Intentar acceder a `/admin/` → Debe ser redirigido al dashboard institucional
2. **Tecnologico**: Intentar acceder a `/admin/` → Debe ser redirigido al dashboard general
3. **Fed_Central**: Intentar acceder a `/admin/` → Debe ser redirigido al dashboard general
4. **Participante**: Intentar acceder a `/admin/` → Debe ser redirigido al dashboard participante
5. **Superuser**: Intentar acceder a `/dashboard/` → Debe ser redirigido a `/admin/`
6. **Superuser**: Acceder a `/admin/` → Debe poder acceder correctamente

## Fecha de Implementación

2026-02-24
