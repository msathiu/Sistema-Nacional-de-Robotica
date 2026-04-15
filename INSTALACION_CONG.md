# 📋 Guía de Instalación y Configuración - RNR-PRO

> **Sistema Nacional de Robótica y Registro Nacional de Semilleros Científicos**
> Federación Venezolana de Robótica Creativa (FVRC)

---

## 📚 Índice

1. [Tecnologías Utilizadas](#-tecnologías-utilizadas)
2. [Requisitos del Sistema](#-requisitos-del-sistema)
3. [Configuración Inicial](#-configuración-inicial)
4. [Ejecución con Docker](#-ejecución-con-docker)
5. [Comandos de Django](#-comandos-de-django)
6. [Estructura del Proyecto](#-estructura-del-proyecto)
7. [Configuración de Cron](#-configuración-de-cron)
8. [Configuración de Nginx](#-configuración-de-nginx)
9. [Variables de Entorno](#-variables-de-entorno)
10. [Solución de Problemas](#-solución-de-problemas)

---

## 🛠 Tecnologías Utilizadas

### Backend
| Tecnología | Versión | Descripción |
|------------|---------|-------------|
| **Python** | 3.12 | Lenguaje de programación principal |
| **Django** | 5.2.6 | Framework web de alto nivel |
| **PostgreSQL** | 17 | Base de datos relacional |
| **Gunicorn** | 25.2.0 | Servidor WSGI HTTP |
| **psycopg2** | 2.9.11 | Adaptador PostgreSQL para Python |

### Frontend
| Tecnología | Versión | Descripción |
|------------|---------|-------------|
| **Bootstrap** | 5.3 | Framework CSS responsive |
| **HTML5/CSS3** | - | Estructura y estilos |
| **JavaScript** | ES6+ | Interactividad del lado del cliente |
| **Django Jazzmin** | 3.0.1 | Tema moderno para el admin de Django |
| **Crispy Forms** | 2.1 | Renderizado elegante de formularios |

### Infraestructura
| Tecnología | Versión | Descripción |
|------------|---------|-------------|
| **Docker** | 20+ | Containerización |
| **Docker Compose** | 2+ | Orquestación de contenedores |
| **Nginx** | Alpine | Servidor web proxy inverso |
| **WhiteNoise** | 6.11.0 | Servidor de archivos estáticos |

### Librerías Adicionales
- **Pillow 10.0.0** - Procesamiento de imágenes
- **openpyxl 3.1.2** - Manipulación de Excel
- **reportlab 4.0.4** - Generación de PDFs
- **pandas 2.3.3** - Análisis de datos
- **python-dotenv 1.2.1** - Variables de entorno
- **uuid6 2025.0.1** - Generación de UUIDs
- **nh3 0.3.4** - Sanitización HTML

---

## 💻 Requisitos del Sistema

### Mínimos
- 2 GB de RAM
- 10 GB de espacio en disco
- Docker Engine 20.10+
- Docker Compose 2.0+

### Recomendados
- 4 GB de RAM
- 20 GB de espacio en disco SSD
- Docker Engine 24.0+
- Sistema operativo: Linux Ubuntu 20.04+ / Windows 10/11 con WSL2

---

## 🔧 Configuración Inicial

### 1. Clonar o Extraer el Proyecto

```bash
# Si está en repositorio Git
git clone <url-del-repositorio>
cd SistemaRegistro
```

### 2. Configurar Variables de Entorno

Copiar el archivo de ejemplo y editar:

```bash
cp .env.example .env
```

Editar `.env` con tus configuraciones:

```bash
# Generar una SECRET_KEY segura
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Variables críticas a configurar:**

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta para Django | `django-insecure-...` (generar nueva) |
| `DEBUG` | Modo desarrollo | `True` (dev) / `False` (prod) |
| `ALLOWED_HOSTS` | Dominios permitidos | `localhost,127.0.0.1,tudominio.com` |
| `POSTGRES_DB` | Nombre de la base de datos | `robotica_db` |
| `POSTGRES_USER` | Usuario PostgreSQL | `admin` |
| `POSTGRES_PASSWORD` | Contraseña segura | `TuPasswordSeguro123!` |
| `DATABASE_URL` | URL de conexión | `postgres://user:pass@db:5432/robotica_db` |
| `BASE_URL` | URL base del sitio | `http://localhost:8000` |

### 3. Configuración de Email (Opcional)

Para desarrollo (Mailtrap):
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=tu_usuario_mailtrap
EMAIL_HOST_PASSWORD=tu_password_mailtrap
DEFAULT_FROM_EMAIL=web@fvrc.org.ve
```

---

## 🐳 Ejecución con Docker

### Modo Desarrollo (Recomendado)

#### Paso 1: Construir y Levantar Servicios

```bash
# Construir imágenes y levantar contenedores
docker compose up --build

# O en modo detached (background)
docker compose up --build -d
```

#### Paso 2: Acceder al Sistema

Abrir en el navegador:
- **Aplicación Django**: http://localhost:8000
- **Nginx (producción simulada)**: http://localhost
- **PostgreSQL**: localhost:5433

#### Comandos Docker Útiles

```bash
# Ver logs en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f web
docker compose logs -f db

# Detener servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ Borra datos)
docker compose down -v

# Reconstruir solo el servicio web
docker compose up --build web

# Ejecutar comando en contenedor
docker compose exec web python manage.py <comando>

# Entrar al contenedor web
docker compose exec web bash

# Entrar al contenedor de base de datos
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

### Servicios Docker

| Servicio | Descripción | Puerto Externo | Puerto Interno |
|----------|-------------|----------------|----------------|
| `db` | PostgreSQL 17 Alpine | 5433 | 5432 |
| `web` | Django + Gunicorn | 8000 | 8000 |
| `nginx` | Proxy inverso | 80 | 80 |

### Volúmenes Docker

| Volumen | Descripción | Ubicación |
|---------|-------------|-----------|
| `postgres_data` | Datos de PostgreSQL | `/var/lib/postgresql/data` |
| `static_volume` | Archivos estáticos recolectados | `/app/staticfiles` |
| `media_volume` | Archivos subidos por usuarios | `/app/media` |
| `./logs` | Logs de la aplicación | `/app/logs` |

---

## 🎯 Comandos de Django

### Acceder al Contenedor Web

Todos los comandos de Django deben ejecutarse dentro del contenedor:

```bash
docker compose exec web bash
```

### Migraciones de Base de Datos

```bash
# Crear migraciones (si hay cambios en modelos)
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Verificar estado de migraciones
python manage.py showmigrations

# Migrar aplicación específica
python manage.py migrate registry
```

### Crear Superusuario

El sistema tiene un comando personalizado que asigna automáticamente el tipo 'superusuario':

```bash
python manage.py createsuperuser
```

**Datos requeridos:**
- Nombre de usuario
- Correo electrónico
- Contraseña (mínimo 8 caracteres, debe incluir mayúsculas, minúsculas y símbolos)

**El sistema automáticamente:**
- Crea el usuario Django
- Crea el perfil asociado con `user_type='superusuario'`
- Asigna permisos de administrador

### Recolectar Archivos Estáticos

```bash
# Recolectar archivos estáticos (sin confirmación)
python manage.py collectstatic --noinput

# Con limpieza de archivos obsoletos
python manage.py collectstatic --noinput --clear
```

**Nota:** En Docker, los archivos estáticos se guardan en `/app/staticfiles` y son servidos por Nginx.

### Comandos Personalizados del Sistema

#### 1. Actualizar Estados de Eventos (Automatizado)

```bash
# Ejecutar actualización de estados
python manage.py actualizar_estados_eventos

# Modo simulación (ver cambios sin aplicar)
python manage.py actualizar_estados_eventos --dry-run

# Incluir eventos pausados vencidos
python manage.py actualizar_estados_eventos --incluir-pausados

# Modo verbose (muestra detalle de cada evento)
python manage.py actualizar_estados_eventos --verbose
```

**Transiciones de estado:**
- `abierto` → `en_proceso`: Cuando la fecha actual está entre fecha inicio y fin
- `abierto` → `finalizado`: Cuando la fecha fin ya pasó
- `en_proceso` → `finalizado`: Cuando la fecha fin ya pasó
- `pausado` → `finalizado`: Solo con flag `--incluir-pausados` y fecha vencida

#### 2. Crear Líneas de Investigación

```bash
python manage.py crear_lineas_investigacion
```

Carga las líneas de investigación predefinidas en el sistema.

#### 3. Limpiar Caché

```bash
python manage.py limpiar_cache
```

Limpia la caché de Django y notificaciones cacheadas.

#### 4. Cargar Datos de Ejemplo (Desarrollo)

```bash
python manage.py load_instituciones_ejemplo
```

Carga instituciones de ejemplo para pruebas.

### Comandos de Utilidad Django

```bash
# Shell de Django
python manage.py shell

# Shell con autoload de modelos
python manage.py shell_plus  # (requiere django-extensions)

# Verificar configuración
python manage.py check
python manage.py check --deploy  # Verificaciones de producción

# Crear respaldo de datos (JSON)
python manage.py dumpdata registry > backup_registry.json

# Cargar respaldo
python manage.py loaddata backup_registry.json

# Cambiar contraseña de usuario
python manage.py changepassword <username>

# Ejecutar tests
python manage.py test
python manage.py test registry.tests
```

---

## 📁 Estructura del Proyecto

```
SistemaRegistro/
├── .env                          # Variables de entorno (no versionar)
├── .env.example                  # Ejemplo de variables de entorno
├── .gitignore                    # Archivos ignorados por Git
├── docker-compose.yml            # Configuración de servicios Docker
├── docker-compose-prod.yml       # Configuración de producción
├── Dockerfile                    # Imagen Docker para desarrollo
├── Dockerfile-prod               # Imagen Docker para producción
├── nginx.conf                    # Configuración de Nginx
├── README.md                     # Documentación general
│
├── SistemaRegistro/              # Proyecto Django principal
│   ├── manage.py                 # Utilidad de comandos Django
│   ├── requirements.txt          # Dependencias Python
│   │
│   ├── SistemaRegistro/          # Configuración del proyecto
│   │   ├── __init__.py
│   │   ├── asgi.py              # Configuración ASGI
│   │   ├── settings.py          # Configuración principal
│   │   ├── urls.py              # Rutas principales
│   │   └── wsgi.py              # Configuración WSGI
│   │
│   ├── registry/                 # Aplicación principal del sistema
│   │   ├── __init__.py
│   │   ├── admin.py             # Configuración del admin
│   │   ├── admin_logs.py        # Logs del administrador
│   │   ├── apps.py              # Configuración de la app
│   │   ├── context_processors.py # Procesadores de contexto
│   │   ├── forms.py             # Formularios principales
│   │   ├── forms_grupos.py      # Formularios de grupos
│   │   ├── notificaciones.py    # Sistema de notificaciones
│   │   ├── signals.py            # Señales Django
│   │   ├── urls.py              # URLs de la app
│   │   ├── utils.py             # Funciones utilitarias
│   │   │
│   │   ├── management/          # Comandos personalizados
│   │   │   └── commands/
│   │   │       ├── __init__.py
│   │   │       ├── actualizar_estados_eventos.py
│   │   │       ├── crear_lineas_investigacion.py
│   │   │       ├── limpiar_cache.py
│   │   │       └── load_instituciones_ejemplo.py
│   │   │
│   │   ├── migrations/          # Migraciones de la base de datos
│   │   │
│   │   ├── models/              # Modelos del sistema
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Modelos base y mixins
│   │   │   ├── club.py          # Modelo de Clubes
│   │   │   ├── evento.py        # Modelo de Eventos
│   │   │   ├── grupo.py         # Modelo de Grupos/Equipos
│   │   │   ├── institucion.py   # Modelo de Instituciones
│   │   │   ├── participante.py  # Modelo de Participantes
│   │   │   ├── tutor.py         # Modelo de Tutores
│   │   │   ├── investigacion.py # Líneas de investigación
│   │   │   └── notificacion.py  # Modelo de Notificaciones
│   │   │
│   │   ├── policies/            # Políticas de negocio
│   │   │
│   │   ├── services/            # Servicios de negocio
│   │   │
│   │   ├── templates/           # Templates HTML
│   │   │   ├── admin/
│   │   │   ├── clubes/
│   │   │   ├── emails/
│   │   │   ├── eventos/
│   │   │   ├── grupos/
│   │   │   ├── instituciones/
│   │   │   ├── participantes/
│   │   │   ├── reportes/
│   │   │   └── tutores/
│   │   │
│   │   ├── tests/               # Tests unitarios y de integración
│   │   │
│   │   └── views*.py            # Vistas del sistema
│   │       ├── views.py
│   │       ├── views_admin_eventos.py
│   │       ├── views_avanzadas.py
│   │       ├── views_eventos.py
│   │       ├── views_grupos.py
│   │       ├── views_institucional.py
│   │       ├── views_reportes.py
│   │       └── views_tutores.py
│   │
│   ├── users/                    # Aplicación de usuarios
│   │   ├── models.py            # Modelos de usuarios y perfiles
│   │   ├── views.py             # Vistas de autenticación
│   │   ├── forms.py             # Formularios de usuarios
│   │   ├── middleware.py        # Middlewares de seguridad
│   │   ├── validators.py        # Validadores personalizados
│   │   └── services/            # Servicios de usuarios
│   │
│   ├── templates/               # Templates base compartidos
│   │   ├── base.html
│   │   ├── admin/
│   │   └── emails/
│   │
│   ├── static/                  # Archivos estáticos fuente
│   │   ├── admin/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── staticfiles/             # Archivos estáticos recolectados (generado)
│   ├── media/                   # Archivos subidos por usuarios
│   └── logs/                    # Logs de la aplicación
│
└── scripts/                     # Scripts de utilidad
    └── test_reactivacion_instituciones.py
```

---

## ⏰ Configuración de Cron

### Propósito

El comando `actualizar_estados_eventos` debe ejecutarse automáticamente cada día a la **1:00 AM** para actualizar los estados de los eventos según las fechas actuales.

### Configuración en Servidor Linux

#### Opción 1: Cron Job del Sistema (Recomendada)

1. Abrir el crontab del sistema:
```bash
sudo crontab -e
```

2. Agregar la siguiente línea:
```cron
# Actualizar estados de eventos a la 1:00 AM todos los días
0 1 * * * cd /ruta/al/proyecto && /usr/bin/docker compose exec -T web python manage.py actualizar_estados_eventos >> /var/log/rnr_cron.log 2>&1
```

3. Verificar que el cron está activo:
```bash
sudo systemctl status cron
```

#### Opción 2: Cron Job de Usuario

1. Abrir el crontab del usuario:
```bash
crontab -e
```

2. Agregar la línea:
```cron
0 1 * * * cd /ruta/al/proyecto/rnr && docker compose exec -T web python manage.py actualizar_estados_eventos >> ./logs/cron_eventos.log 2>&1
```

#### Opción 3: Usando Docker Cron (Contenedor Separado)

Crear un archivo `docker-compose.cron.yml`:

```yaml
version: '3.8'

services:
  cron:
    image: sistemaregistro-web:latest
    container_name: sistemaregistro_cron
    command: >
      sh -c "echo '0 1 * * * python /app/manage.py actualizar_estados_eventos' | crontab - && cron -f"
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=SistemaRegistro.settings
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
    volumes:
      - ./SistemaRegistro:/app
      - ./logs:/app/logs
    depends_on:
      - db
    networks:
      - backend_network
```

Ejecutar:
```bash
docker compose -f docker-compose.yml -f docker-compose.cron.yml up -d
```

### Verificación de Cron

1. Verificar logs del cron:
```bash
# Ver logs
tail -f /var/log/rnr_cron.log
# O si usas el log local
tail -f ./logs/cron_eventos.log
```

2. Ejecutar manualmente para probar:
```bash
docker compose exec web python manage.py actualizar_estados_eventos
```

3. Verificar que el evento está programado:
```bash
# Listar crontabs del usuario
crontab -l

# O ver el crontab del sistema
sudo cat /var/spool/cron/crontabs/root
```

### Formato de Log Recomendado

El comando incluye logging automático. Para logs rotativos, agregar a `settings.py`:

```python
LOGGING = {
    # ... configuración existente ...
    'handlers': {
        'cron_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / "logs" / "cron_eventos.log",
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'registry.management.commands.actualizar_estados_eventos': {
            'handlers': ['cron_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## 🌐 Configuración de Nginx

### Archivo de Configuración

La configuración se encuentra en `nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;

    # Archivos estáticos
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Archivos media
    location /media/ {
        alias /app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy inverso al contenedor web
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Personalización para Producción

Para producción, modificar `server_name`:

```nginx
server {
    listen 80;
    server_name fvrc.org.ve www.fvrc.org.ve;

    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name fvrc.org.ve www.fvrc.org.ve;

    # Configuración SSL
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # ... resto de configuración
}
```

---

## 🔐 Variables de Entorno

### Variables Obligatorias

| Variable | Descripción | Default | Obligatoria |
|----------|-------------|---------|-------------|
| `SECRET_KEY` | Clave secreta de Django | - | ✅ Sí |
| `DEBUG` | Modo debug | `False` | ✅ Sí |
| `DATABASE_URL` | URL de conexión a BD | - | ✅ Sí (en producción) |
| `ALLOWED_HOSTS` | Hosts permitidos | - | ✅ Sí (en producción) |

### Variables de Base de Datos

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `POSTGRES_DB` | Nombre de la BD | `robotica_db` |
| `POSTGRES_USER` | Usuario PostgreSQL | `admin` |
| `POSTGRES_PASSWORD` | Contraseña | `secure_password` |
| `DATABASE_URL` | URL completa | `postgres://admin:pass@db:5432/robotica_db` |

### Variables de Email

| Variable | Descripción | Default |
|----------|-------------|---------|
| `EMAIL_BACKEND` | Backend de email | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | Servidor SMTP | `sandbox.smtp.mailtrap.io` |
| `EMAIL_PORT` | Puerto SMTP | `2525` |
| `EMAIL_HOST_USER` | Usuario SMTP | - |
| `EMAIL_HOST_PASSWORD` | Contraseña SMTP | - |
| `DEFAULT_FROM_EMAIL` | Remitente por defecto | `registro@fvrc.org.ve` |

### Variables de Seguridad (Producción)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables | `https://fvrc.org.ve` |
| `SECURE_SSL_REDIRECT` | Redirigir a HTTPS | `True` |
| `SECURE_HSTS_SECONDS` | Segundos HSTS | `31536000` |

---

## 🐛 Solución de Problemas

### Problemas Comunes

#### 1. Error de Conexión a PostgreSQL

**Síntoma:** `could not connect to server: Connection refused`

**Solución:**
```bash
# Verificar que el contenedor de DB está corriendo
docker compose ps

# Verificar logs del DB
docker compose logs db

# Reiniciar el servicio
docker compose restart db
```

#### 2. Archivos Estáticos No Cargan (404)

**Síntoma:** CSS/JS no se aplican, Nginx devuelve 404

**Solución:**
```bash
# Entrar al contenedor y recolectar estáticos
docker compose exec web bash
python manage.py collectstatic --noinput --clear

# Verificar permisos
docker compose exec web ls -la /app/staticfiles/
```

#### 3. Error de Permisos en Volúmenes

**Síntoma:** `Permission denied` al escribir archivos

**Solución:**
```bash
# En Linux/Mac, cambiar propietario
sudo chown -R $USER:$USER ./SistemaRegistro/logs
sudo chown -R $USER:$USER ./SistemaRegistro/media
```

#### 4. Puerto 8000 o 80 Ya en Uso

**Síntoma:** `bind: address already in use`

**Solución:**
```bash
# Encontrar proceso usando el puerto
# Windows (PowerShell Admin)
netstat -ano | findstr :8000
netstat -ano | findstr :80

# Linux/Mac
lsof -i :8000
lsof -i :80

# Cambiar puertos en docker-compose.yml
# ports:
#   - "8001:8000"  # Puerto externo 8001
```

#### 5. Migraciones Pendientes

**Síntoma:** `You have unapplied migrations`

**Solución:**
```bash
docker compose exec web python manage.py migrate
```

#### 6. Error de SECRET_KEY

**Síntoma:** `ValueError: SECRET_KEY must not be empty`

**Solución:**
```bash
# Generar nueva SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copiar y pegar en .env
```

### Comandos de Diagnóstico

```bash
# Ver estado de todos los contenedores
docker compose ps

# Ver uso de recursos
docker stats

# Inspeccionar red
docker network ls
docker network inspect sistemaregistro_backend_network

# Ver volúmenes
docker volume ls

# Ver logs completos
docker compose logs --tail=500
```

### Contacto y Soporte

- **Proyecto:** Registro Nacional de Robótica (RNR-PRO)
- **Institución:** Federación Venezolana de Robótica Creativa (FVRC)
- **Supervisión:** MINCYT (Ministerio del Poder Popular para la Ciencia y Tecnología)

---

## 📄 Licencia

Proyecto institucional supervisado por el MINCYT - Venezuela.

---

*Documento generado el: Abril 2026*
*Versión del Sistema: 2.0*
