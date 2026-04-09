# Guía de Configuración del Servidor — RNR-PRO

> Stack: Python 3.12 · Django 5.0 · PostgreSQL 17 · Nginx · Docker Compose  
> Última revisión: 2026-04-07

---

## 1. Requisitos del Servidor

| Componente | Mínimo recomendado |
|---|---|
| OS | Ubuntu 22.04 LTS / Debian 12 |
| RAM | 2 GB |
| CPU | 2 vCPU |
| Disco | 20 GB |
| Docker | 24+ |
| Docker Compose | v2.20+ |

```bash
# Instalar Docker en Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

---

## 2. Variables de Entorno (`.env`)

Copiar `.env.example` y ajustar **todos** los valores antes de levantar:

```bash
cp .env.example .env
```

Variables críticas para producción:

```env
# Generar con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=<clave-unica-generada>

DEBUG=False

# Dominio real del servidor
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# PostgreSQL
POSTGRES_DB=robotica_db
POSTGRES_USER=<usuario_db>
POSTGRES_PASSWORD=<password_segura>
DATABASE_URL=postgresql://<usuario_db>:<password_segura>@db:5432/robotica_db

# Email (producción — usar SMTP real, no Mailtrap)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.tuproveedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=<correo>
EMAIL_HOST_PASSWORD=<password_email>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=registro@fvrc.org.ve

# Seguridad HTTPS
CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000

# URL base del sitio
BASE_URL=https://tudominio.com

DJANGO_SETTINGS_MODULE=SistemaRegistro.settings
```

---

## 3. Docker Compose — Producción

El proyecto incluye `docker-compose-prod.yml`. Para producción se recomienda
usarlo directamente o renombrarlo a `docker-compose.yml`.

Servicios que levanta:
- `db` — PostgreSQL 17
- `web` — Django + Gunicorn
- `nginx` — Proxy reverso + archivos estáticos
- `certbot` — Certificados SSL (Let's Encrypt)

```bash
# Primera vez
docker compose -f docker-compose-prod.yml up --build -d

# Ver logs
docker compose -f docker-compose-prod.yml logs -f web

# Detener
docker compose -f docker-compose-prod.yml down
```

---

## 4. Inicialización del Sistema (primera vez)

Ejecutar en orden después de levantar los contenedores:

```bash
# 1. Aplicar migraciones
docker compose exec web python manage.py migrate

# 2. Recolectar archivos estáticos
docker compose exec web python manage.py collectstatic --noinput

# 3. Crear superusuario (asigna user_type='superusuario' automáticamente)
docker compose exec web python manage.py createsuperuser

# 4. Cargar líneas de investigación iniciales (si aplica)
docker compose exec web python manage.py crear_lineas_investigacion
```

---

## 5. Nginx — Configuración HTTPS

El archivo `nginx.conf` actual solo cubre HTTP (puerto 80). Para producción
con SSL, reemplazar su contenido:

```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name tudominio.com www.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tudominio.com/privkey.pem;

    client_max_body_size 20M;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }
}
```

### Obtener certificado SSL con Certbot

```bash
# Levantar solo nginx y certbot primero
docker compose -f docker-compose-prod.yml up -d nginx certbot

# Solicitar certificado
docker compose -f docker-compose-prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d tudominio.com -d www.tudominio.com \
  --email admin@tudominio.com --agree-tos --no-eff-email

# Levantar el resto
docker compose -f docker-compose-prod.yml up -d
```

---

## 6. Cache

El sistema usa `django.core.cache` en los context processors para:
- Contador de clubes pendientes (federación) — TTL 300s
- Contador de solicitudes de eliminación pendientes — TTL 300s

**En desarrollo** usa `LocMemCache` (configurado en `settings.py`).  
**En producción** se recomienda Redis para cache compartida entre workers de Gunicorn:

### 6.1 Agregar Redis al docker-compose-prod.yml

```yaml
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - backend_network
```

### 6.2 Instalar dependencia

```bash
# Agregar a requirements.txt
django-redis==5.4.0
```

### 6.3 Configurar en settings.py

```python
# Reemplazar el bloque CACHES en producción (DEBUG=False)
if not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
```

### 6.4 Variable de entorno

```env
REDIS_URL=redis://redis:6379/1
```

> **Nota:** Si no se configura Redis, el sistema funciona correctamente con
> `LocMemCache`, pero en producción con múltiples workers Gunicorn cada proceso
> tendrá su propia cache independiente.

---

## 7. Tareas Programadas con Cron

El sistema tiene comandos de gestión que deben ejecutarse periódicamente.

### 7.1 Comando `actualizar_estados_eventos`

Recalcula automáticamente los estados de eventos según la fecha actual:
- `abierto` → `en_proceso` cuando comienza el evento
- `abierto` / `en_proceso` → `finalizado` cuando vence la fecha

**Configurar en crontab del servidor host:**

```bash
# Editar crontab
crontab -e
```

Agregar las siguientes líneas:

```cron
# Actualizar estados de eventos — todos los días a la 1:00 AM
0 1 * * * docker compose -f /ruta/al/proyecto/docker-compose-prod.yml exec -T web python manage.py actualizar_estados_eventos >> /var/log/rnr/cron_eventos.log 2>&1

# Limpiar cache del sistema — todos los lunes a las 2:00 AM
0 2 * * 1 docker compose -f /ruta/al/proyecto/docker-compose-prod.yml exec -T web python manage.py limpiar_cache >> /var/log/rnr/cron_cache.log 2>&1
```

> El flag `-T` es obligatorio en cron para evitar errores de TTY.

### 7.2 Crear directorio de logs para cron

```bash
sudo mkdir -p /var/log/rnr
sudo chown $USER:$USER /var/log/rnr
```

### 7.3 Verificar que el cron funciona

```bash
# Ejecutar manualmente para probar
docker compose exec web python manage.py actualizar_estados_eventos --verbose

# Modo dry-run (sin persistir cambios)
docker compose exec web python manage.py actualizar_estados_eventos --dry-run --verbose

# Incluir eventos pausados vencidos
docker compose exec web python manage.py actualizar_estados_eventos --incluir-pausados
```

---

## 8. Gunicorn — Workers en Producción

El `Dockerfile` ya usa Gunicorn. Para ajustar workers según el servidor:

```bash
# Regla general: (2 × núcleos_CPU) + 1
# Para 2 vCPU → 5 workers
```

Modificar el CMD en `Dockerfile-prod`:

```dockerfile
CMD ["gunicorn", "SistemaRegistro.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "5", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

---

## 9. PostgreSQL — Respaldos

```bash
# Backup manual
docker compose exec db pg_dump -U <usuario_db> robotica_db > backup_$(date +%Y%m%d).sql

# Restaurar
docker compose exec -T db psql -U <usuario_db> robotica_db < backup_20260407.sql
```

### Cron para backup automático diario

```cron
# Backup de base de datos — todos los días a las 3:00 AM
0 3 * * * docker compose -f /ruta/al/proyecto/docker-compose-prod.yml exec -T db pg_dump -U <usuario_db> robotica_db > /var/backups/rnr/db_$(date +\%Y\%m\%d).sql 2>> /var/log/rnr/cron_backup.log
```

```bash
sudo mkdir -p /var/backups/rnr
sudo chown $USER:$USER /var/backups/rnr
```

---

## 10. Logs del Sistema

Django escribe logs rotativos en `logs/django.log` (máx. 10 MB × 5 archivos).
El volumen `./logs:/app/logs` en `docker-compose.yml` los persiste en el host.

```bash
# Ver logs en tiempo real
tail -f logs/django.log

# Ver logs del contenedor web
docker compose logs -f web

# Ver logs de nginx
docker compose logs -f nginx
```

---

## 11. Resumen de Comandos de Gestión Disponibles

| Comando | Descripción | Frecuencia sugerida |
|---|---|---|
| `actualizar_estados_eventos` | Recalcula estados según fecha | Diario 1:00 AM |
| `limpiar_cache` | Limpia cache y archivos temporales | Semanal |
| `createsuperuser` | Crea superusuario con tipo correcto | Una vez |
| `crear_lineas_investigacion` | Carga líneas de investigación | Una vez |
| `verificar_instituciones` | Verifica integridad de instituciones | Manual |
| `verificar_perfil` | Verifica perfiles de usuario | Manual |

---

## 12. Checklist de Despliegue

- [ ] `.env` configurado con valores de producción
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` única generada
- [ ] `ALLOWED_HOSTS` con dominio real
- [ ] `CSRF_TRUSTED_ORIGINS` con dominio HTTPS
- [ ] Certificado SSL obtenido (Certbot)
- [ ] `nginx.conf` actualizado para HTTPS
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Estáticos recolectados (`collectstatic`)
- [ ] Superusuario creado
- [ ] Cron configurado para `actualizar_estados_eventos`
- [ ] Cron configurado para backup de base de datos
- [ ] Directorio de logs con permisos correctos
- [ ] Redis configurado (opcional pero recomendado para producción)
