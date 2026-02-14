# 🧪 Prueba de Envío de Correo de Activación

## 📋 Configuración Previa

### 1. Verificar Configuración de Email en `.env`

Asegúrate de que tu archivo `.env` tenga la configuración correcta de Mailtrap:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=tu_usuario_mailtrap
EMAIL_HOST_PASSWORD=tu_password_mailtrap
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=registro@fvrc.org.ve
SITE_NAME=Registro Nacional para Robótica Creativa
BASE_URL=http://localhost:8000
```

### 2. Verificar que las Señales están Registradas

Asegúrate de que en [`settings.py`](SistemaRegistro/SistemaRegistro/settings.py) la app `registry` esté configurada correctamente:

```python
INSTALLED_APPS = [
    # ...
    'registry.apps.RegistryConfig',  # Debe usar RegistryConfig
    # ...
]
```

### 3. Reiniciar el Servidor

Después de los cambios, reinicia el servidor de Django:

```bash
# Detener el servidor actual (Ctrl+C)
# Luego reiniciar:
python manage.py runserver
```

---

## 🧪 Métodos de Prueba

### Método 1: Desde el Admin de Django (Recomendado)

1. **Acceder al Admin:**
   ```
   http://localhost:8000/admin/
   ```

2. **Ir a Instituciones:**
   - Click en "Instituciones"
   - Seleccionar una institución con `activa=False`

3. **Activar la Institución:**
   - Marcar el checkbox "Activa"
   - Click en "Guardar"

4. **Verificar en Mailtrap:**
   - Ir a tu inbox de Mailtrap
   - Deberías ver el correo de activación

5. **Verificar en Logs:**
   ```bash
   tail -f SistemaRegistro/logs/django.log
   ```

   Deberías ver:
   ```
   INFO Activación detectada para [Nombre Institución]...
   INFO Correo de activación enviado exitosamente a [email]
   ```

### Método 2: Desde el Shell de Django

```bash
python manage.py shell
```

```python
from registry.models import Institucion

# Obtener una institución inactiva
inst = Institucion.objects.filter(activa=False).first()

if inst:
    print(f"Institución: {inst.nombre}")
    print(f"Email: {inst.email}")
    print(f"Código actual: {inst.codigo}")
    print(f"Activa: {inst.activa}")

    # Activar la institución
    inst.activa = True
    inst.save()

    print(f"\n✅ Institución activada")
    print(f"Nuevo código: {inst.codigo}")
    print(f"Verifica tu inbox de Mailtrap")
else:
    print("No hay instituciones inactivas para probar")
```

### Método 3: Probar Envío Directo

```bash
python manage.py shell
```

```python
from registry.models import Institucion

# Obtener una institución activa
inst = Institucion.objects.filter(activa=True).first()

if inst:
    print(f"Probando envío de correo a: {inst.email}")

    # Enviar correo directamente
    resultado = inst.enviar_correo_activacion()

    if resultado:
        print("✅ Correo enviado exitosamente")
    else:
        print("❌ Error al enviar correo")
else:
    print("No hay instituciones activas")
```

---

## 🔍 Diagnóstico de Problemas

### Problema 1: No se envía el correo

**Verificar configuración de email:**

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

print("Configuración de Email:")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Probar envío simple
try:
    send_mail(
        'Test',
        'Mensaje de prueba',
        settings.DEFAULT_FROM_EMAIL,
        ['test@example.com'],
        fail_silently=False,
    )
    print("\n✅ Configuración de email correcta")
except Exception as e:
    print(f"\n❌ Error: {e}")
```

### Problema 2: Las señales no se ejecutan

**Verificar que las señales están registradas:**

```bash
python manage.py shell
```

```python
from django.db.models.signals import post_save, pre_save
from registry.models import Institucion

# Ver señales registradas
print("Señales pre_save:")
for receiver in pre_save.receivers:
    print(f"  - {receiver}")

print("\nSeñales post_save:")
for receiver in post_save.receivers:
    print(f"  - {receiver}")
```

### Problema 3: Error en el template

**Verificar que el template existe:**

```bash
ls -la SistemaRegistro/templates/emails/aprobacion.html
```

Si no existe, el archivo debería estar en:
```
SistemaRegistro/templates/emails/aprobacion.html
```

---

## 📊 Verificación de Logs

### Ver logs en tiempo real:

```bash
tail -f SistemaRegistro/logs/django.log
```

### Buscar logs de activación:

```bash
grep "Activación detectada" SistemaRegistro/logs/django.log
```

### Buscar logs de correo:

```bash
grep "Correo de activación" SistemaRegistro/logs/django.log
```

### Buscar errores:

```bash
grep "ERROR" SistemaRegistro/logs/django.log | tail -20
```

---

## ✅ Checklist de Verificación

Antes de probar, verifica:

- [ ] Archivo `.env` configurado con credenciales de Mailtrap
- [ ] Servidor Django reiniciado después de cambios
- [ ] App `registry` usa `RegistryConfig` en `INSTALLED_APPS`
- [ ] Archivo `registry/signals.py` existe
- [ ] Archivo `registry/apps.py` existe y registra señales
- [ ] Template `templates/emails/aprobacion.html` existe
- [ ] Directorio `logs/` existe

---

## 🎯 Resultado Esperado

Cuando actives una institución, deberías ver:

1. **En los logs:**
   ```
   INFO Activación detectada para [Nombre]...
   INFO Correo de activación enviado exitosamente a [email]
   ```

2. **En Mailtrap:**
   - Un correo con el asunto "Cuenta Activada - Registro Nacional para Robótica Creativa"
   - Contenido HTML con el código RNR
   - Instrucciones de acceso

3. **En la base de datos:**
   - `activa = True`
   - `estatus = 'aprobado'`
   - `codigo` cambiado de `TEMP-XXXXXXXX` a `RNR26-XXXXXXXXX-XXXXXXXX`
   - `username` del usuario actualizado con el código RNR

---

## 🆘 Soporte

Si después de seguir estos pasos el correo no se envía:

1. Revisa los logs: `tail -f SistemaRegistro/logs/django.log`
2. Verifica la configuración de Mailtrap en su panel web
3. Prueba el envío directo desde el shell (Método 3)
4. Verifica que no haya errores en la consola del servidor Django

---

**Última actualización:** Febrero 2026
