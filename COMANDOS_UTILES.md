# 🛠️ Comandos Útiles - Sistema Nacional de Robótica

## 📋 Índice

1. [Configuración Inicial](#configuración-inicial)
2. [Base de Datos](#base-de-datos)
3. [Desarrollo](#desarrollo)
4. [Testing](#testing)
5. [Producción](#producción)
6. [Mantenimiento](#mantenimiento)
7. [Docker](#docker)

---

## 🚀 Configuración Inicial

### Crear Entorno Virtual

```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

### Instalar Dependencias

```bash
cd SistemaRegistro
pip install -r requirements.txt
```

### Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Generar SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Editar .env con tu editor favorito
nano .env  # o code .env
```

---

## 💾 Base de Datos

### Migraciones

```bash
# Crear migraciones
python manage.py makemigrations

# Ver SQL de las migraciones
python manage.py sqlmigrate registry 0001

# Aplicar migraciones
python manage.py migrate

# Revertir migraciones
python manage.py migrate registry 0001  # Volver a migración específica
python manage.py migrate registry zero  # Revertir todas

# Ver estado de migraciones
python manage.py showmigrations
```

### Datos Iniciales

```bash
# Cargar datos de ejemplo
python manage.py loaddata fixtures/estados.json

# Crear superusuario
python manage.py createsuperuser

# Ejecutar comando personalizado
python manage.py load_instituciones_ejemplo
```

### Backup y Restore

```bash
# Backup de base de datos SQLite
cp db.sqlite3 db.sqlite3.backup

# Backup de PostgreSQL
pg_dump -U usuario -d nombre_bd > backup.sql

# Restore de PostgreSQL
psql -U usuario -d nombre_bd < backup.sql

# Exportar datos a JSON
python manage.py dumpdata registry.Institucion --indent 2 > instituciones.json

# Importar datos desde JSON
python manage.py loaddata instituciones.json
```

---

## 💻 Desarrollo

### Servidor de Desarrollo

```bash
# Iniciar servidor
python manage.py runserver

# Iniciar en puerto específico
python manage.py runserver 8080

# Iniciar en todas las interfaces
python manage.py runserver 0.0.0.0:8000
```

### Shell Interactivo

```bash
# Shell de Django
python manage.py shell

# Shell con IPython (si está instalado)
python manage.py shell -i ipython

# Shell Plus (django-extensions)
python manage.py shell_plus
```

### Ejemplos de Shell

```python
# En el shell de Django
from registry.models import Institucion, Participante
from django.contrib.auth.models import User

# Crear institución
institucion = Institucion.objects.create(
    nombre="Escuela Ejemplo",
    email="ejemplo@escuela.com",
    # ... más campos
)

# Consultar participantes
participantes = Participante.objects.filter(activo=True)

# Contar registros
total = Institucion.objects.count()

# Filtros complejos
from django.db.models import Q
instituciones = Institucion.objects.filter(
    Q(tipo_institucion='educativa') | Q(federado=True)
)
```

### Archivos Estáticos

```bash
# Recolectar archivos estáticos
python manage.py collectstatic

# Recolectar sin confirmación
python manage.py collectstatic --noinput

# Limpiar archivos estáticos antiguos
python manage.py collectstatic --clear --noinput
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests de una app específica
python manage.py test registry

# Tests de un módulo específico
python manage.py test registry.tests.test_models

# Test específico
python manage.py test registry.tests.test_models.ParticipanteModelTest.test_edad

# Con verbosidad
python manage.py test --verbosity=2

# Mantener base de datos de test
python manage.py test --keepdb

# Tests en paralelo
python manage.py test --parallel
```

### Coverage

```bash
# Instalar coverage
pip install coverage

# Ejecutar tests con coverage
coverage run --source='.' manage.py test

# Ver reporte en terminal
coverage report

# Generar reporte HTML
coverage html
# Abrir htmlcov/index.html en navegador
```

---

## 🚀 Producción

### Verificaciones Pre-Despliegue

```bash
# Verificar configuración de producción
python manage.py check --deploy

# Verificar migraciones pendientes
python manage.py showmigrations | grep "\[ \]"

# Verificar archivos estáticos
python manage.py collectstatic --dry-run
```

### Optimización

```bash
# Compilar mensajes de traducción
python manage.py compilemessages

# Limpiar sesiones expiradas
python manage.py clearsessions

# Limpiar caché
python manage.py clear_cache  # Si tienes este comando personalizado
```

### Gunicorn (Servidor WSGI)

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar con gunicorn
gunicorn SistemaRegistro.wsgi:application --bind 0.0.0.0:8000

# Con workers
gunicorn SistemaRegistro.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120

# Con archivo de configuración
gunicorn -c gunicorn_config.py SistemaRegistro.wsgi:application
```

---

## 🔧 Mantenimiento

### Logs

```bash
# Ver logs en tiempo real
tail -f SistemaRegistro/logs/django.log

# Ver últimas 100 líneas
tail -n 100 SistemaRegistro/logs/django.log

# Buscar errores
grep "ERROR" SistemaRegistro/logs/django.log

# Limpiar logs antiguos
find SistemaRegistro/logs -name "*.log.*" -mtime +30 -delete
```

### Base de Datos

```bash
# Optimizar base de datos SQLite
python manage.py dbshell
# En el shell de SQLite:
# VACUUM;
# ANALYZE;

# Ver tamaño de base de datos
du -h db.sqlite3

# Verificar integridad
python manage.py check
```

### Usuarios

```bash
# Cambiar contraseña de usuario
python manage.py changepassword username

# Crear superusuario sin interacción
python manage.py createsuperuser --noinput \
    --username admin \
    --email admin@example.com

# Listar usuarios
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.all())"
```

---

## 🐳 Docker

### Construcción y Ejecución

```bash
# Construir imagen
docker build -t snr-robotica .

# Ejecutar contenedor
docker run -p 8000:8000 snr-robotica

# Con docker-compose
docker-compose up

# En segundo plano
docker-compose up -d

# Reconstruir
docker-compose up --build

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

### Comandos en Contenedor

```bash
# Ejecutar comando en contenedor
docker-compose exec web python manage.py migrate

# Shell en contenedor
docker-compose exec web bash

# Shell de Django en contenedor
docker-compose exec web python manage.py shell

# Ver logs de un servicio
docker-compose logs -f web
```

### Limpieza Docker

```bash
# Eliminar contenedores detenidos
docker container prune

# Eliminar imágenes sin usar
docker image prune

# Eliminar volúmenes sin usar
docker volume prune

# Limpieza completa
docker system prune -a
```

---

## 📊 Utilidades Adicionales

### Django Extensions

```bash
# Instalar django-extensions
pip install django-extensions

# Generar diagrama de modelos
python manage.py graph_models -a -o models.png

# Mostrar URLs
python manage.py show_urls

# Validar templates
python manage.py validate_templates

# Limpiar archivos .pyc
python manage.py clean_pyc
```

### Debugging

```bash
# Ejecutar con debugger
python -m pdb manage.py runserver

# Ver queries SQL
python manage.py shell
>>> from django.db import connection
>>> connection.queries

# Modo debug con django-debug-toolbar
# Agregar a INSTALLED_APPS y MIDDLEWARE
```

### Performance

```bash
# Analizar queries lentas
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import override_settings
>>> with override_settings(DEBUG=True):
...     # Tu código aquí
...     print(connection.queries)

# Profile de código
python -m cProfile manage.py runserver
```

---

## 🔍 Búsqueda y Análisis

### Buscar en Código

```bash
# Buscar texto en archivos Python
grep -r "texto_a_buscar" --include="*.py"

# Buscar en templates
grep -r "texto_a_buscar" --include="*.html"

# Buscar definiciones de modelos
grep -r "class.*models.Model" --include="*.py"

# Contar líneas de código
find . -name "*.py" | xargs wc -l
```

### Git

```bash
# Ver cambios
git status
git diff

# Commit
git add .
git commit -m "feat: descripción del cambio"

# Push
git push origin main

# Ver historial
git log --oneline --graph

# Crear branch
git checkout -b feature/nueva-funcionalidad

# Merge
git checkout main
git merge feature/nueva-funcionalidad
```

---

## 📚 Recursos

- [Documentación Django](https://docs.djangoproject.com/)
- [Django Management Commands](https://docs.djangoproject.com/en/stable/ref/django-admin/)
- [Docker Documentation](https://docs.docker.com/)

---

**Última actualización:** Febrero 2026  
**Mantenido por:** Equipo de Desarrollo SNR
