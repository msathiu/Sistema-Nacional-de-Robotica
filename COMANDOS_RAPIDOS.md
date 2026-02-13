# ⚡ COMANDOS RÁPIDOS

## Aplicar Cambios

```bash
# Navegar al directorio del proyecto
cd SistemaRegistro

# Aplicar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

---

## Crear Superusuario

```bash
# Crear superusuario con tipo automático
python manage.py createsuperuser

# Ejemplo de datos:
# Username: admin
# Email: admin@snr.gob.ve
# Password: (tu contraseña segura)
```

---

## Iniciar Servidor

```bash
# Modo desarrollo
python manage.py runserver

# Acceder a:
# - Frontend: http://localhost:8000/
# - Admin: http://localhost:8000/admin/
```

---

## Probar APIs (en navegador o Postman)

```bash
# Municipios de un estado (requiere login)
http://localhost:8000/api/municipios/1/

# Parroquias de un municipio (requiere login)
http://localhost:8000/api/parroquias/1/
```

---

## Verificar Implementación

```bash
# Windows
verificar_implementacion.bat

# Linux/Mac
bash verificar_implementacion.sh
```

---

## Ver Logs

```bash
# Windows
type logs\django.log

# Linux/Mac
tail -f logs/django.log
```

---

## Comandos de Django Útiles

```bash
# Ver todas las rutas
python manage.py show_urls

# Ver rutas de API
python manage.py show_urls | findstr api

# Crear migraciones
python manage.py makemigrations

# Shell interactivo
python manage.py shell

# Verificar configuración
python manage.py check
```

---

## Probar en Python Shell

```python
# Abrir shell
python manage.py shell

# Probar creación de perfil
from django.contrib.auth.models import User
from users.models import UserProfile

# Verificar superusuarios
for user in User.objects.filter(is_superuser=True):
    profile = user.userprofile
    print(f"{user.username}: {profile.user_type}")

# Probar filtrado de ubicaciones
from registry.models import Estado, Municipio, Parroquia

# Ver estados
Estado.objects.all()

# Ver municipios de un estado
estado = Estado.objects.first()
Municipio.objects.filter(estado=estado)

# Ver parroquias de un municipio
municipio = Municipio.objects.first()
Parroquia.objects.filter(municipio=municipio)
```

---

## Limpiar y Reiniciar

```bash
# Limpiar archivos estáticos
python manage.py collectstatic --clear --noinput

# Recrear base de datos (¡CUIDADO! Borra todos los datos)
# Solo en desarrollo
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## Docker (si aplica)

```bash
# Construir y levantar
docker compose up --build

# Solo levantar
docker compose up

# Detener
docker compose down

# Ver logs
docker compose logs -f
```

---

## Git (Control de Versiones)

```bash
# Ver cambios
git status

# Agregar archivos nuevos
git add .

# Commit
git commit -m "Implementado sistema de ubicación en cascada y comando createsuperuser"

# Push
git push origin main
```

---

## Troubleshooting Rápido

```bash
# Si hay error de migraciones
python manage.py migrate --run-syncdb

# Si hay error de permisos en archivos estáticos
python manage.py collectstatic --clear --noinput

# Si el comando createsuperuser no se reconoce
python manage.py help createsuperuser

# Verificar que Django reconoce el comando
python manage.py help | findstr createsuperuser
```

---

## URLs Importantes

```
Admin Panel:
http://localhost:8000/admin/

User Profiles:
http://localhost:8000/admin/users/userprofile/

API Municipios:
http://localhost:8000/api/municipios/1/

API Parroquias:
http://localhost:8000/api/parroquias/1/

Home:
http://localhost:8000/
```

---

## Atajos de Teclado en Admin

```
Ctrl + S          - Guardar
Ctrl + Shift + S  - Guardar y continuar editando
F12               - Abrir consola del navegador
Ctrl + Shift + I  - Inspeccionar elemento
```

---

## Copiar y Pegar - Setup Completo

```bash
# Setup completo en un solo bloque
cd SistemaRegistro
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py runserver
```

Luego abrir: http://localhost:8000/admin/

---

**Tip**: Guarda este archivo en tus marcadores para acceso rápido a los comandos.
