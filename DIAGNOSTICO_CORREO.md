# 🔧 Diagnóstico: Correo de Activación No Llega

## 📋 Pasos de Diagnóstico

### Paso 1: Verificar que las señales están registradas

```bash
docker compose exec web python manage.py shell
```

```python
# Verificar señales registradas
from django.db.models.signals import post_save, pre_save
from registry.models import Institucion

print("=== SEÑALES REGISTRADAS ===")
print("pre_save receivers:")
for receiver in pre_save.receivers:
    print(f"  - {receiver[1].__name__ if len(receiver) > 1 else 'Unknown'}")

print("\npost_save receivers:")
for receiver in post_save.receivers:
    print(f"  - {receiver[1].__name__ if len(receiver) > 1 else 'Unknown'}")
```

**Debes ver:**
- `detectar_activacion_institucion`
- `enviar_correo_activacion_institucion`

---

### Paso 2: Probar envío directo de correo

```python
from django.core.mail import send_mail
from django.conf import settings

print("\n=== CONFIGURACIÓN DE EMAIL ===")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")

# Probar envío directo
try:
    resultado = send_mail(
        'Test Subject',
        'Test message body',
        settings.DEFAULT_FROM_EMAIL,
        ['tu_email@ejemplo.com'],  # Cambia a tu email real
        fail_silently=False,
    )
    print(f"\n✅ RESULTADO: {resultado} correo(s) enviado(s)")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
```

---

### Paso 3: Probar método de envío de correo

```python
from registry.models import Institucion

# Obtener una institución
inst = Institucion.objects.filter(activa=True).first()

if inst:
    print("\n=== PROBANDO ENVÍO DE CORREO ===")
    print(f"Institución: {inst.nombre}")
    print(f"Email: {inst.email}")

    resultado = inst.enviar_correo_activacion()

    if resultado:
        print("✅ Correo enviado exitosamente")
        print("📬 Revisa tu inbox de Mailtrap")
    else:
        print("❌ Error al enviar correo")
        print("📋 Revisa los logs para más detalles")
else:
    print("No hay instituciones para probar")
```

---

### Paso 4: Probar activación completa

```python
from registry.models import Institucion

# Obtener institución inactiva
inst = Institucion.objects.filter(activa=False).first()

if inst:
    print("\n=== PRUEBA DE ACTIVACIÓN ===")
    print(f"Institución: {inst.nombre}")
    print(f"Código actual: {inst.codigo}")
    print(f"Activa: {inst.activa}")

    if inst.usuario:
        print(f"Username: {inst.usuario.username}")
        print(f"User.is_active: {inst.usuario.is_active}")

    # Activar
    print("\n⚡ Activando...")
    inst.activa = True
    inst.save()

    # Verificar
    inst.refresh_from_db()
    print(f"\n✅ Después de activar:")
    print(f"Código: {inst.codigo}")
    print(f"Activa: {inst.activa}")

    if inst.usuario:
        print(f"Username: {inst.usuario.username}")
        print(f"User.is_active: {inst.usuario.is_active}")

    print("\n📬 Verifica Mailtrap para el correo")
else:
    print("No hay instituciones inactivas para probar")
```

---

## 🔍 Verificar Logs

```bash
# Ver todos los logs
tail -f SistemaRegistro/logs/django.log

# Buscar específicamente activaciones
grep -i "activacion\|correo\|error" SistemaRegistro/logs/django.log | tail -20
```

---

## ⚠️ Problemas Comunes y Soluciones

### Problema 1: Señales no registradas

**Síntoma:** No aparece nada en los logs al activar

**Solución:**
1. Verificar que `settings.py` usa `RegistryConfig`:
```python
LOCAL_APPS = [
    "users.apps.UsersConfig",
    "registry.apps.RegistryConfig",  # ← Debe ser así
]
```

2. Reiniciar completamente:
```bash
docker compose down
docker compose up --build
```

---

### Problema 2: Error en template

**Síntoma:** Error en logs relacionado con `aprobacion.html`

**Solución:**
Verificar que el template existe:
```bash
ls -la SistemaRegistro/templates/emails/aprobacion.html
```

Si no existe, crear el archivo con el contenido del template.

---

### Problema 3: Error en send_mail

**Síntoma:** `AttributeError` o `NameError`

**Solución:**
Verificar imports en `models.py`:
```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
```

---

### Problema 4: Credenciales de Mailtrap incorrectas

**Síntoma:** Conexión rechazada

**Solución:**
Verificar `.env`:
```env
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=tu_usuario
EMAIL_HOST_PASSWORD=tu_password
```

---

## 📋 Checklist de Verificación

- [ ] Señales registradas correctamente
- [ ] Template `aprobacion.html` existe
- [ ] Credenciales de Mailtrap correctas
- [ ] Institución tiene código RNR (no TEMP)
- [ ] Institución tiene usuario asociado
- [ ] Logs muestran la activación

---

## 🔧 Solución Rápida

Si funcionó antes y ahora no funciona, probablemente hubo un cambio en:

1. **Archivo `settings.py`** - Verificar que usa `RegistryConfig`
2. **Archivo `registry/signals.py`** - Verificar que existe
3. **Archivo `registry/apps.py`** - Verificar que importa las señales

Para forzar una recarga completa:

```bash
# Detener contenedores
docker compose down

# Eliminar caches
docker compose exec web rm -rf __pycache__
docker compose exec web find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Recrear contenedores
docker compose up --build -d

# Verificar
docker compose logs -f web
```
