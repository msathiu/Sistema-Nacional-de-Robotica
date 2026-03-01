# 🔒 Corrección de Menús por Roles de Usuario

## 📋 Problema Identificado

Los usuarios con rol **Federación Regional** veían opciones de menú administrativas que solo deberían estar disponibles para **Federación Central** y **Superusuarios**. Aunque los decoradores protegían las vistas (mostrando "sin permiso" al hacer clic), las opciones aparecían visibles en el menú lateral.

### Causa Raíz
- Las variables `es_central` y `es_regional` no estaban disponibles globalmente en el contexto de los templates
- El template `base_dashboard.html` usaba estas variables, pero al no existir, Django las evaluaba como `False`
- Esto causaba que el menú mostrara opciones incorrectas según el rol

---

## ✅ Solución Implementada

### 1️⃣ Context Processor de Roles (`registry/context_processors.py`)

Se agregó un nuevo context processor que inyecta automáticamente las variables de rol en **todos los templates**:

```python
def user_roles(request):
    """Agrega variables de roles de usuario al contexto global."""
    if request.user.is_authenticated:
        try:
            perfil = request.user.userprofile
            return {
                'perfil': perfil,
                'es_central': perfil.user_type == 'fed_central',
                'es_regional': perfil.user_type == 'fed_regional',
                'es_institucional': perfil.user_type == 'institucional',
                'es_participante': perfil.user_type == 'participante',
            }
        except:
            pass
    return {
        'perfil': None,
        'es_central': False,
        'es_regional': False,
        'es_institucional': False,
        'es_participante': False,
    }
```

**Beneficios:**
- ✅ Variables disponibles en todos los templates sin necesidad de pasarlas manualmente
- ✅ Código más limpio y mantenible
- ✅ Consistencia en toda la aplicación

### 2️⃣ Registro en Settings (`SistemaRegistro/settings.py`)

Se registró el context processor en la configuración de templates:

```python
"context_processors": [
    # ... otros context processors
    "registry.context_processors.notificaciones_no_leidas",
    "registry.context_processors.user_roles",  # ← NUEVO
],
```

### 3️⃣ Separación de Menús por Rol (`templates/users/base_dashboard.html`)

Se reestructuró la lógica del menú lateral para tener **tres menús distintos**:

#### 🔵 Menú Federación Central + Superusuarios
```django
{% if es_central or user.is_superuser %}
    <!-- Acceso completo a todas las funciones administrativas -->
    - Revisar Clubes
    - Solicitudes Eliminación
    - Papelera
    - Gestionar Sedes
    - Métricas Clubes
    - etc.
{% endif %}
```

#### 🟢 Menú Federación Regional (NUEVO)
```django
{% elif es_regional %}
    <!-- Solo visualización de datos de su estado -->
    - Inicio
    - Mi Perfil Profesional
    - Instituciones (filtradas por estado)
    - Participantes (filtrados por estado)
    - Métricas Clubes (solo su estado)
{% endif %}
```

#### 🟡 Menú Usuarios Institucionales
```django
{% else %}
    <!-- Gestión de su propia institución -->
    - Mis Clubes
    - Mis Grupos
    - Eventos
    - Notificaciones
    - etc.
{% endif %}
```

---

## 🎯 Permisos por Rol

| Funcionalidad | Fed. Central | Fed. Regional | Institucional |
|--------------|--------------|---------------|---------------|
| Revisar Clubes | ✅ Aprobar/Rechazar | ❌ | ❌ |
| Solicitudes Eliminación | ✅ | ❌ | ❌ |
| Papelera | ✅ | ❌ | ❌ |
| Gestionar Sedes | ✅ | ❌ | ❌ |
| Métricas Clubes | ✅ Todos los estados | ✅ Solo su estado | ❌ |
| Ver Instituciones | ✅ Todas | ✅ Solo su estado | ❌ |
| Ver Participantes | ✅ Todos | ✅ Solo su estado | ✅ De su sede |
| Gestionar Clubes | ❌ | ❌ | ✅ De su sede |

---

## 🧪 Cómo Probar

### 1. Reiniciar el servidor
```bash
cd SistemaRegistro
python manage.py runserver
```

### 2. Probar con diferentes roles

#### Usuario Regional:
```bash
# Iniciar sesión con un usuario fed_regional
# Verificar que SOLO vea:
- Inicio
- Mi Perfil Profesional
- Instituciones
- Participantes
- Métricas Clubes
```

#### Usuario Central:
```bash
# Iniciar sesión con un usuario fed_central
# Verificar que vea TODAS las opciones administrativas
```

#### Usuario Institucional:
```bash
# Iniciar sesión con un usuario institucional
# Verificar que vea opciones de gestión de su sede
```

---

## 📝 Archivos Modificados

1. **`registry/context_processors.py`**
   - ✅ Agregado context processor `user_roles()`

2. **`SistemaRegistro/settings.py`**
   - ✅ Registrado nuevo context processor

3. **`templates/users/base_dashboard.html`**
   - ✅ Separada lógica de menús por rol
   - ✅ Menú específico para federación regional

---

## 🔐 Seguridad

Esta corrección es **solo visual**. La seguridad real está garantizada por:

1. **Decoradores en las vistas** (`@role_required`, `@login_required`)
2. **Validaciones en los métodos** (verificación de permisos)
3. **Filtros de QuerySet** (usuarios regionales solo ven datos de su estado)

**Importante:** Aunque un usuario intente acceder directamente a una URL sin permiso, los decoradores lo bloquearán.

---

## 🚀 Próximos Pasos

- ✅ Verificar que todos los dashboards usen `base_dashboard.html`
- ✅ Probar con usuarios reales de cada rol
- ✅ Documentar permisos específicos de cada vista
- ⏳ Considerar agregar tooltips explicativos en el menú

---

## 📚 Referencias

- [Django Context Processors](https://docs.djangoproject.com/en/5.0/ref/templates/api/#built-in-template-context-processors)
- [Template Inheritance](https://docs.djangoproject.com/en/5.0/ref/templates/language/#template-inheritance)
- Documento: `MEJORES_PRACTICAS.md`
- Documento: `CONFIGURAR_ROLES.md`
