# Corrección: Status de Instituciones por Defecto

## 🎯 Problema Identificado

Las instituciones nuevas aparecían con status "aprobado" y campo `activa=True` por defecto, cuando deberían estar deshabilitadas hasta que un administrador las apruebe manualmente.

## ✅ Solución Implementada

### 1. **Modelo de Institución** (`registry/models.py`)

Los valores por defecto ya estaban correctos:
```python
activa = models.BooleanField(default=False)  # ✅ Desactivada por defecto
estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default="pendiente")  # ✅ Pendiente por defecto
```

### 2. **Formulario de Registro** (`users/forms.py`)

Se agregó validación explícita en el método `save()`:
```python
# IMPORTANTE: Asegurar que las instituciones nuevas estén desactivadas por defecto
if not instance.pk:  # Si es una nueva institución
    instance.activa = False
    instance.estatus = 'pendiente'
```

### 3. **Vista de Registro** (`users/views.py`)

Se mejoró la lógica para diferenciar entre registro por admin y registro público:

```python
# Si registra el admin, se aprueba de una vez
if es_administrador:
    institucion.activa = True
    institucion.estatus = 'aprobado'
else:
    # Usuario normal: pendiente de aprobación
    institucion.activa = False
    institucion.estatus = 'pendiente'
```

### 4. **Panel de Administración** (`registry/admin.py`)

Se mejoró la visualización y gestión:

**Cambios en `list_display`:**
```python
list_display = ('nombre', 'rif', 'codigo', 'estatus', 'activa', 'federado')
```
- Ahora muestra el campo `estatus` en la lista principal
- Permite ver de un vistazo qué instituciones están pendientes

**Cambios en `list_filter`:**
```python
list_filter = ('estatus', 'activa', 'federado', 'estado')
```
- Filtro por estatus agregado en primer lugar
- Facilita encontrar instituciones pendientes de aprobación

**Cambios en `fieldsets`:**
```python
('Estado de la Cuenta', {'fields': ('estatus', 'activa', 'eliminado')}),
```
- Campo `estatus` ahora visible en el formulario de edición
- Permite ver y modificar el estado de aprobación

**Acción de Aprobación Mejorada:**
```python
def aprobar_instituciones(self, request, queryset):
    count = 0
    for inst in queryset.filter(estatus='pendiente'):
        inst.activa = True
        inst.estatus = 'aprobado'
        inst.save()
        count += 1
    self.message_user(request, f"{count} instituciones han sido aprobadas y sus códigos RNR generados.")
```
- Solo aprueba instituciones con estatus 'pendiente'
- Muestra contador de instituciones aprobadas
- Genera códigos RNR automáticamente al aprobar

## 🔄 Flujo de Aprobación

### Registro Público (Usuario Normal)

1. Usuario completa formulario de registro
2. Sistema crea institución con:
   - `activa = False`
   - `estatus = 'pendiente'`
   - `codigo = 'TEMP-XXXXXXXX'`
3. Usuario de Django creado con `is_active = False`
4. Usuario ve página de "Registro Pendiente"
5. No puede iniciar sesión hasta aprobación

### Registro por Administrador

1. Admin completa formulario desde panel
2. Sistema crea institución con:
   - `activa = True`
   - `estatus = 'aprobado'`
   - `codigo = 'RNR[YY]-[EEEMMMPPP]-[8CHARS]'`
3. Usuario de Django creado con `is_active = True`
4. Puede iniciar sesión inmediatamente

### Aprobación Manual por Admin

1. Admin accede a "Gestión de Instituciones"
2. Filtra por `estatus = 'pendiente'`
3. Selecciona instituciones a aprobar
4. Ejecuta acción "✅ Aprobar y generar códigos RNR"
5. Sistema:
   - Cambia `activa = True`
   - Cambia `estatus = 'aprobado'`
   - Genera código RNR permanente
   - Activa usuario de Django (`is_active = True`)
   - Envía correo de activación (vía signals)

## 📊 Estados Posibles

| Estado | activa | estatus | Puede Login | Descripción |
|--------|--------|---------|-------------|-------------|
| Nuevo Registro | `False` | `pendiente` | ❌ No | Esperando aprobación admin |
| Aprobado | `True` | `aprobado` | ✅ Sí | Cuenta activa y funcional |
| Rechazado | `False` | `rechazado` | ❌ No | Solicitud denegada |
| Suspendido | `False` | `aprobado` | ❌ No | Cuenta temporalmente desactivada |

## 🔍 Verificación

Para verificar que los cambios funcionan correctamente:

### 1. Verificar Registro Nuevo
```python
# En Django shell
from registry.models import Institucion

# Buscar última institución registrada
inst = Institucion.objects.latest('fecha_registro')
print(f"Activa: {inst.activa}")  # Debe ser False
print(f"Estatus: {inst.estatus}")  # Debe ser 'pendiente'
print(f"Código: {inst.codigo}")  # Debe empezar con 'TEMP-'
```

### 2. Verificar Usuario Asociado
```python
# Verificar que el usuario no puede loguearse
user = inst.usuario
print(f"Usuario activo: {user.is_active}")  # Debe ser False
```

### 3. Verificar Aprobación
```python
# Aprobar institución
inst.activa = True
inst.estatus = 'aprobado'
inst.save()

# Verificar código RNR generado
print(f"Código: {inst.codigo}")  # Debe ser RNR[YY]-[EEEMMMPPP]-[8CHARS]

# Verificar usuario activado
inst.usuario.refresh_from_db()
print(f"Usuario activo: {inst.usuario.is_active}")  # Debe ser True
```

## 📝 Notas Importantes

1. **Códigos Temporales**: Las instituciones pendientes tienen códigos `TEMP-XXXXXXXX` que se reemplazan por códigos RNR al aprobar.

2. **Sincronización Usuario-Institución**: El campo `is_active` del usuario de Django se sincroniza automáticamente con el campo `activa` de la institución.

3. **Correos de Activación**: El envío de correos se maneja mediante signals (ver `registry/signals.py`).

4. **Seguridad**: Los usuarios con instituciones pendientes no pueden iniciar sesión hasta que un admin los apruebe.

## 🚀 Próximos Pasos

1. Probar el flujo completo de registro → aprobación → login
2. Verificar que los correos de activación se envían correctamente
3. Documentar el proceso para los administradores del sistema
4. Considerar agregar notificaciones para admins cuando hay instituciones pendientes

---

**Fecha de Implementación**: 2024
**Archivos Modificados**:
- `SistemaRegistro/registry/admin.py`
- `SistemaRegistro/users/forms.py`
- `SistemaRegistro/users/views.py`
