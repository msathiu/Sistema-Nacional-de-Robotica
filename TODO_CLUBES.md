# TODO: Mejoras del Sistema de Clubes

## 🎯 Objetivo
Mejorar la funcionalidad de clubes implementando visualización correcta según permisos y flujo de aprobación robusto.

---

## 📊 Estado Actual

### ✅ Completado
- [x] Modelo Club con campos: status, coordinador, documento_legal
- [x] Modelo MembresiaClu con campo tipo_linea
- [x] Migraciones aplicadas
- [x] Vistas CRUD completas (crear, editar, enviar a revisión)
- [x] Vistas de aprobación/rechazo para federación
- [x] URLs configuradas
- [x] Templates básicos creados
- [x] Métodos del modelo: enviar_a_revision(), aprobar(), rechazar()
- [x] Propiedades: cupos_disponibles, puede_postularse

### ❌ Problemas Identificados

#### 1. Vista `clubes_lista` - Lógica Incorrecta
**Ubicación:** `registry/views_institucional.py:237`
- ❌ Muestra TODOS los clubes sin diferenciar estados
- ❌ No separa "Mis Clubes Creados" de "Clubes Aprobados"
- ❌ No filtra correctamente clubes disponibles de otras instituciones

#### 2. Dashboard Institucional - Sin Visualización
**Ubicación:** `users/views.py:770`
- ✅ La vista YA calcula las métricas (líneas 818-824)
- ❌ El template NO muestra las tarjetas de clubes

#### 3. Permisos y Seguridad
- ❌ Falta validación estricta de permisos en algunas vistas
- ❌ No hay control de quién puede ver qué clubes

---

## 🔴 TAREAS CRÍTICAS (Prioridad Alta)

### Tarea 1: Corregir Vista `clubes_lista`
**Archivo:** `SistemaRegistro/registry/views_institucional.py:237`
**Tiempo Estimado:** 30 minutos

**Problema:**
```python
# Línea 247-249: Muestra TODOS sin filtrar
mis_clubes = Club.objects.filter(institucion_creadora=institucion).order_by("-fecha_creacion")
```

**Solución:**
Diferenciar 3 secciones:
1. **Mis Clubes Creados**: Todos los estados (para gestión interna)
2. **Mis Clubes Aprobados**: Solo aprobados de mi institución
3. **Clubes Disponibles**: Aprobados de OTRAS instituciones

**Código Propuesto:**
```python
# 1. MIS CLUBES CREADOS (todos los estados)
mis_clubes_creados = Club.objects.filter(
    institucion_creadora=institucion
).order_by("-fecha_creacion")

# 2. MIS CLUBES APROBADOS
mis_clubes_aprobados = mis_clubes_creados.filter(
    status="aprobado",
    activo=True
)

# 3. CLUBES DISPONIBLES (otras instituciones)
clubes_disponibles = Club.objects.filter(
    activo=True,
    status="aprobado",
    estado_vinculacion__in=["abierto", "invitacion"]
).exclude(
    institucion_creadora=institucion
).annotate(
    num_membresias=Count("membresias", filter=Q(membresias__estado="aprobada"))
)

# Filtrar con cupos
clubes_disponibles = [c for c in clubes_disponibles if c.cupos_disponibles > 0]

context = {
    "mis_clubes_creados": mis_clubes_creados,
    "mis_clubes_aprobados": mis_clubes_aprobados,
    "clubes_disponibles": clubes_disponibles,
}
```

**Validación:**
- [ ] La vista compila sin errores
- [ ] Se muestran 3 secciones diferenciadas
- [ ] Clubes en borrador solo en "Mis Clubes Creados"
- [ ] Clubes aprobados en ambas secciones
- [ ] Clubes de otras instituciones solo en "Disponibles"

---

### Tarea 2: Actualizar Template `clubes_lista.html`
**Archivo:** `SistemaRegistro/registry/templates/registry/clubes_lista.html`
**Tiempo Estimado:** 1 hora

**Cambios Requeridos:**
1. Crear 3 secciones con cards diferenciadas
2. Agregar badges de estado (borrador, pendiente, aprobado, rechazado)
3. Botones contextuales según estado del club
4. Diseño responsive con Bootstrap 5

**Estructura:**
```html
<!-- SECCIÓN 1: Mis Clubes Creados -->
<div class="card mb-4">
    <div class="card-header bg-primary">
        <h5>Mis Clubes Creados ({{ total_creados }})</h5>
    </div>
    <div class="card-body">
        <!-- Tabla con todos los clubes creados -->
    </div>
</div>

<!-- SECCIÓN 2: Mis Clubes Aprobados -->
<div class="card mb-4">
    <div class="card-header bg-success">
        <h5>Mis Clubes Aprobados ({{ total_aprobados }})</h5>
    </div>
    <div class="card-body">
        <!-- Cards de clubes aprobados -->
    </div>
</div>

<!-- SECCIÓN 3: Clubes Disponibles -->
<div class="card mb-4">
    <div class="card-header bg-info">
        <h5>Clubes Disponibles ({{ total_disponibles }})</h5>
    </div>
    <div class="card-body">
        <!-- Cards de clubes para postular -->
    </div>
</div>
```

**Validación:**
- [ ] 3 secciones claramente diferenciadas
- [ ] Badges de estado correctos
- [ ] Botones contextuales funcionan
- [ ] Diseño responsive
- [ ] Iconos Bootstrap Icons

---

### Tarea 3: Agregar Tarjetas al Dashboard Institucional
**Archivo:** `SistemaRegistro/templates/users/dashboard_institucional.html`
**Ubicación:** Después de línea 83
**Tiempo Estimado:** 20 minutos

**Agregar:**
```html
<!-- Tarjetas de Clubes -->
<div class="row mb-4">
    <!-- Tarjeta: Mis Clubes -->
    <div class="col-md-3">
        <a href="{% url 'clubes_lista' %}" class="text-decoration-none">
            <div class="card border-0 shadow-lg text-white" 
                 style="background: linear-gradient(145deg, #0b2c6d, #051636);">
                <div class="card-body p-4">
                    <div class="text-white-50 small fw-bold text-uppercase mb-2">
                        Mis Clubes
                    </div>
                    <h2 class="display-5 fw-bold mb-0">{{ total_mis_clubes|default:0 }}</h2>
                </div>
            </div>
        </a>
    </div>
    
    <!-- Tarjeta: Clubes Aprobados -->
    <div class="col-md-3">
        <a href="{% url 'clubes_lista' %}" class="text-decoration-none">
            <div class="card border-0 shadow-lg text-white" 
                 style="background: linear-gradient(145deg, #0b2c6d, #051636);">
                <div class="card-body p-4">
                    <div class="text-white-50 small fw-bold text-uppercase mb-2">
                        Clubes Aprobados
                    </div>
                    <h2 class="display-5 fw-bold mb-0">{{ mis_clubes_aprobados|default:0 }}</h2>
                </div>
            </div>
        </a>
    </div>
</div>
```

**Validación:**
- [ ] Tarjetas se muestran correctamente
- [ ] Números son correctos
- [ ] Enlaces funcionan
- [ ] Diseño consistente con dashboard

---

## 🟡 TAREAS MEDIAS (Prioridad Media)

### Tarea 4: Validar Permisos en Todas las Vistas
**Archivos:** `SistemaRegistro/registry/views_institucional.py`
**Tiempo Estimado:** 1 hora

**Vistas a Validar:**
- [ ] `clubes_lista` - Solo institucionales
- [ ] `crear_club` - Solo institucionales
- [ ] `editar_club` - Solo propietario, solo borrador/rechazado
- [ ] `enviar_club_revision` - Solo propietario, solo borrador
- [ ] `postular_club` - Verificar club aprobado y cupos
- [ ] `revisar_clubes` - Solo staff/federación
- [ ] `aprobar_club` - Solo staff/federación
- [ ] `rechazar_club` - Solo staff/federación

**Código de Validación:**
```python
# Verificar permisos de institución
if club.institucion_creadora != institucion:
    messages.error(request, "No tienes permiso")
    return redirect("clubes_lista")

# Verificar estado del club
if club.status not in ["borrador", "rechazado"]:
    messages.warning(request, "No puedes editar este club")
    return redirect("clubes_lista")
```

---

### Tarea 5: Agregar Mensajes de Feedback
**Archivos:** Todas las vistas de clubes
**Tiempo Estimado:** 30 minutos

**Mensajes a Agregar:**
- [ ] Después de crear club: "✅ Club creado en BORRADOR"
- [ ] Después de enviar a revisión: "📤 Club enviado a revisión"
- [ ] Después de aprobar: "✅ Club APROBADO"
- [ ] Después de rechazar: "⚠️ Club RECHAZADO"
- [ ] Después de postular: "📨 Solicitud enviada"

---

## 🟢 TAREAS BAJAS (Prioridad Baja)

### Tarea 6: Agregar Tooltips y Ayudas
**Tiempo Estimado:** 30 minutos

- [ ] Tooltips en formularios
- [ ] Ayudas contextuales
- [ ] Iconos informativos

---

### Tarea 7: Documentación
**Tiempo Estimado:** 1 hora

- [ ] Actualizar README.md con sección de clubes
- [ ] Documentar flujo de trabajo
- [ ] Agregar comentarios en código
- [ ] Crear guía de usuario

---

## 📋 CHECKLIST FINAL

### Funcionalidad
- [ ] Vista `clubes_lista` diferencia 3 secciones
- [ ] Template muestra clubes según estado
- [ ] Dashboard muestra métricas de clubes
- [ ] Permisos validados en todas las vistas
- [ ] Mensajes de feedback implementados

### Seguridad
- [ ] Solo institucionales ven sus clubes
- [ ] Solo federación aprueba clubes
- [ ] Validaciones de permisos
- [ ] No se editan clubes aprobados

### UX
- [ ] Badges de estado correctos
- [ ] Botones contextuales
- [ ] Diseño responsive
- [ ] Tooltips y ayudas

### Documentación
- [ ] README actualizado
- [ ] Comentarios en código
- [ ] Flujo documentado

---

## 🚀 Orden de Ejecución Recomendado

**DÍA 1:**
1. Tarea 1: Corregir vista `clubes_lista` (30 min)
2. Tarea 2: Actualizar template `clubes_lista.html` (1 hora)

**DÍA 2:**
3. Tarea 3: Agregar tarjetas al dashboard (20 min)
4. Tarea 4: Validar permisos (1 hora)

**DÍA 3:**
5. Tarea 5: Mensajes de feedback (30 min)
6. Tarea 6: Tooltips (30 min)
7. Tarea 7: Documentación (1 hora)

---

## 📚 Archivos de Referencia

- **Análisis Completo:** `ANALISIS_COMPLETO_CLUBES.md`
- **Tareas Detalladas:** `TAREAS_IMPLEMENTACION_CLUBES.md`
- **Modelo Club:** `registry/models.py:746`
- **Vistas Clubes:** `registry/views_institucional.py:237-580`
- **URLs:** `registry/urls.py:35-82`
- **Dashboard:** `users/views.py:770`

---

## 📞 Notas Importantes

1. **No romper el sistema actual**: Todas las mejoras son aditivas
2. **Priorizar seguridad**: Validar permisos en cada vista
3. **Feedback claro**: Mensajes informativos para el usuario
4. **Diseño consistente**: Mantener estética del sistema
5. **Testing**: Probar cada cambio antes de continuar

