# 📋 PLAN DE TAREAS: Mejora del Sistema de Clubes

## 🎯 Objetivo General
Implementar un sistema robusto de gestión de clubes con flujo de aprobación y visualización correcta según permisos.

---

## 📊 FASE 1: Corrección de Lógica de Negocio

### ✅ Tarea 1.1: Actualizar Vista `clubes_lista`
**Archivo:** `SistemaRegistro/registry/views_institucional.py`  
**Línea:** 237  
**Prioridad:** 🔴 CRÍTICA

**Problema:**
- Actualmente muestra TODOS los clubes sin diferenciar estados
- No separa "Mis Clubes Creados" de "Clubes Aprobados"

**Solución:**
```python
@login_required
def clubes_lista(request):
    """Lista de clubes - Diferenciando creados, aprobados y disponibles."""
    if (
        not hasattr(request.user, "userprofile")
        or request.user.userprofile.user_type != "institucional"
    ):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")

    institucion = request.user.userprofile.institution

    # 1. MIS CLUBES CREADOS (todos los estados para gestión interna)
    mis_clubes_creados = Club.objects.filter(
        institucion_creadora=institucion
    ).order_by("-fecha_creacion")

    # 2. MIS CLUBES APROBADOS (solo los aprobados de mi institución)
    mis_clubes_aprobados = mis_clubes_creados.filter(
        status="aprobado",
        activo=True
    )

    # 3. CLUBES DISPONIBLES (aprobados de OTRAS instituciones para postular)
    clubes_disponibles = (
        Club.objects.filter(
            activo=True,
            status="aprobado",
            estado_vinculacion__in=["abierto", "invitacion"],
        )
        .exclude(institucion_creadora=institucion)
        .annotate(
            num_membresias=Count("membresias", filter=Q(membresias__estado="aprobada"))
        )
    )

    # Filtrar los que tienen cupos disponibles
    clubes_disponibles = [c for c in clubes_disponibles if c.cupos_disponibles > 0]

    context = {
        "mis_clubes_creados": mis_clubes_creados,
        "mis_clubes_aprobados": mis_clubes_aprobados,
        "clubes_disponibles": clubes_disponibles,
        "total_creados": mis_clubes_creados.count(),
        "total_aprobados": mis_clubes_aprobados.count(),
        "total_disponibles": len(clubes_disponibles),
    }
    return render(request, "registry/clubes_lista.html", context)
```

**Validación:**
- [ ] La vista compila sin errores
- [ ] Se muestran 3 secciones diferenciadas
- [ ] Los clubes en borrador solo aparecen en "Mis Clubes Creados"
- [ ] Los clubes aprobados aparecen en ambas secciones
- [ ] Los clubes de otras instituciones solo aparecen en "Disponibles"

---

### ✅ Tarea 1.2: Actualizar Template `clubes_lista.html`
**Archivo:** `SistemaRegistro/registry/templates/registry/clubes_lista.html`  
**Prioridad:** 🔴 CRÍTICA

**Cambios Requeridos:**

1. **Agregar 3 Secciones Diferenciadas:**

```html
{% extends "users/base_dashboard.html" %}
{% load static %}

{% block content %}
<div class="container-fluid py-4">
    <h2 class="mb-4">
        <i class="bi bi-people-fill"></i> Gestión de Clubes
    </h2>

    <!-- SECCIÓN 1: MIS CLUBES CREADOS -->
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">
                <i class="bi bi-folder"></i> Mis Clubes Creados
                <span class="badge bg-light text-dark">{{ total_creados }}</span>
            </h5>
        </div>
        <div class="card-body">
            {% if mis_clubes_creados %}
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Estado</th>
                                <th>Fecha Creación</th>
                                <th>Cupos</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for club in mis_clubes_creados %}
                            <tr>
                                <td>
                                    <strong>{{ club.nombre }}</strong>
                                    {% if club.siglas %}
                                        <small class="text-muted">({{ club.siglas }})</small>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if club.status == 'borrador' %}
                                        <span class="badge bg-secondary">Borrador</span>
                                    {% elif club.status == 'pendiente' %}
                                        <span class="badge bg-warning text-dark">Pendiente</span>
                                    {% elif club.status == 'en_revision' %}
                                        <span class="badge bg-info">En Revisión</span>
                                    {% elif club.status == 'aprobado' %}
                                        <span class="badge bg-success">Aprobado</span>
                                    {% elif club.status == 'rechazado' %}
                                        <span class="badge bg-danger">Rechazado</span>
                                    {% endif %}
                                </td>
                                <td>{{ club.fecha_creacion|date:"d/m/Y" }}</td>
                                <td>
                                    <span class="badge bg-info">
                                        {{ club.cupos_disponibles }}/{{ club.cupo_maximo }}
                                    </span>
                                </td>
                                <td>
                                    {% if club.status == 'borrador' %}
                                        <a href="{% url 'editar_club' club.id %}" 
                                           class="btn btn-sm btn-primary">
                                            <i class="bi bi-pencil"></i> Editar
                                        </a>
                                        <a href="{% url 'enviar_club_revision' club.id %}" 
                                           class="btn btn-sm btn-success">
                                            <i class="bi bi-send"></i> Enviar a Revisión
                                        </a>
                                    {% elif club.status == 'rechazado' %}
                                        <a href="{% url 'editar_club' club.id %}" 
                                           class="btn btn-sm btn-warning">
                                            <i class="bi bi-arrow-repeat"></i> Corregir
                                        </a>
                                    {% elif club.status == 'pendiente' or club.status == 'en_revision' %}
                                        <span class="text-muted">En proceso...</span>
                                    {% elif club.status == 'aprobado' %}
                                        <span class="badge bg-success">
                                            <i class="bi bi-check-circle"></i> Activo
                                        </span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> 
                    No has creado ningún club aún.
                    <a href="{% url 'crear_club' %}" class="alert-link">Crear mi primer club</a>
                </div>
            {% endif %}
        </div>
    </div>

    <!-- SECCIÓN 2: MIS CLUBES APROBADOS -->
    <div class="card mb-4">
        <div class="card-header bg-success text-white">
            <h5 class="mb-0">
                <i class="bi bi-check-circle"></i> Mis Clubes Aprobados
                <span class="badge bg-light text-dark">{{ total_aprobados }}</span>
            </h5>
        </div>
        <div class="card-body">
            {% if mis_clubes_aprobados %}
                <div class="row">
                    {% for club in mis_clubes_aprobados %}
                    <div class="col-md-6 mb-3">
                        <div class="card border-success">
                            <div class="card-body">
                                <h5 class="card-title">{{ club.nombre }}</h5>
                                <p class="card-text text-muted">{{ club.descripcion|truncatewords:20 }}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="badge bg-success">
                                        <i class="bi bi-people"></i> 
                                        {{ club.cupos_disponibles }} cupos disponibles
                                    </span>
                                    <span class="text-muted small">
                                        {{ club.fecha_aprobacion|date:"d/m/Y" }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> 
                    Aún no tienes clubes aprobados. Los clubes deben ser revisados por la federación.
                </div>
            {% endif %}
        </div>
    </div>

    <!-- SECCIÓN 3: CLUBES DISPONIBLES PARA POSTULAR -->
    <div class="card mb-4">
        <div class="card-header bg-info text-white">
            <h5 class="mb-0">
                <i class="bi bi-globe"></i> Clubes Disponibles para Postular
                <span class="badge bg-light text-dark">{{ total_disponibles }}</span>
            </h5>
        </div>
        <div class="card-body">
            {% if clubes_disponibles %}
                <div class="row">
                    {% for club in clubes_disponibles %}
                    <div class="col-md-4 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">{{ club.nombre }}</h5>
                                <p class="text-muted small">
                                    <i class="bi bi-building"></i> 
                                    {{ club.institucion_creadora.nombre }}
                                </p>
                                <p class="card-text">{{ club.descripcion|truncatewords:15 }}</p>
                                <div class="mb-2">
                                    <strong>Líneas de Investigación:</strong>
                                    <ul class="list-unstyled">
                                        {% for linea in club.lineas_investigacion %}
                                            <li><i class="bi bi-check"></i> {{ linea }}</li>
                                        {% endfor %}
                                    </ul>
                                </div>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="badge bg-info">
                                        {{ club.cupos_disponibles }} cupos
                                    </span>
                                    {% if club.puede_postularse %}
                                        <a href="{% url 'postular_club' club.id %}" 
                                           class="btn btn-sm btn-primary">
                                            <i class="bi bi-send"></i> Postular
                                        </a>
                                    {% else %}
                                        <span class="badge bg-secondary">No disponible</span>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> 
                    No hay clubes disponibles para postular en este momento.
                </div>
            {% endif %}
        </div>
    </div>

    <!-- Botón Flotante para Crear Club -->
    <a href="{% url 'crear_club' %}" 
       class="btn btn-primary btn-lg position-fixed bottom-0 end-0 m-4 rounded-circle shadow-lg"
       style="width: 60px; height: 60px; z-index: 1000;"
       title="Crear Nuevo Club">
        <i class="bi bi-plus-lg"></i>
    </a>
</div>
{% endblock %}
```

**Validación:**
- [ ] Se muestran 3 secciones claramente diferenciadas
- [ ] Los badges de estado son correctos
- [ ] Los botones contextuales funcionan según el estado
- [ ] El diseño es responsive
- [ ] Los iconos se muestran correctamente

---

## 📊 FASE 2: Actualización del Dashboard Institucional

### ✅ Tarea 2.1: Verificar Contexto en Vista
**Archivo:** `SistemaRegistro/users/views.py`  
**Línea:** 770 (función `dashboard_institucional`)  
**Prioridad:** 🟡 MEDIA

**Verificación:**
El código YA existe (líneas 818-824):
```python
mis_clubes = Club.objects.filter(institucion_creadora=institution)
total_mis_clubes = mis_clubes.count()
mis_clubes_aprobados = mis_clubes.filter(status="aprobado", activo=True).count()
```

**Acción:**
- [x] Verificar que estas variables están en el contexto del render
- [ ] Si no están, agregarlas al diccionario context

**Código a Verificar:**
```python
context = {
    "institution": institution,
    "total_mis_grupos": total_mis_grupos,
    "total_mis_participantes": total_mis_participantes,
    "eventos_disponibles": total_eventos_disponibles,
    "eventos_asignados": eventos_asignados,
    # Verificar que estas líneas existen:
    "total_mis_clubes": total_mis_clubes,
    "mis_clubes_aprobados": mis_clubes_aprobados,
}
```

---

### ✅ Tarea 2.2: Actualizar Template Dashboard
**Archivo:** `SistemaRegistro/templates/users/dashboard_institucional.html`  
**Ubicación:** Después de línea 83 (cierre del row de KPIs)  
**Prioridad:** 🟡 MEDIA

**Agregar:**
```html
<!-- Tarjetas de Clubes -->
<div class="row mb-4">
    <!-- Tarjeta: Mis Clubes -->
    <div class="col-md-3">
        <a href="{% url 'clubes_lista' %}" class="text-decoration-none">
            <div class="card border-0 shadow-lg overflow-hidden text-white" 
                 style="background: linear-gradient(145deg, #0b2c6d, #051636); border-radius: 15px;">
                <div class="card-body p-4 position-relative z-1">
                    <div class="text-white-50 small fw-bold text-uppercase mb-2">
                        Mis Clubes
                    </div>
                    <h2 class="display-5 fw-bold mb-0 counter" 
                        data-target="{{ total_mis_clubes|default:0 }}">0</h2>
                    <i class="bi bi-people-fill position-absolute opacity-10" 
                       style="font-size: 4.5rem; right: 15px; bottom: 10px;"></i>
                </div>
                <div style="height: 4px; background: #3b82f6;"></div>
            </div>
        </a>
    </div>

    <!-- Tarjeta: Clubes Aprobados -->
    <div class="col-md-3">
        <a href="{% url 'clubes_lista' %}" class="text-decoration-none">
            <div class="card border-0 shadow-lg overflow-hidden text-white" 
                 style="background: linear-gradient(145deg, #0b2c6d, #051636); border-radius: 15px;">
                <div class="card-body p-4 position-relative z-1">
                    <div class="text-white-50 small fw-bold text-uppercase mb-2">
                        Clubes Aprobados
                    </div>
                    <h2 class="display-5 fw-bold mb-0 counter" 
                        data-target="{{ mis_clubes_aprobados|default:0 }}">0</h2>
                    <i class="bi bi-check-circle position-absolute opacity-10" 
                       style="font-size: 4.5rem; right: 15px; bottom: 10px;"></i>
                </div>
                <div style="height: 4px; background: #10b981;"></div>
            </div>
        </a>
    </div>
</div>
```

**Validación:**
- [ ] Las tarjetas se muestran correctamente
- [ ] Los números son correctos
- [ ] Los enlaces funcionan
- [ ] El diseño es consistente con el resto del dashboard

---

## 🔒 FASE 3: Seguridad y Permisos

### ✅ Tarea 3.1: Validar Permisos en Todas las Vistas
**Archivos:** `SistemaRegistro/registry/views_institucional.py`  
**Prioridad:** 🔴 CRÍTICA

**Vistas a Validar:**

1. **`clubes_lista`** (línea 237)
   - [ ] Verificar que solo usuarios institucionales acceden
   - [ ] Verificar que solo ven sus propios clubes

2. **`crear_club`** (línea 273)
   - [ ] Verificar decorador `@login_required`
   - [ ] Verificar que solo institucionales crean clubes

3. **`editar_club`** (línea 363)
   - [ ] Verificar que el club pertenece a la institución
   - [ ] Verificar que solo se editan clubes en borrador/rechazado

4. **`enviar_club_revision`** (línea 323)
   - [ ] Verificar que el club pertenece a la institución
   - [ ] Verificar que solo se envían clubes en borrador

5. **`postular_club`** (línea 417)
   - [ ] Verificar que el club está aprobado
   - [ ] Verificar que no es el propio club
   - [ ] Verificar que hay cupos disponibles

**Código de Validación Estándar:**
```python
# Verificar permisos de institución
if club.institucion_creadora != institucion:
    messages.error(request, "No tienes permiso para modificar este club.")
    return redirect("clubes_lista")

# Verificar estado del club
if club.status not in ["borrador", "rechazado"]:
    messages.warning(request, "No puedes editar un club en este estado.")
    return redirect("clubes_lista")
```

---

## 🎨 FASE 4: Mejoras de UX

### ✅ Tarea 4.1: Agregar Mensajes de Feedback
**Prioridad:** 🟢 BAJA

**Ubicaciones:**
- Después de crear club
- Después de enviar a revisión
- Después de aprobar/rechazar
- Después de postular

**Ejemplo:**
```python
messages.success(request, f'✅ Club "{club.nombre}" creado exitosamente en estado BORRADOR.')
messages.info(request, f'📤 Club "{club.nombre}" enviado a revisión.')
messages.success(request, f'✅ Club "{club.nombre}" ha sido APROBADO.')
messages.warning(request, f'⚠️ Club "{club.nombre}" ha sido RECHAZADO.')
```

---

### ✅ Tarea 4.2: Agregar Tooltips y Ayudas
**Prioridad:** 🟢 BAJA

**Agregar en formularios:**
```html
<div class="form-group">
    <label for="status">Estado del Club</label>
    <i class="bi bi-info-circle" 
       data-bs-toggle="tooltip" 
       title="Los clubes inician en BORRADOR y deben ser enviados a revisión"></i>
    <select name="status" class="form-control" disabled>
        <option value="borrador">Borrador</option>
    </select>
</div>
```

---

## 📝 FASE 5: Documentación

### ✅ Tarea 5.1: Actualizar README
**Archivo:** `README.md`  
**Prioridad:** 🟢 BAJA

**Agregar sección:**
```markdown
## 🤖 Sistema de Clubes

### Flujo de Trabajo

1. **Creación**: Las instituciones crean clubes en estado BORRADOR
2. **Revisión**: Los clubes se envían a la federación para aprobación
3. **Aprobación**: La federación aprueba o rechaza clubes
4. **Postulación**: Otras instituciones pueden postular a clubes aprobados
5. **Membresía**: Los coordinadores aprueban membresías

### Estados de Clubes

- **Borrador**: Club en edición
- **Pendiente**: Enviado a revisión
- **En Revisión**: Siendo revisado por la federación
- **Aprobado**: Visible públicamente
- **Rechazado**: Requiere correcciones
```

---

## ✅ CHECKLIST FINAL

### Funcionalidad
- [ ] Vista `clubes_lista` diferencia 3 secciones
- [ ] Template muestra clubes según estado
- [ ] Dashboard muestra métricas de clubes
- [ ] Permisos validados en todas las vistas
- [ ] Mensajes de feedback implementados

### Seguridad
- [ ] Solo institucionales ven sus clubes
- [ ] Solo federación aprueba clubes
- [ ] Validaciones de permisos en todas las vistas
- [ ] No se pueden editar clubes aprobados

### UX
- [ ] Badges de estado correctos
- [ ] Botones contextuales según estado
- [ ] Diseño responsive
- [ ] Tooltips y ayudas

### Documentación
- [ ] README actualizado
- [ ] Comentarios en código
- [ ] Flujo de trabajo documentado

---

## 🚀 Orden de Ejecución Recomendado

1. **DÍA 1:** Tarea 1.1 - Actualizar vista `clubes_lista`
2. **DÍA 1:** Tarea 1.2 - Actualizar template `clubes_lista.html`
3. **DÍA 2:** Tarea 2.1 - Verificar contexto dashboard
4. **DÍA 2:** Tarea 2.2 - Actualizar template dashboard
5. **DÍA 3:** Tarea 3.1 - Validar permisos
6. **DÍA 4:** Tarea 4.1 - Mensajes de feedback
7. **DÍA 4:** Tarea 4.2 - Tooltips
8. **DÍA 5:** Tarea 5.1 - Documentación

---

## 📞 Soporte

Si encuentras problemas durante la implementación:
1. Revisar logs en `logs/django.log`
2. Verificar migraciones aplicadas
3. Comprobar permisos de usuario
4. Revisar contexto de templates con `{{ debug }}`
