# 🔐 INSTRUCCIONES: Configurar .env

## ⚠️ IMPORTANTE
El archivo `.env` contiene información sensible y **NUNCA** debe ser versionado en Git.
Ya está incluido en `.gitignore`.

---

## 📝 Pasos para Configurar

### 1. Crear el archivo .env

```bash
# Copiar desde el template
cp .env.example .env
```

### 2. Generar SECRET_KEY única

```bash
# Ejecutar este comando
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copiar el resultado (algo como):
# django-insecure-abc123xyz789...
```

### 3. Editar el archivo .env

Abre `.env` con tu editor favorito y configura:

```bash
# ============================================
# CONFIGURACIÓN DEL SISTEMA NACIONAL DE ROBÓTICA
# ============================================

# --- SEGURIDAD ---
# PEGAR AQUÍ LA SECRET_KEY GENERADA EN EL PASO 2
SECRET_KEY=django-insecure-abc123xyz789...

# Modo de depuración
# DESARROLLO: True
# PRODUCCIÓN: False
DEBUG=False

# Hosts permitidos (tu dominio)
# DESARROLLO: localhost,127.0.0.1
# PRODUCCIÓN: tudominio.com,www.tudominio.com
ALLOWED_HOSTS=localhost,127.0.0.1

# --- BASE DE DATOS ---
# DESARROLLO: SQLite
DATABASE_URL=sqlite:///db.sqlite3

# PRODUCCIÓN: PostgreSQL (descomentar y configurar)
# DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/robotica_db

# --- CONFIGURACIÓN DE EMAIL ---
# Configurar con tus credenciales reales
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=tu_usuario_aqui
EMAIL_HOST_PASSWORD=tu_password_aqui
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=registro@fvrc.org.ve

# --- CONFIGURACIÓN DEL SITIO ---
SITE_NAME=Registro Nacional para Robótica Creativa
BASE_URL=http://localhost:8000

# --- SEGURIDAD ADICIONAL (Producción) ---
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://tudominio.com
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=31536000

# --- LOGGING ---
LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=INFO

# --- DJANGO SETTINGS MODULE ---
DJANGO_SETTINGS_MODULE=SistemaRegistro.settings
```

---

## 🔍 Verificar Configuración

Después de editar `.env`, verifica que todo esté correcto:

```bash
# Ejecutar script de verificación
python verificar_seguridad.py

# O en Windows
verificar_seguridad.bat
```

Debes ver:
```
✅ Archivo .env configurado correctamente
✅ Modo DEBUG verificado
✅ No se encontraron credenciales hardcodeadas
✅ Decoradores de seguridad implementados
✅ Middlewares de seguridad configurados
✅ Endpoints críticos protegidos
```

---

## 📧 Configurar Email (Mailtrap para Testing)

### Opción 1: Mailtrap (Recomendado para desarrollo)

1. Crear cuenta en https://mailtrap.io
2. Ir a "Email Testing" → "Inboxes"
3. Copiar credenciales SMTP
4. Configurar en `.env`:

```bash
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=tu_usuario_mailtrap
EMAIL_HOST_PASSWORD=tu_password_mailtrap
```

### Opción 2: Gmail (Para producción)

1. Habilitar "Acceso de apps menos seguras" o usar "Contraseñas de aplicación"
2. Configurar en `.env`:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_password_o_app_password
EMAIL_USE_TLS=True
```

### Opción 3: SendGrid (Para producción)

1. Crear cuenta en https://sendgrid.com
2. Crear API Key
3. Configurar en `.env`:

```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=tu_sendgrid_api_key
EMAIL_USE_TLS=True
```

---

## 🗄️ Configurar Base de Datos

### Desarrollo (SQLite - Por defecto)
```bash
DATABASE_URL=sqlite:///db.sqlite3
```

### Producción (PostgreSQL)

1. Instalar PostgreSQL
2. Crear base de datos:
```sql
CREATE DATABASE robotica_db;
CREATE USER robotica_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE robotica_db TO robotica_user;
```

3. Configurar en `.env`:
```bash
DATABASE_URL=postgresql://robotica_user:tu_password_seguro@localhost:5432/robotica_db
```

---

## 🌐 Configurar para Producción

### Cambios necesarios en .env:

```bash
# 1. Cambiar DEBUG a False
DEBUG=False

# 2. Configurar hosts permitidos con tu dominio
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# 3. Configurar orígenes CSRF confiables
CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com

# 4. Habilitar redirección SSL (si tienes HTTPS)
SECURE_SSL_REDIRECT=True

# 5. Cambiar BASE_URL
BASE_URL=https://tudominio.com

# 6. Usar PostgreSQL
DATABASE_URL=postgresql://usuario:password@localhost:5432/robotica_db

# 7. Configurar email de producción (no Mailtrap)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu_email_real@gmail.com
EMAIL_HOST_PASSWORD=tu_password_real
```

---

## ✅ Checklist Final

Antes de ejecutar el sistema, verifica:

- [ ] Archivo `.env` creado
- [ ] `SECRET_KEY` única generada (no la default)
- [ ] `DEBUG` configurado apropiadamente
- [ ] `ALLOWED_HOSTS` configurado
- [ ] Credenciales de email configuradas
- [ ] Base de datos configurada
- [ ] Script de verificación ejecutado exitosamente
- [ ] `.env` NO está en Git (verificar con `git status`)

---

## 🚨 Seguridad

### ⚠️ NUNCA:
- ❌ Subir `.env` a Git
- ❌ Compartir `.env` por email/chat
- ❌ Usar la misma SECRET_KEY en desarrollo y producción
- ❌ Dejar DEBUG=True en producción
- ❌ Usar credenciales de prueba en producción

### ✅ SIEMPRE:
- ✅ Mantener `.env` en `.gitignore`
- ✅ Usar SECRET_KEY única por entorno
- ✅ Rotar credenciales periódicamente
- ✅ Usar HTTPS en producción
- ✅ Hacer backup de `.env` de forma segura

---

## 🆘 Solución de Problemas

### Error: "SECRET_KEY debe estar configurada"
```bash
# Verificar que SECRET_KEY no esté vacía
cat .env | grep SECRET_KEY

# Si está vacía, generar nueva
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Error: "No such file or directory: '.env'"
```bash
# Verificar que .env existe
ls -la .env

# Si no existe, crear desde template
cp .env.example .env
```

### Error: Email no se envía
```bash
# Verificar credenciales
cat .env | grep EMAIL

# Probar conexión SMTP
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

---

## 📚 Referencias

- **Documentación Django:** https://docs.djangoproject.com/en/5.0/topics/settings/
- **python-dotenv:** https://pypi.org/project/python-dotenv/
- **Mailtrap:** https://mailtrap.io/
- **PostgreSQL:** https://www.postgresql.org/docs/

---

**Última actualización:** $(date)
**Versión:** SNR-PRO v1.0
