# 🔄 Flujo Actualizado: Registro y Aprobación de Instituciones

## 📋 Resumen del Flujo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGISTRO DE INSTITUCIÓN                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Usuario completa formulario en /registrar-institucion/     │
│     ├─ Datos de la institución                                 │
│     ├─ Email de contacto                                       │
│     └─ Contraseña                                              │
│                                                                 │
│  2. Sistema crea institución:                                  │
│     ├─ codigo = "TEMP-XXXXXXXX" (temporal)                     │
│     ├─ activa = False                                          │
│     ├─ estatus = "pendiente"                                   │
│     └─ Crea usuario con:                                       │
│         ├─ username = "TEMP-XXXXXXXX"                          │
│         └─ is_active = False (NO puede login)                  │
│                                                                 │
│  3. Usuario ve: "Registro Pendiente de Aprobación"            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              APROBACIÓN POR ADMINISTRADOR                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Admin accede a /instituciones/                             │
│     └─ Ve instituciones con badge "PENDIENTE"                  │
│                                                                 │
│  2. Admin activa el switch de la institución                   │
│     └─ Modal de confirmación aparece                           │
│                                                                 │
│  3. Admin confirma la aprobación                               │
│                                                                 │
│  4. Sistema ejecuta aprobar_institucion():                     │
│     ├─ Detecta código TEMP-XXXXXXXX                            │
│     ├─ Cambia activa = True                                    │
│     ├─ Cambia estatus = "aprobado"                             │
│     ├─ save() genera código RNR26-EEEMMMPPP-XXXXXXXX           │
│     ├─ Actualiza usuario:                                      │
│     │   ├─ username = código RNR                               │
│     │   └─ is_active = True (AHORA puede login)                │
│     └─ Envía correo con credenciales                           │
│                                                                 │
│  5. Usuario recibe correo con:                                 │
│     ├─ Código RNR (su username)                                │
│     ├─ Contraseña (la que usó al registrarse)                  │
│     └─ URL de login                                            │
│                                                                 │
│  6. Usuario puede iniciar sesión                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Estados de la Institución

### Estado 1: Pendiente (Recién Registrada)

```python
{
    "codigo": "TEMP-A1B2C3D4",
    "activa": False,
    "estatus": "pendiente",
    "usuario": {
        "username": "TEMP-A1B2C3D4",
        "is_active": False  # ❌ NO puede hacer login
    }
}
```

**Badge en panel**: 🟡 PENDIENTE
**Switch**: Desactivado (puede activarse)
**Usuario puede login**: ❌ NO

### Estado 2: Aprobada (Después de activación)

```python
{
    "codigo": "RNR26-011131421-B69TFUW7",
    "activa": True,
    "estatus": "aprobado",
    "usuario": {
        "username": "RNR26-011131421-B69TFUW7",
        "is_active": True  # ✅ SÍ puede hacer login
    }
}
```

**Badge en panel**: 🟢 APROBADA
**Switch**: Activado (puede desactivarse)
**Usuario puede login**: ✅ SÍ
**Correo enviado**: ✅ SÍ (solo en primera aprobación)

### Estado 3: Suspendida (Desactivada por admin)

```python
{
    "codigo": "RNR26-011131421-B69TFUW7",
    "activa": False,
    "estatus": "aprobado",  # Mantiene estatus aprobado
    "usuario": {
        "username": "RNR26-011131421-B69TFUW7",
        "is_active": False  # ❌ NO puede hacer login
    }
}
```

**Badge en panel**: 🟡 PENDIENTE
**Switch**: Desactivado
**Usuario puede login**: ❌ NO
**Correo enviado**: ❌ NO (al reactivar tampoco se envía)

---

## 💻 Código Clave

### Vista de Aprobación (`users/views.py`)

```python
@admin_required
@require_http_methods(["POST"])
def aprobar_institucion(request, institucion_id):
    with transaction.atomic():
        institucion = get_object_or_404(Institucion, id=institucion_id)

        # Verificar si tiene código temporal (primera aprobación)
        tiene_codigo_temporal = institucion.codigo.startswith('TEMP-')

        # 1. Activar institución (genera código RNR en save())
        institucion.activa = True
        institucion.estatus = 'aprobado'
        institucion.save()

        # 2. Activar usuario y actualizar username
        perfil = UserProfile.objects.filter(institution=institucion).first()
        if perfil and perfil.user:
            perfil.user.is_active = True
            perfil.user.username = institucion.codigo  # Código RNR
            perfil.user.save()

            # 3. Enviar correo SOLO en primera aprobación
            if tiene_codigo_temporal:
                institucion.enviar_correo_activacion()

            messages.success(request, f'Cuenta activada correctamente.')

    return redirect('lista_instituciones')
```

### Método save() del Modelo (`registry/models.py`)

```python
def save(self, *args, **kwargs):
    # Si se activa y tiene código temporal, generar código RNR
    if self.activa and (not self.codigo or self.codigo.startswith("TEMP-")):
        self.codigo = self.generar_codigo_rnr()
        self.estatus = "aprobado"

    # Vincular usuario si existe
    if not self.usuario_id and self.pk:
        UserProfile = apps.get_model("users", "UserProfile")
        perfil = UserProfile.objects.filter(institution=self).first()
        if perfil and perfil.user:
            self.usuario = perfil.user

    super().save(*args, **kwargs)

    # Sincronizar username con código RNR
    if self.activa and self.usuario and self.usuario.username != self.codigo:
        self.usuario.username = self.codigo
        self.usuario.save(update_fields=["username"])
```

---

## 📧 Correo de Activación

### Cuándo se envía

✅ **SÍ se envía**:
- Primera vez que se aprueba una institución (código TEMP → RNR)

❌ **NO se envía**:
- Al desactivar una institución
- Al reactivar una institución ya aprobada
- Al editar datos de una institución aprobada

### Contenido del correo

```
Asunto: Cuenta Activada - Registro Nacional para Robótica Creativa

Estimado/a representante de [NOMBRE INSTITUCIÓN],

Su cuenta ha sido activada exitosamente.

Credenciales de acceso:
- Usuario: RNR26-011131421-B69TFUW7
- Contraseña: (la que usó al registrarse)

Puede iniciar sesión en:
http://localhost:8000/login/

Atentamente,
FVRC - Federación Venezolana de Robótica Creativa
```

---

## 🔍 Verificación del Flujo

### Paso 1: Verificar institución pendiente

```bash
cd SistemaRegistro
python manage.py shell
```

```python
from registry.models import Institucion

# Buscar institución pendiente
inst = Institucion.objects.filter(estatus='pendiente').first()

print(f"Nombre: {inst.nombre}")
print(f"Código: {inst.codigo}")  # Debe ser TEMP-XXXXXXXX
print(f"Activa: {inst.activa}")  # Debe ser False
print(f"Estatus: {inst.estatus}")  # Debe ser 'pendiente'

if inst.usuario:
    print(f"Username: {inst.usuario.username}")  # Debe ser TEMP-XXXXXXXX
    print(f"User is_active: {inst.usuario.is_active}")  # Debe ser False
```

### Paso 2: Aprobar desde el panel

1. Ir a: http://localhost:8000/instituciones/
2. Buscar institución con badge "PENDIENTE"
3. Activar el switch
4. Confirmar en el modal

### Paso 3: Verificar cambios

```python
# Refrescar datos
inst.refresh_from_db()
inst.usuario.refresh_from_db()

print(f"\nDespués de aprobar:")
print(f"Código: {inst.codigo}")  # Debe ser RNR26-...
print(f"Activa: {inst.activa}")  # Debe ser True
print(f"Estatus: {inst.estatus}")  # Debe ser 'aprobado'
print(f"Username: {inst.usuario.username}")  # Debe ser RNR26-...
print(f"User is_active: {inst.usuario.is_active}")  # Debe ser True
```

### Paso 4: Verificar correo en Mailtrap

1. Ir a: https://mailtrap.io/
2. Verificar bandeja de entrada
3. Confirmar que llegó correo con código RNR

---

## ✅ Checklist de Funcionamiento

### Registro
- [ ] Usuario completa formulario
- [ ] Código generado: TEMP-XXXXXXXX
- [ ] activa = False
- [ ] estatus = 'pendiente'
- [ ] usuario.is_active = False
- [ ] Usuario NO puede hacer login

### Aprobación
- [ ] Admin ve badge "PENDIENTE"
- [ ] Admin activa switch
- [ ] Modal de confirmación aparece
- [ ] Admin confirma
- [ ] Código cambia a RNR26-...
- [ ] activa = True
- [ ] estatus = 'aprobado'
- [ ] usuario.username = código RNR
- [ ] usuario.is_active = True
- [ ] Correo enviado a Mailtrap
- [ ] Usuario PUEDE hacer login

### Desactivación/Reactivación
- [ ] Admin desactiva switch
- [ ] activa = False
- [ ] usuario.is_active = False
- [ ] Usuario NO puede hacer login
- [ ] NO se envía correo
- [ ] Admin reactiva switch
- [ ] activa = True
- [ ] usuario.is_active = True
- [ ] Usuario PUEDE hacer login
- [ ] NO se envía correo (ya fue enviado antes)

---

## 🐛 Solución de Problemas

### Problema: Correo no se envía al aprobar

**Causa**: Código ya es RNR (no es TEMP)

**Solución**: Verificar que la institución tenga código TEMP antes de aprobar

```python
inst = Institucion.objects.get(id=1)
print(inst.codigo)  # Si no empieza con TEMP-, el correo no se enviará
```

### Problema: Usuario no puede hacer login después de aprobar

**Causa**: `usuario.is_active` sigue en False

**Solución**:
```python
inst = Institucion.objects.get(id=1)
inst.usuario.is_active = True
inst.usuario.save()
```

### Problema: Username no se actualiza a código RNR

**Causa**: El método save() no se ejecutó correctamente

**Solución**:
```python
inst = Institucion.objects.get(id=1)
inst.usuario.username = inst.codigo
inst.usuario.save()
```

---

## 📝 Notas Importantes

1. **Código TEMP es temporal**: Solo existe hasta la primera aprobación
2. **Código RNR es permanente**: No cambia aunque se desactive/reactive
3. **Correo solo se envía una vez**: En la primera aprobación
4. **Usuario bloqueado hasta aprobación**: `is_active=False` impide login
5. **Switch refleja estado actual**: Activado = puede login, Desactivado = no puede login

---

**Última actualización**: Febrero 2026
**Versión**: SNR-PRO v1.0
**Estado**: ✅ Implementado y Funcionando
