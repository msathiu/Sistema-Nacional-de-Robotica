# Instrucciones para Configurar Roles de Usuario

## 🚀 Pasos para aplicar las mejoras

### 1️⃣ Aplicar migraciones
```bash
docker compose exec web python manage.py migrate
```

### 2️⃣ Actualizar perfiles de superusuarios existentes
```bash
docker compose exec web python manage.py actualizar_superusuarios
```

### 3️⃣ Crear un nuevo superusuario (si no existe)
```bash
docker compose exec web python manage.py createsuperuser
```

## 📋 Tipos de Usuario Disponibles

El sistema ahora maneja **4 roles de usuario**:

1. **Superusuario** (`superuser`)
   - Acceso completo al admin de Django
   - Al hacer login normal, se redirige automáticamente a `/admin/`
   - Gestión total del sistema

2. **Administrador (Ministerio)** (`admin`)
   - Dashboard administrativo con estadísticas completas
   - Gestión de instituciones y participantes
   - Acceso a reportes y logs del sistema

3. **Usuario Institucional** (`institucional`)
   - Dashboard institucional
   - Gestión de grupos y participantes de su institución
   - Inscripción a eventos

4. **Participante** (`participante`)
   - Dashboard de participante
   - Visualización de eventos disponibles
   - Gestión de su perfil

## 🔐 Comportamiento del Login

- **Superusuarios**: Redirigidos a `/admin/` (Admin de Django)
- **Otros usuarios**: Redirigidos a `/dashboard/` (Router que los envía a su dashboard específico)

## 👁️ Visualización en Admin de Django

En el panel de administración de Django (`/admin/`) ahora puedes ver:

- **Columna "Tipo de Usuario"**: Muestra el rol de cada usuario
- **Columna "Código RNR"**: Muestra el código de la institución (si aplica)
- **Filtros**: Por tipo de usuario, staff, superusuario, activo
- **Modelo UserProfile**: Gestión completa de perfiles de usuario

## 🧪 Verificar el Sistema

```bash
# Ver usuarios y sus tipos
docker compose exec web python manage.py shell
>>> from django.contrib.auth.models import User
>>> from users.models import UserProfile
>>> for u in User.objects.all():
...     print(f"{u.username}: {u.userprofile.get_user_type_display()}")
```

## 📝 Notas Importantes

- Los superusuarios creados con `createsuperuser` automáticamente reciben el tipo `superuser`
- Los usuarios existentes pueden actualizarse con el comando `actualizar_superusuarios`
- El admin de Django muestra todos los tipos de usuario en una columna dedicada
- Cada tipo de usuario tiene su propia vista/dashboard personalizado
