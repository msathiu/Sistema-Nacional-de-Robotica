# 🔄 Flujo de Activación de Instituciones

## 📋 Resumen

Este documento explica el flujo completo de activación de instituciones y la sincronización entre los modelos `Institucion` y `User`.

---

## 🎯 Campo Principal de Activación

### `Institucion.activa` (BooleanField)

**Este es el campo principal que controla la activación de una institución.**

- ✅ `activa=True`: Institución activa, puede acceder al sistema
- ❌ `activa=False`: Institución inactiva, NO puede acceder al sistema

### Sincronización con `User.is_active`

El campo `User.is_active` se sincroniza automáticamente con `Institucion.activa`:

```python
# Cuando cambias Institucion.activa
institucion.activa = True
institucion.save()

# Automáticamente se actualiza
institucion.usuario.is_active = True  # Sincronizado
```

---

## 🔄 Flujo Completo de Activación

### 1️⃣ Registro Inicial

```
Usuario se registra como institución
    ↓
Se crea User con is_active=True (por defecto de Django)
    ↓
Se crea Institucion con:
    - activa=False (inactiva por defecto)
    - codigo="TEMP-XXXXXXXX" (código temporal)
    - estatus="pendiente"
    ↓
Usuario NO puede acceder al sistema (activa=False)
```

### 2️⃣ Activación por Admin

**Desde el Admin de Django:**

```
Admin marca Institucion.activa=True
    ↓
Señal pre_save guarda estado anterior
    ↓
Modelo save() detecta activación:
    - Genera código RNR permanente
    - Actualiza estatus="aprobado"
    - Actualiza username con código RNR
    ↓
Señal post_save detecta activación:
    - Sincroniza User.is_active=True
    - Verifica que código sea RNR (no TEMP-)
    - Envía correo con código e instrucciones
    ↓
Usuario recibe correo y puede acceder al sistema
```

### 3️⃣ Desactivación

```
Admin marca Institucion.activa=False
    ↓
Señal post_save sincroniza:
    - User.is_active=False
    ↓
Usuario NO puede acceder al sistema
```

---

## 🔐 Condiciones para Envío de Correo

El correo de activación se envía **SOLO** si se cumplen TODAS estas condiciones:

1. ✅ `Institucion.activa` cambió de `False` a `True`
2. ✅ El código es permanente (empieza con `RNR`)
3. ✅ El código NO es temporal (NO empieza con `TEMP-`)
4. ✅ La institución tiene un usuario asociado

### Ejemplo de Logs

**Activación exitosa:**
```
INFO Activación detectada para Escuela Ejemplo.
INFO Usuario RNR26-001002003-ABC12345 sincronizado: is_active=True
INFO Correo de activación enviado exitosamente a escuela@example.com
```

**Activación con código temporal (NO envía correo):**
```
WARNING Institución Escuela Ejemplo activada pero tiene código temporal.
WARNING No se envía correo. Código: TEMP-ABC12345
```

---

## 🎛️ Campos en el Admin de Django

### Modelo User (django.contrib.auth.models.User)

- **`is_active`**: Se sincroniza automáticamente con `Institucion.activa`
- **`username`**: Se actualiza automáticamente con el código RNR

### Modelo Institucion

- **`activa`**: Campo principal de activación ⭐
- **`codigo`**: Código temporal (TEMP-) o permanente (RNR)
- **`estatus`**: Estado de la solicitud (pendiente/aprobado/rechazado)

---

## 📝 Recomendaciones de Uso

### Para Activar una Institución:

1. **Ir al Admin de Django** → Instituciones
2. **Seleccionar la institución** con `activa=False`
3. **Marcar el checkbox "Activa"**
4. **Guardar**

**Resultado:**
- ✅ Se genera código RNR permanente
- ✅ Se actualiza username del usuario
- ✅ Se sincroniza `User.is_active=True`
- ✅ Se envía correo automáticamente
- ✅ Usuario puede acceder al sistema

### Para Desactivar una Institución:

1. **Ir al Admin de Django** → Instituciones
2. **Seleccionar la institución** con `activa=True`
3. **Desmarcar el checkbox "Activa"**
4. **Guardar**

**Resultado:**
- ✅ Se sincroniza `User.is_active=False`
- ✅ Usuario NO puede acceder al sistema
- ✅ El código RNR se mantiene (no se pierde)

---

## 🔍 Verificación

### Verificar estado de una institución:

```bash
python manage.py shell
```

```python
from registry.models import Institucion

inst = Institucion.objects.get(codigo="RNR26-001002003-ABC12345")

print(f"Institución: {inst.nombre}")
print(f"Activa: {inst.activa}")
print(f"Código: {inst.codigo}")
print(f"Estatus: {inst.estatus}")

if inst.usuario:
    print(f"Usuario: {inst.usuario.username}")
    print(f"User.is_active: {inst.usuario.is_active}")
    print(f"Sincronizado: {inst.activa == inst.usuario.is_active}")
```

### Ver logs de activación:

```bash
tail -f SistemaRegistro/logs/django.log | grep "Activación"
```

---

## ⚠️ Casos Especiales

### Caso 1: Institución con código temporal

```python
# Institución con código TEMP-
inst.activa = True
inst.save()

# Resultado:
# - User.is_active = True (sincronizado)
# - NO se envía correo (código temporal)
# - Log: "activada pero tiene código temporal"
```

### Caso 2: Cambio de código sin activación

```python
# Institución ya activa, solo cambio de código
inst.codigo = "RNR26-001002003-NEW12345"
inst.save()

# Resultado:
# - NO se envía correo (ya estaba activa)
# - Username se actualiza con nuevo código
```

### Caso 3: Reactivación

```python
# Institución que fue desactivada y se reactiva
inst.activa = False
inst.save()  # Desactivación

inst.activa = True
inst.save()  # Reactivación

# Resultado:
# - Se envía correo nuevamente
# - User.is_active = True
```

---

## 🎯 Diagrama de Estados

```
┌─────────────────┐
│   REGISTRO      │
│  activa=False   │
│  codigo=TEMP-   │
└────────┬────────┘
         │
         │ Admin marca activa=True
         ↓
┌─────────────────┐
│   ACTIVADA      │
│  activa=True    │
│  codigo=RNR     │
│  ✉️ Correo      │
└────────┬────────┘
         │
         │ Admin marca activa=False
         ↓
┌─────────────────┐
│  DESACTIVADA    │
│  activa=False   │
│  codigo=RNR     │
│  (mantiene)     │
└────────┬────────┘
         │
         │ Admin marca activa=True
         ↓
┌─────────────────┐
│  REACTIVADA     │
│  activa=True    │
│  codigo=RNR     │
│  ✉️ Correo      │
└─────────────────┘
```

---

## ✅ Checklist de Activación

Antes de activar una institución, verificar:

- [ ] La institución tiene todos los datos completos
- [ ] El email es válido
- [ ] La institución tiene un usuario asociado
- [ ] El código es temporal (TEMP-) o vacío
- [ ] El campo `activa` está en `False`

Después de activar:

- [ ] Se generó código RNR permanente
- [ ] El username del usuario se actualizó
- [ ] `User.is_active` está en `True`
- [ ] Se envió el correo (verificar en Mailtrap/logs)
- [ ] El usuario puede hacer login

---

**Última actualización:** Febrero 2026  
**Mantenido por:** Equipo de Desarrollo SNR
