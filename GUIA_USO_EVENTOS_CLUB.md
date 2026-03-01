# 🎯 Guía de Uso: Sistema de Eventos de Club

## 📋 Resumen

El sistema de eventos de club está **completamente implementado** y funcional. Permite a los clubes crear eventos que requieren aprobación de la federación antes de estar disponibles para inscripciones.

---

## 🔍 ¿Dónde está implementado?

### 1️⃣ **Backend (Vistas y Lógica)**

**Archivo**: `SistemaRegistro/registry/views_eventos.py`

**8 Vistas implementadas**:
- `crear_evento_club()` - Crear evento (propietario del club)
- `listar_eventos_club()` - Ver eventos del club
- `detalle_evento_club()` - Ver detalle de un evento
- `enviar_evento_revision()` - Enviar evento a revisión
- `inscribir_grupo_evento_club()` - Inscribir grupo al evento
- `revisar_eventos_club()` - Revisar eventos pendientes (federación)
- `aprobar_evento_club()` - Aprobar evento (federación)
- `rechazar_evento_club()` - Rechazar evento (federación)

---

### 2️⃣ **URLs (Rutas de Acceso)**

**Archivo**: `SistemaRegistro/registry/urls.py`

**8 URLs configuradas**:

```python
# Eventos de Club - Instituciones
path("clubes/<int:club_id>/eventos/", views_eventos.listar_eventos_club, name="eventos_club")
path("clubes/<int:club_id>/eventos/crear/", views_eventos.crear_evento_club, name="crear_evento_club")
path("eventos-club/<int:evento_id>/detalle/", views_eventos.detalle_evento_club, name="detalle_evento_club")
path("eventos-club/<int:evento_id>/enviar-revision/", views_eventos.enviar_evento_revision, name="enviar_evento_revision")
path("eventos-club/<int:evento_id>/inscribir-grupo/", views_eventos.inscribir_grupo_evento_club, name="inscribir_grupo_evento_club")

# Eventos de Club - Federación
path("admin/eventos-club/revisar/", views_eventos.revisar_eventos_club, name="revisar_eventos_club")
path("admin/eventos-club/<int:evento_id>/aprobar/", views_eventos.aprobar_evento_club, name="aprobar_evento_club")
path("admin/eventos-club/<int:evento_id>/rechazar/", views_eventos.rechazar_evento_club, name="rechazar_evento_club")
```

---

### 3️⃣ **Templates (Interfaz de Usuario)**

**Directorio**: `SistemaRegistro/registry/templates/registry/`

**8 Templates creados**:
- `evento_club_crear.html` - Formulario para crear evento
- `evento_club_lista.html` - Lista de eventos del club
- `evento_club_detalle.html` - Detalle del evento
- `evento_club_enviar_revision.html` - Confirmación de envío a revisión
- `inscribir_grupo_evento_club.html` - Formulario de inscripción de grupo
- `revisar_eventos_club.html` - Lista de eventos pendientes (federación)
- `aprobar_evento_club.html` - Formulario de aprobación (federación)
- `rechazar_evento_club.html` - Formulario de rechazo (federación)

---

### 4️⃣ **Menús de Navegación**

#### **A) Menú de Federación Central**

**Archivo**: `SistemaRegistro/templates/users/base_dashboard.html` (línea 177)

```html
<a href="{% url 'revisar_eventos_club' %}" class="nav-link-custom">
    <i class="bi bi-calendar-check"></i> Revisar Eventos Club
</a>
```

**Acceso**: Visible solo para federación central y superusuarios.

---

#### **B) Sidebar del Detalle de Club**

**Archivo**: `SistemaRegistro/registry/templates/registry/detalle_club.html` (líneas 227-241)

```html
<!-- Fase 4: Eventos del Club -->
{% if es_propietario or es_miembro %}
<div class="card border-0 shadow-sm mb-4">
    <div class="card-header bg-primary text-white py-3">
        <h6 class="mb-0"><i class="bi bi-calendar-event"></i> Eventos del Club</h6>
    </div>
    <div class="card-body text-center">
        {% if es_propietario %}
        <a href="{% url 'eventos_club' club.id %}" class="btn btn-primary w-100 mb-2">
            <i class="bi bi-calendar-plus"></i> Gestionar Eventos
        </a>
        {% else %}
        <a href="{% url 'eventos_club' club.id %}" class="btn btn-outline-primary w-100 mb-2">
            <i class="bi bi-calendar-event"></i> Ver Eventos
        </a>
        {% endif %}
    </div>
</div>
{% endif %}
```

**Acceso**: 
- **Propietario del club**: Botón "Gestionar Eventos" (azul sólido)
- **Miembros del club**: Botón "Ver Eventos" (azul outline)

---

## 🚀 Flujo de Uso Completo

### **PASO 1: Crear Evento (Propietario del Club)**

1. Ir al **Detalle del Club** (como propietario)
2. En el sidebar derecho, hacer clic en **"Gestionar Eventos"**
3. Hacer clic en **"Crear Nuevo Evento"**
4. Llenar el formulario:
   - Nombre del evento
   - Tipo (competencia, taller, charla, etc.)
   - Categoría
   - Descripción
   - Fecha
   - Modalidad (presencial/virtual/híbrida)
   - Ubicación
   - Capacidad máxima
   - Requisitos
5. Hacer clic en **"Crear Evento"**
6. El evento se crea en estado **BORRADOR**

**URL**: `/registry/clubes/<club_id>/eventos/crear/`

---

### **PASO 2: Enviar a Revisión (Propietario del Club)**

1. En la lista de eventos del club, localizar el evento en borrador
2. Hacer clic en **"Enviar a Revisión"**
3. Confirmar el envío
4. El evento cambia a estado **PENDIENTE**

**URL**: `/registry/eventos-club/<evento_id>/enviar-revision/`

---

### **PASO 3: Revisar Evento (Federación Central)**

1. Iniciar sesión como **federación central** o **superusuario**
2. En el menú lateral, hacer clic en **"Revisar Eventos Club"**
3. Ver la lista de eventos pendientes
4. Hacer clic en **"Revisar"** en el evento deseado

**URL**: `/registry/admin/eventos-club/revisar/`

---

### **PASO 4A: Aprobar Evento (Federación Central)**

1. En la vista de revisión, hacer clic en **"Aprobar"**
2. Agregar comentarios de aprobación (obligatorio)
3. Hacer clic en **"Confirmar Aprobación"**
4. El evento cambia a estado **APROBADO**
5. El evento ahora acepta inscripciones

**URL**: `/registry/admin/eventos-club/<evento_id>/aprobar/`

---

### **PASO 4B: Rechazar Evento (Federación Central)**

1. En la vista de revisión, hacer clic en **"Rechazar"**
2. Especificar el motivo del rechazo (obligatorio)
3. Hacer clic en **"Confirmar Rechazo"**
4. El evento cambia a estado **RECHAZADO**
5. El propietario puede corregir y reenviar

**URL**: `/registry/admin/eventos-club/<evento_id>/rechazar/`

---

### **PASO 5: Inscribir Grupo (Miembros del Club)**

1. Ir al **Detalle del Evento** (solo eventos aprobados)
2. Hacer clic en **"Inscribir Grupo"**
3. Seleccionar un grupo en estado **EDITABLE**
4. Seleccionar el rol de participación
5. Hacer clic en **"Inscribir Grupo"**
6. El grupo cambia a estado **INSCRITO**

**URL**: `/registry/eventos-club/<evento_id>/inscribir-grupo/`

**Validaciones**:
- Solo miembros aprobados del club pueden inscribir grupos
- Solo grupos en estado "editable" pueden inscribirse
- No se puede inscribir el mismo grupo dos veces

---

## 🔐 Permisos y Validaciones

### **Crear Evento**
- ✅ Solo propietario del club (institución creadora)
- ✅ Club debe estar aprobado
- ✅ Usuario debe tener perfil institucional

### **Enviar a Revisión**
- ✅ Solo propietario del club
- ✅ Evento debe estar en estado "borrador" o "rechazado"

### **Revisar/Aprobar/Rechazar**
- ✅ Solo federación central o superusuarios
- ✅ Evento debe estar en estado "pendiente"
- ✅ Comentarios obligatorios

### **Inscribir Grupo**
- ✅ Solo miembros aprobados del club
- ✅ Evento debe estar en estado "aprobado"
- ✅ Grupo debe estar en estado "editable"
- ✅ Grupo no debe estar ya inscrito

---

## 📊 Estados del Evento

| Estado | Descripción | Puede Editar | Puede Inscribirse |
|--------|-------------|--------------|-------------------|
| **borrador** | Recién creado | Propietario | ❌ No |
| **pendiente** | En revisión | ❌ No | ❌ No |
| **aprobado** | Aprobado por federación | ❌ No | ✅ Sí |
| **rechazado** | Rechazado por federación | Propietario | ❌ No |

---

## 🎯 Puntos de Acceso en la UI

### **Para Propietarios de Club**

1. **Dashboard** → **Mis Clubes** → **[Seleccionar Club]** → **Gestionar Eventos** (sidebar derecho)
2. **Dashboard** → **Directorio Clubes** → **[Seleccionar tu Club]** → **Gestionar Eventos** (sidebar derecho)

### **Para Miembros de Club**

1. **Dashboard** → **Mis Membresías** → **[Ver Club]** → **Ver Eventos** (sidebar derecho)
2. **Dashboard** → **Directorio Clubes** → **[Seleccionar Club]** → **Ver Eventos** (sidebar derecho)

### **Para Federación Central**

1. **Dashboard** → **Revisar Eventos Club** (menú lateral izquierdo)

---

## 🧪 Testing

**Archivo**: `SistemaRegistro/registry/tests_eventos.py`

**17 tests implementados**:
- ✅ Crear evento de club
- ✅ Validar permisos de creación
- ✅ Enviar a revisión
- ✅ Aprobar evento
- ✅ Rechazar evento
- ✅ Inscribir grupo
- ✅ Validar membresía para inscripción
- ✅ Validar estado del grupo
- ✅ Validar duplicados de inscripción

**Ejecutar tests**:
```bash
cd SistemaRegistro
python manage.py test registry.tests_eventos
```

---

## 📝 Ejemplo de Uso Real

### **Escenario**: Club de Robótica "TechBots" crea un taller

1. **Institución "Liceo Bolivariano"** crea el club "TechBots" ✅
2. **Federación** aprueba el club ✅
3. **Liceo Bolivariano** (propietario) crea evento "Taller de Arduino" en **BORRADOR** ✅
4. **Liceo Bolivariano** envía evento a revisión → **PENDIENTE** ✅
5. **Federación** revisa y aprueba el evento → **APROBADO** ✅
6. **Institución "Escuela Técnica"** (miembro del club) inscribe su grupo "Innovadores" ✅
7. **Institución "Colegio Nacional"** (miembro del club) inscribe su grupo "Creadores" ✅

---

## 🔧 Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `registry/models.py` | Modelo Evento con campos de club |
| `registry/views_eventos.py` | Lógica de negocio |
| `registry/urls.py` | Rutas de acceso |
| `registry/templates/registry/evento_club_*.html` | Interfaces de usuario |
| `templates/users/base_dashboard.html` | Menú de federación |
| `registry/templates/registry/detalle_club.html` | Botones de acceso |
| `registry/tests_eventos.py` | Tests unitarios |

---

## ✅ Checklist de Implementación

- [x] Modelo Evento extendido con campos de club
- [x] Migración 0021 aplicada
- [x] 8 vistas implementadas
- [x] 8 URLs configuradas
- [x] 8 templates creados
- [x] Menú de federación agregado
- [x] Botones en detalle de club agregados
- [x] Validaciones de permisos implementadas
- [x] Validaciones de membresía implementadas
- [x] 17 tests implementados y pasando
- [x] Documentación completa

---

## 🚨 Problemas Comunes

### **No veo el botón "Gestionar Eventos"**

**Causa**: No eres propietario del club.

**Solución**: Solo la institución creadora del club puede gestionar eventos. Verifica que tu institución sea la que creó el club.

---

### **No puedo inscribir mi grupo**

**Causa**: Tu institución no es miembro del club o el evento no está aprobado.

**Solución**: 
1. Verifica que tu institución tenga membresía aprobada en el club
2. Verifica que el evento esté en estado "aprobado"

---

### **No veo "Revisar Eventos Club" en el menú**

**Causa**: No tienes permisos de federación.

**Solución**: Solo federación central y superusuarios pueden revisar eventos. Verifica tu tipo de usuario.

---

## 📚 Documentación Relacionada

- [`ARQUITECTURA_EVENTOS_DUAL.md`](ARQUITECTURA_EVENTOS_DUAL.md) - Arquitectura técnica
- [`FASE2_EVENTOS_CLUB_COMPLETADA.md`](FASE2_EVENTOS_CLUB_COMPLETADA.md) - Implementación de vistas
- [`FASE3_TEMPLATES_EVENTOS_COMPLETADA.md`](FASE3_TEMPLATES_EVENTOS_COMPLETADA.md) - Implementación de templates
- [`FASE4_MENUS_NAVEGACION_COMPLETADA.md`](FASE4_MENUS_NAVEGACION_COMPLETADA.md) - Implementación de menús
- [`FASE5_TESTING_COMPLETADA.md`](FASE5_TESTING_COMPLETADA.md) - Tests implementados
- [`SISTEMA_EVENTOS_DUAL_COMPLETADO.md`](SISTEMA_EVENTOS_DUAL_COMPLETADO.md) - Resumen completo

---

## 🎓 Conclusión

El sistema de eventos de club está **100% funcional** y listo para usar. Los puntos de acceso están en:

1. **Sidebar del detalle de club** (botón "Gestionar Eventos" o "Ver Eventos")
2. **Menú lateral de federación** (enlace "Revisar Eventos Club")

Todos los flujos de creación, revisión, aprobación e inscripción están implementados y validados con tests.
