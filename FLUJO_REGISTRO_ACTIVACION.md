# 📋 Flujo Completo de Registro y Activación

## 🔄 Resumen del Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGISTRO DE INSTITUCIÓN                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Usuario completa el formulario de registro                  │
│     ├─ Datos de la institución                                  │
│     ├─ Email de contacto                                        │
│     └─ Contraseña                                               │
│                                                                 │
│  2. Sistema procesa el registro:                                  │
│     ├─ Genera código temporal: TEMP-XXXXXXXX                     │
│     ├─ Crea usuario con username = TEMP-XXXXXXXX                │
│     ├─ is_active = False (no puede acceder aún)                 │
│     └─ Estatus = "pendiente"                                    │
│                                                                 │
│  3. Usuario ve pantalla: "Registro Pendiente"                     │
│     └─ Espera aprobación del admin                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ACTIVACIÓN POR ADMIN                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Admin marca "Activa" en el Admin de Django                 │
│                                                                 │
│  2. Señal post_save detecta la activación:                        │
│     ├─ Genera código RNR permanente                             │
│     ├─ Actualiza username = código RNR                         │
│     ├─ Sincroniza is_active = True                              │
│     └─ Envía correo con credenciales                             │
│                                                                 │
│  3. Usuario recibe correo con:                                    │
│     ├─ Código RNR (su username)                                 │
│     ├─ Contraseña (la que usó al registrarse)                   │
│     └─ URL de login                                             │
│                                                                 │
│  4. Usuario puede acceder al sistema                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Código Temporal vs Permanente

### Código Temporal (TEMP-XXXXXXXX)
```python
# Durante registro:
TEMP-3A7B2C1D
# - Username del usuario: TEMP-3A7B2C1D
# - is_active: False
# - No puede hacer login
```

### Código Permanente (RNR26-XXX-XXX-XXXXXXXX)
```python
# Después de activación:
RNR26-001-002-003-XYZ12345
# - Username del usuario: RNR26-001-002-003-XYZ12345
# - is_active: True
# - Puede hacer login
# - Recibe correo con credenciales
```

---

## 🔧 Verificación del Flujo

### Paso 1: Verificar que las señales están cargadas

```bash
docker compose exec web python manage.py shell
```

```python
from django.db.models.signals import post_save
from registry.models import Institucion

# Verificar señales registradas
print("Señales post_save:")
for receiver in post_save.receivers:
    print(f"  - {receiver}")
    
# Debe mostrar las funciones de señales
```

### Paso 2: Verificar una institución registrada

```python
from registry.models import Institucion

# Obtener una institución pendiente
inst = Institucion.objects.filter(activa=False).first()

if inst:
    print(f"Institución: {inst.nombre}")
    print(f"Código: {inst.codigo}")
    print(f"Activa: {inst.activa}")
    
    if inst.usuario:
        print(f"Username: {inst.usuario.username}")
        print(f"User.is_active: {inst.usuario.is_active}")
```

### Paso 3: Activar y verificar cambio

```python
# Activar la institución
inst.activa = True
inst.save()

# Verificar cambios
inst.refresh_from_db()

print(f"\nDespués de activar:")
print(f"Código: {inst.codigo}")
print(f"Username: {inst.usuario.username}")
print(f"User.is_active: {inst.usuario.is_active}")

# Verificar en Mailtrap que llegó el correo
```

---

## 📧 Plantilla de Correo

La plantilla de correo [`templates/emails/aprobacion.html`](SistemaRegistro/templates/emails/aprobacion.html) incluye:

- ✅ Código RNR generado
- ✅ Usuario (el código RNR)
- ✅ Contraseña: La que usó al registrarse
- ✅ URL de login
- ✅ Instrucciones de acceso

---

## ⚙️ Archivos Clave

| Archivo | Función |
|---------|---------|
| [`users/views.py:403`](SistemaRegistro/users/views.py:403) | `registrar_institucion()` - Crea usuario con código TEMP |
| [`users/forms.py:278`](SistemaRegistro/users/forms.py:278) | Genera código TEMP |
| [`registry/models.py:251`](SistemaRegistro/registry/models.py:251) | `save()` - Genera código RNR permanente |
| [`registry/signals.py`](SistemaRegistro/registry/signals.py) | Detecta activación y envía correo |
| [`templates/emails/aprobacion.html`](SistemaRegistro/templates/emails/aprobacion.html) | Template del correo |

---

## 🔍 Diagnóstico

### Problema: No se envía el correo

1. **Verificar que las señales están cargadas:**
   ```bash
   docker compose exec web python manage.py shell
   # Ejecutar código de verificación anterior
   ```

2. **Verificar los logs:**
   ```bash
   tail -f SistemaRegistro/logs/django.log
   ```

3. **Verificar que el código es permanente:**
   ```python
   # El código debe empezar con RNR, no TEMP
   inst.codigo.startswith('RNR')  # Debe ser True
   ```

4. **Verificar que tiene usuario:**
   ```python
   inst.usuario is not None  # Debe ser True
   ```

### Problema: Username no se actualiza

El username se actualiza en el método `save()` del modelo:

```python
# registry/models.py línea 271-273
if self.usuario and self.usuario.username != self.codigo:
    self.usuario.activa and self.username = self.codigo
    self.usuario.save(update_fields=["username"])
```

Verificar:
- ✅ `self.activa` es `True`
- ✅ `self.usuario` existe
- ✅ `self.codigo` empieza con `RNR`

---

## ✅ Checklist de Verificación

### Antes de activar:
- [ ] Institución tiene código temporal (TEMP-XXXXXXXX)
- [ ] Usuario.username = código temporal
- [ ] User.is_active = False
- [ ] is_active = False

### Después de activar:
- [ ] Código cambió a RNR permanente
- [ ] Usuario.username = código RNR
- [ ] User.is_active = True
- [ ] is_active = True
- [ ] Correo recibido en Mailtrap
- [ ] Usuario puede hacer login

---

## 🎯 Ejemplo Completo

```python
# Antes de activar
print("=== ANTES ===")
inst = Institucion.objects.filter(activa=False).first()
print(f"Institución: {inst.nombre}")
print(f"Código: {inst.codigo}")
print(f"Username: {inst.usuario.username}")
print(f"is_active: {inst.usuario.is_active}")

# Activar
inst.activa = True
inst.save()

# Después de activar
print("\n=== DESPUÉS ===")
inst.refresh_from_db()
print(f"Institución: {inst.nombre}")
print(f"Código: {inst.codigo}")
print(f"Username: {inst.usuario.username}")
print(f"is_active: {inst.usuario.is_active}")

# Verificar correo en Mailtrap
print("\n✅ Verificar correo en Mailtrap")
```

**Salida esperada:**
```
=== ANTES ===
Institución: Escuela Ejemplo
Código: TEMP-3A7B2C1D
Username: TEMP-3A7B2C1D
is_active: False

=== DESPUÉS ===
Institución: Escuela Ejemplo
Código: RNR26-001-002-003-XYZ12345
Username: RNR26-001-002-003-XYZ12345
is_active: True

✅ Verificar correo en Mailtrap
```

---

**Última actualización:** Febrero 2026
