# 🚀 IMPLEMENTACIÓN DEL SISTEMA INSTITUCIONAL DE GESTIÓN

## 📋 Resumen de Cambios

Se ha implementado el flujo completo de gestión institucional según el diseño UX proporcionado, incluyendo:

- ✅ Gestión de Grupos (Crear, Editar, Ver, Eliminar)
- ✅ Inscripción de Grupos a Eventos
- ✅ Gestión de Clubes y Membresías
- ✅ Estados dinámicos (Editable → Inscrito → Bloqueado)
- ✅ Dashboard institucional mejorado
- ✅ Validaciones UX completas

---

## 🗂️ Archivos Creados/Modificados

### Modelos Actualizados
- `registry/models.py` - Agregados campos y modelos nuevos:
  - **Evento**: `tipo`, `modalidad`, `ubicacion`, `estado_evento`
  - **Grupo**: `codigo`, `criterio`, `estado_grupo`, `tutor_apellidos`
  - **Club**: `logo`, `siglas`, `fecha_fundacion`, `institucion_creadora`, `estado_vinculacion`, `cupo_maximo`, `requisitos`
  - **Nuevos modelos**: `MembresiaClu`, `InscripcionGrupoEvento`

### Vistas Nuevas
- `registry/views_institucional.py` - Todas las vistas del módulo institucional

### Templates Creados
- `templates/users/dashboard_institucional_new.html` - Dashboard mejorado
- `registry/templates/registry/grupos_lista.html` - Lista de grupos
- `registry/templates/registry/grupo_crear.html` - Crear/editar grupo
- `registry/templates/registry/eventos_disponibles.html` - Eventos disponibles
- `registry/templates/registry/inscribir_grupo.html` - Inscribir grupo a evento
- `registry/templates/registry/clubes_lista.html` - Lista de clubes

### URLs Actualizadas
- `registry/urls.py` - Agregadas rutas para grupos, eventos y clubes

### Migraciones
- `registry/migrations/0011_sistema_institucional.py` - Migración con todos los cambios

---

## 🔧 PASOS PARA IMPLEMENTAR

### 1️⃣ Aplicar Migraciones

```bash
cd SistemaRegistro
python manage.py makemigrations
python manage.py migrate
```

**Nota**: Si hay conflictos con migraciones existentes, puede ser necesario ajustar el número de la migración.

### 2️⃣ Actualizar el Admin (Opcional)

Agregar los nuevos modelos al admin en `registry/admin.py`:

```python
from .models import MembresiaClu, InscripcionGrupoEvento

@admin.register(MembresiaClu)
class MembresiaCluAdmin(admin.ModelAdmin):
    list_display = ['club', 'institucion', 'estado', 'fecha_solicitud']
    list_filter = ['estado', 'fecha_solicitud']
    search_fields = ['club__nombre', 'institucion__nombre']

@admin.register(InscripcionGrupoEvento)
class InscripcionGrupoEventoAdmin(admin.ModelAdmin):
    list_display = ['grupo', 'evento', 'rol_participacion', 'fecha_inscripcion']
    list_filter = ['rol_participacion', 'fecha_inscripcion']
    search_fields = ['grupo__nombre', 'evento__nombre']
```

### 3️⃣ Actualizar el Dashboard Institucional

Reemplazar el contenido de `templates/users/dashboard_institucional.html` con el contenido de `dashboard_institucional_new.html`, o simplemente renombrar:

```bash
# Backup del original
mv templates/users/dashboard_institucional.html templates/users/dashboard_institucional_old.html

# Usar el nuevo
mv templates/users/dashboard_institucional_new.html templates/users/dashboard_institucional.html
```

### 4️⃣ Actualizar el Menú de Navegación

En `templates/users/base_dashboard.html`, agregar los enlaces al menú lateral:

```html
<!-- Sección para Usuarios Institucionales -->
{% if user.userprofile.user_type == 'institucional' %}
<li class="nav-item">
    <a class="nav-link" href="{% url 'grupos_institucion' %}">
        <i class="fas fa-users"></i> Mis Grupos
    </a>
</li>
<li class="nav-item">
    <a class="nav-link" href="{% url 'eventos_disponibles_institucion' %}">
        <i class="fas fa-calendar-alt"></i> Eventos
    </a>
</li>
<li class="nav-item">
    <a class="nav-link" href="{% url 'clubes_lista' %}">
        <i class="fas fa-trophy"></i> Clubes
    </a>
</li>
{% endif %}
```

### 5️⃣ Instalar Pillow (para imágenes de clubes)

```bash
pip install Pillow
```

Agregar a `requirements.txt`:
```
Pillow>=10.0.0
```

### 6️⃣ Configurar Media Files

En `settings.py`, asegurarse de tener:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

En `urls.py` principal:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... tus urls
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 🎯 FLUJO DE USUARIO IMPLEMENTADO

### 1. Login Institucional
- Usuario ingresa con código RNR y contraseña
- Redirige a Dashboard Institucional

### 2. Dashboard
- Muestra KPIs: Total Grupos, Participantes, Eventos
- Lista próximos eventos
- Lista grupos recientes
- Acciones rápidas

### 3. Gestión de Grupos

#### Crear Grupo
1. Click en "Crear Grupo"
2. Llenar datos del grupo (nombre, criterio)
3. Agregar datos del tutor
4. Agregar participantes dinámicamente
5. Buscar participantes existentes por cédula
6. Guardar → Estado: **Editable**

#### Editar Grupo
- Solo disponible si estado = **Editable**
- Modificar datos y participantes

#### Ver Grupo
- Ver detalles completos
- Ver inscripciones a eventos

#### Eliminar Grupo
- Solo disponible si estado = **Editable**

### 4. Inscripción a Eventos

#### Ver Eventos Disponibles
- Lista de eventos con filtros
- Estados visuales por color
- Solo eventos "Abiertos" permiten inscripción

#### Inscribir Grupo
1. Seleccionar evento
2. Elegir grupo (solo **Editables**)
3. Seleccionar rol de participación
4. Confirmar
5. Grupo cambia a estado **Inscrito**

#### Cuando Evento Finaliza
- Automático: Grupo → **Bloqueado**
- No se puede editar ni eliminar

### 5. Gestión de Clubes

#### Crear Club
- Datos básicos (nombre, siglas, logo)
- Hasta 3 líneas de investigación
- Configurar vinculación (abierto/cerrado/invitación)
- Definir cupo máximo

#### Postular a Club
- Ver directorio de clubes
- Filtrar por línea de investigación
- Enviar solicitud con:
  - Carta de intención
  - Propuesta técnica
  - Representante legal
- Estados: Pendiente → En Revisión → Aprobada/Rechazada

---

## 🎨 ESTADOS VISUALES IMPLEMENTADOS

### Grupos
- 🟢 **Editable** (gris) - Se puede editar/eliminar
- 🔵 **Inscrito** (azul) - Inscrito en evento activo
- 🔴 **Bloqueado** (rojo) - Evento finalizado, solo lectura

### Eventos
- 🟢 **Abierto** (verde) - Acepta inscripciones
- 🟡 **Pausado** (amarillo) - Temporalmente cerrado
- 🔴 **Cerrado** (rojo) - No acepta inscripciones
- ⚫ **Finalizado** (gris) - Evento terminado

### Clubes
- 🟢 **Abierto** (verde) - Acepta postulaciones
- 🔴 **Cerrado** (rojo) - No acepta postulaciones
- 🟡 **Bajo Invitación** (amarillo) - Solo por invitación

### Membresías
- 🟡 **Pendiente** (amarillo)
- 🔵 **En Revisión** (azul)
- 🟢 **Aprobada** (verde)
- 🔴 **Rechazada** (rojo)

---

## 🔐 VALIDACIONES IMPLEMENTADAS

### Grupos
- ✅ No se puede editar grupo inscrito o bloqueado
- ✅ No se puede eliminar grupo inscrito o bloqueado
- ✅ Código único autogenerado (GRP-XXXXXXXX)
- ✅ Búsqueda de participantes existentes por cédula

### Eventos
- ✅ Solo grupos editables pueden inscribirse
- ✅ No se puede inscribir el mismo grupo dos veces
- ✅ Al inscribir, grupo cambia a estado "inscrito"
- ✅ Solo eventos "abiertos" permiten inscripción

### Clubes
- ✅ Máximo 3 líneas de investigación
- ✅ Control de cupos disponibles
- ✅ No se puede postular dos veces al mismo club
- ✅ Validación de estado de vinculación

---

## 📊 DATOS DE PRUEBA SUGERIDOS

### Crear Eventos de Prueba

```python
# En Django shell
python manage.py shell

from registry.models import Evento, Institucion
from datetime import date, timedelta

inst = Institucion.objects.first()

Evento.objects.create(
    nombre="Competencia Nacional de Robótica 2025",
    tipo="competencia",
    fecha=date.today() + timedelta(days=30),
    modalidad="presencial",
    ubicacion="Caracas, Venezuela",
    estado_evento="abierto",
    institucion=inst,
    descripcion="Competencia nacional de robótica educativa"
)
```

### Crear Clubes de Prueba

```python
from registry.models import Club

Club.objects.create(
    nombre="Club de Robótica Avanzada",
    siglas="CRA",
    descripcion="Club dedicado a la investigación en robótica avanzada",
    ubicacion="Caracas",
    linea_1="ia",
    linea_2="programacion",
    estado_vinculacion="abierto",
    cupo_maximo=15,
    institucion_creadora=inst
)
```

---

## 🐛 TROUBLESHOOTING

### Error: "No module named 'PIL'"
```bash
pip install Pillow
```

### Error: "relation does not exist"
```bash
python manage.py migrate --run-syncdb
```

### Error: "Duplicate column name"
- La migración ya fue aplicada parcialmente
- Revisar con: `python manage.py showmigrations`
- Hacer rollback si es necesario

### Grupos no aparecen en el dropdown
- Verificar que el usuario tenga grupos en estado "editable"
- Verificar que el usuario sea el creador del grupo

---

## 📝 PRÓXIMOS PASOS RECOMENDADOS

1. **Notificaciones**: Agregar sistema de notificaciones cuando:
   - Un grupo es inscrito a un evento
   - Un evento cambia de estado
   - Una membresía es aprobada/rechazada

2. **Reportes**: Generar reportes PDF de:
   - Grupos inscritos por evento
   - Certificados de participación
   - Estadísticas de clubes

3. **Permisos**: Implementar permisos granulares para:
   - Gestión de eventos (solo admin)
   - Aprobación de membresías (creador del club)

4. **API REST**: Exponer endpoints para:
   - Consulta de eventos disponibles
   - Estado de inscripciones
   - Directorio de clubes

---

## 📞 SOPORTE

Para dudas o problemas con la implementación, revisar:
- Logs del sistema: `logs/django.log`
- Consola del navegador (F12) para errores JavaScript
- Django Debug Toolbar para queries lentas

---

**Fecha de Implementación**: Febrero 2025
**Versión**: 1.0.0
**Autor**: Amazon Q Developer
