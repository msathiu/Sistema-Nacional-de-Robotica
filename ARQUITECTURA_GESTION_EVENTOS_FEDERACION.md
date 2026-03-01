# 🏗️ Arquitectura: Gestión de Eventos por Federación

## 📋 Requerimientos

1. ✅ Federación puede crear eventos (publicación directa)
2. ✅ Federación gestiona ciclo de vida de eventos institucionales
3. ✅ Eventos institucionales requieren aprobación para ser visibles
4. ✅ Estados del ciclo: Revisión → Aprobado → Publicado → En Proceso → Concluido

---

## 🎯 Solución Arquitectónica

### 1. Estados del Modelo Evento (ACTUALIZADO)

```python
# registry/models.py - Clase Evento
ESTADO_CHOICES = [
    # Workflow Institucional
    ('borrador', 'Borrador'),              # Institución crea
    ('pendiente', 'Pendiente Aprobación'), # Institución envía
    ('en_revision', 'En Revisión'),        # Federación revisa
    ('aprobado', 'Aprobado'),              # Federación aprueba (no visible)
    ('publicado', 'Publicado'),            # Federación publica (VISIBLE)
    
    # Ciclo de Vida
    ('en_proceso', 'En Proceso'),          # Evento en curso
    ('finalizado', 'Finalizado'),          # Evento concluido
    
    # Estados Especiales
    ('rechazado', 'Rechazado'),            # Federación rechaza
    ('cancelado', 'Cancelado'),            # Cancelado por cualquier motivo
    
    # Compatibilidad (deprecados)
    ('abierto', 'Abierto'),
    ('pausado', 'Pausado'),
    ('cerrado', 'Cerrado'),
]
```

### 2. Permisos y Roles

```python
┌─────────────────────────────────────────────────────────────┐
│  FEDERACIÓN (fed_central, fed_regional, superuser)         │
├─────────────────────────────────────────────────────────────┤
│  ✅ Crear eventos → estado: 'publicado' (directo)           │
│  ✅ Revisar eventos institucionales                         │
│  ✅ Aprobar: pendiente → aprobado                           │
│  ✅ Publicar: aprobado → publicado                          │
│  ✅ Gestionar ciclo: publicado → en_proceso → finalizado    │
│  ✅ Rechazar: pendiente → rechazado                         │
│  ✅ Cancelar cualquier evento                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  INSTITUCIÓN (institucional)                                │
├─────────────────────────────────────────────────────────────┤
│  ✅ Crear eventos → estado: 'borrador'                      │
│  ✅ Enviar a revisión: borrador → pendiente                 │
│  ✅ Editar eventos en borrador/rechazado                    │
│  ✅ Ver solo eventos publicados de otras instituciones      │
│  ❌ NO puede publicar directamente                          │
│  ❌ NO puede cambiar estados de aprobación                  │
└─────────────────────────────────────────────────────────────┘
```

### 3. Flujos de Trabajo

#### A. Evento Institucional (Requiere Aprobación)
```
Institución crea
    ↓
[borrador] → Editable por institución
    ↓ (Enviar a revisión)
[pendiente] → Visible para federación
    ↓ (Federación toma)
[en_revision] → Federación revisando
    ↓
    ├─→ [aprobado] → Federación aprueba (aún no visible)
    │       ↓ (Publicar)
    │   [publicado] → VISIBLE para todos
    │       ↓
    │   [en_proceso] → Evento en curso
    │       ↓
    │   [finalizado] → Evento concluido
    │
    └─→ [rechazado] → Institución puede corregir
            ↓
        [borrador] → Reinicia ciclo
```

#### B. Evento de Federación (Publicación Directa)
```
Federación crea
    ↓
[publicado] → VISIBLE inmediatamente
    ↓
[en_proceso] → Evento en curso
    ↓
[finalizado] → Evento concluido
```

---

## 🛠️ Implementación

### Paso 1: Actualizar Modelo (✅ COMPLETADO)

```python
# registry/models.py
class Evento(models.Model):
    # ... campos existentes ...
    
    estado_evento = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default="abierto", 
        db_index=True
    )
    
    # Método para verificar visibilidad
    def es_visible_publicamente(self):
        """Solo eventos publicados son visibles para todos"""
        return self.estado_evento == 'publicado' and self.activo
```

### Paso 2: Habilitar Creación para Federación

```python
# users/views.py

@login_required
def crear_evento(request):
    """
    Vista unificada para crear eventos.
    - Federación: Publica directamente
    - Instituciones: Crea en borrador
    """
    perfil = request.user.userprofile
    user_type = perfil.user_type
    
    # Validar permisos
    roles_permitidos = ['institucional', 'fed_central', 'fed_regional', 'superuser']
    if user_type not in roles_permitidos:
        messages.error(request, "No tienes permisos para crear eventos.")
        return redirect('dashboard')
    
    es_federacion = user_type in ['fed_central', 'fed_regional', 'superuser']
    
    if request.method == 'POST':
        # ... validaciones ...
        
        # Determinar estado inicial según rol
        if es_federacion:
            estado_inicial = 'publicado'  # Federación publica directo
            institucion = None  # Eventos de federación no tienen institución
        else:
            estado_inicial = 'borrador'  # Instituciones en borrador
            institucion = perfil.institution
        
        evento = Evento.objects.create(
            nombre=request.POST.get('nombre'),
            # ... otros campos ...
            estado_evento=estado_inicial,
            institucion=institucion,
            tipo_evento='institucional' if institucion else 'federacion',
            activo=True
        )
        
        if es_federacion:
            messages.success(request, f'✅ Evento "{evento.nombre}" publicado exitosamente.')
        else:
            messages.success(request, f'✅ Evento "{evento.nombre}" creado. Envíalo a revisión para publicarlo.')
        
        return redirect('gestionar_eventos_inst')
    
    # GET - Renderizar formulario
    context = {
        'es_federacion': es_federacion,
        # ... otros datos ...
    }
    return render(request, 'users/crear_evento.html', context)
```

### Paso 3: Vista de Gestión de Eventos (Federación)

```python
# users/views.py

@login_required
def gestionar_eventos_federacion(request):
    """
    Panel de gestión de eventos para federación.
    Permite revisar, aprobar, publicar y gestionar ciclo de vida.
    """
    perfil = request.user.userprofile
    
    if perfil.user_type not in ['fed_central', 'fed_regional', 'superuser']:
        messages.error(request, "Acceso denegado.")
        return redirect('dashboard')
    
    # Filtrar por territorio si es regional
    if perfil.user_type == 'fed_regional':
        eventos_pendientes = Evento.objects.filter(
            estado_evento='pendiente',
            estado=perfil.estado
        )
    else:
        eventos_pendientes = Evento.objects.filter(estado_evento='pendiente')
    
    eventos_en_revision = Evento.objects.filter(estado_evento='en_revision')
    eventos_aprobados = Evento.objects.filter(estado_evento='aprobado')
    eventos_publicados = Evento.objects.filter(estado_evento='publicado')
    
    context = {
        'eventos_pendientes': eventos_pendientes,
        'eventos_en_revision': eventos_en_revision,
        'eventos_aprobados': eventos_aprobados,
        'eventos_publicados': eventos_publicados,
    }
    return render(request, 'users/gestionar_eventos_federacion.html', context)
```

### Paso 4: Acciones de Gestión

```python
# users/views.py

@login_required
@require_http_methods(['POST'])
def cambiar_estado_evento_federacion(request, evento_id):
    """
    Permite a la federación cambiar el estado de un evento.
    """
    perfil = request.user.userprofile
    
    if perfil.user_type not in ['fed_central', 'fed_regional', 'superuser']:
        return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)
    
    evento = get_object_or_404(Evento, id=evento_id)
    nuevo_estado = request.POST.get('nuevo_estado')
    observaciones = request.POST.get('observaciones', '')
    
    # Validar transiciones permitidas
    transiciones_validas = {
        'pendiente': ['en_revision', 'rechazado'],
        'en_revision': ['aprobado', 'rechazado'],
        'aprobado': ['publicado', 'rechazado'],
        'publicado': ['en_proceso', 'cancelado'],
        'en_proceso': ['finalizado', 'cancelado'],
    }
    
    if nuevo_estado not in transiciones_validas.get(evento.estado_evento, []):
        return JsonResponse({
            'status': 'error',
            'message': f'Transición no válida: {evento.estado_evento} → {nuevo_estado}'
        }, status=400)
    
    # Aplicar cambio
    evento.estado_evento = nuevo_estado
    evento.save()
    
    # Registrar en historial (si existe modelo HistorialEvento)
    # HistorialEvento.objects.create(...)
    
    # Notificar a la institución si aplica
    if evento.institucion and nuevo_estado in ['aprobado', 'publicado', 'rechazado']:
        # Enviar notificación
        pass
    
    return JsonResponse({
        'status': 'success',
        'message': f'Evento cambiado a: {evento.get_estado_evento_display()}'
    })
```

### Paso 5: Filtrar Eventos Visibles

```python
# users/views.py

@login_required
def eventos_disponibles(request):
    """
    Vista para mostrar eventos disponibles según el perfil del usuario.
    """
    perfil = request.user.userprofile
    hoy = date.today()
    
    # Base: Solo eventos publicados y activos
    eventos = Evento.objects.filter(
        estado_evento='publicado',
        activo=True,
        cancelado=False
    )
    
    # Filtrar por territorio si es institucional
    if perfil.user_type == 'institucional':
        eventos = eventos.filter(
            Q(estado=perfil.institution.estado) |  # Eventos de su estado
            Q(estado__isnull=True)  # Eventos nacionales
        )
    
    # Separar por fecha
    eventos_proximos = eventos.filter(fecha__gte=hoy).order_by('fecha')
    eventos_pasados = eventos.filter(fecha__lt=hoy).order_by('-fecha')[:10]
    
    context = {
        'eventos_proximos': eventos_proximos,
        'eventos_pasados': eventos_pasados,
    }
    return render(request, 'users/eventos_disponibles.html', context)
```

---

## 📊 Migración de Base de Datos

```bash
# Generar migración
python manage.py makemigrations

# Aplicar migración
python manage.py migrate

# Actualizar eventos existentes (opcional)
python manage.py shell
>>> from registry.models import Evento
>>> Evento.objects.filter(estado_evento='abierto').update(estado_evento='publicado')
```

---

## 🎨 Templates Necesarios

### 1. `crear_evento.html` (Actualizar)
- Agregar indicador visual si es federación
- Mostrar que se publicará directamente

### 2. `gestionar_eventos_federacion.html` (Nuevo)
- Tabs para: Pendientes | En Revisión | Aprobados | Publicados
- Botones de acción por estado
- Formulario de observaciones

### 3. `eventos_disponibles.html` (Actualizar)
- Mostrar solo eventos publicados
- Badge de estado visible

---

## ✅ Checklist de Implementación

- [x] Actualizar estados en modelo Evento
- [ ] Modificar vista `crear_evento` para permitir federación
- [ ] Crear vista `gestionar_eventos_federacion`
- [ ] Crear vista `cambiar_estado_evento_federacion`
- [ ] Actualizar vista `eventos_disponibles` (filtrar solo publicados)
- [ ] Crear template `gestionar_eventos_federacion.html`
- [ ] Actualizar template `crear_evento.html`
- [ ] Agregar URLs en `users/urls.py`
- [ ] Generar y aplicar migraciones
- [ ] Testing de flujos completos

---

## 🔒 Reglas de Negocio

1. **Visibilidad**: Solo eventos con `estado_evento='publicado'` son visibles públicamente
2. **Creación Directa**: Federación crea eventos en estado `publicado`
3. **Aprobación Requerida**: Instituciones deben pasar por: borrador → pendiente → aprobado → publicado
4. **Territorio**: Federación regional solo gestiona eventos de su estado
5. **Historial**: Todos los cambios de estado deben registrarse
6. **Notificaciones**: Instituciones reciben notificación en cada cambio de estado

---

## 📈 Beneficios

✅ **Centralización**: Federación controla qué eventos son visibles
✅ **Calidad**: Revisión antes de publicación
✅ **Trazabilidad**: Historial completo de cambios
✅ **Flexibilidad**: Federación puede publicar eventos urgentes directamente
✅ **Escalabilidad**: Fácil agregar nuevos estados si se requiere
