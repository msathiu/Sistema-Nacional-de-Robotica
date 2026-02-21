# 🔄 Arquitectura: Transferencia de Propiedad de Clubes

## 🎯 Problema Identificado

**Situación**: El propietario de un club no puede salirse porque:
- Es el responsable del club
- Debe mantener la gestión activa
- No puede abandonar sin dejar sucesor

**Soluciones Actuales**:
1. ❌ **Salir como miembro**: BLOQUEADO (correcto)
2. ✅ **Eliminar club**: Requiere aprobación de federación (ya implementado)
3. 🆕 **Transferir propiedad**: NUEVA FUNCIONALIDAD (recomendada)

---

## 🏗️ Solución Arquitectónica Profesional

### Flujo Lógico Completo

```
Propietario quiere abandonar el club:
│
├─ Opción 1: TRANSFERIR PROPIEDAD
│   ├─ Selecciona miembro activo del club
│   ├─ Envía solicitud de transferencia
│   ├─ Nuevo propietario acepta/rechaza
│   │   ├─ Si ACEPTA → Transferencia completada
│   │   │   └─ Propietario anterior puede salir como miembro
│   │   └─ Si RECHAZA → Solicitud cancelada
│   │       └─ Propietario puede intentar con otro miembro
│   └─ Notificaciones a ambas partes
│
└─ Opción 2: ELIMINAR CLUB
    ├─ Crea solicitud de eliminación
    ├─ Federación revisa y decide
    │   ├─ Si APRUEBA → Club eliminado
    │   └─ Si RECHAZA → Club permanece activo
    └─ Notificaciones a propietario y federación
```

---

## 📊 Modelo de Datos

### Nuevo Modelo: SolicitudTransferenciaClub

```python
class SolicitudTransferenciaClub(models.Model):
    """Gestiona solicitudes de transferencia de propiedad de clubes."""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Aceptación'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    propietario_actual = models.ForeignKey(Institucion, related_name='transferencias_enviadas')
    nuevo_propietario = models.ForeignKey(Institucion, related_name='transferencias_recibidas')
    
    motivo = models.TextField(verbose_name="Motivo de la transferencia")
    mensaje_nuevo_propietario = models.TextField(blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    observaciones_respuesta = models.TextField(blank=True)
    
    # Auditoría
    usuario_solicitante = models.ForeignKey(User, related_name='transferencias_solicitadas')
    usuario_respondio = models.ForeignKey(User, null=True, related_name='transferencias_respondidas')
```

---

## 🔄 Flujo de Transferencia

### Fase 1: Solicitud

**Actor**: Propietario Actual

1. Accede a "Gestionar Club"
2. Ve opción "Transferir Propiedad"
3. Selecciona miembro activo del club
4. Proporciona motivo de transferencia
5. Envía solicitud

**Validaciones**:
- ✅ Usuario es propietario del club
- ✅ Club está aprobado y activo
- ✅ Nuevo propietario es miembro activo (membresía aprobada)
- ✅ No hay transferencia pendiente activa

### Fase 2: Revisión

**Actor**: Nuevo Propietario (Candidato)

1. Recibe notificación de solicitud
2. Revisa información del club
3. Decide: Aceptar o Rechazar

**Si ACEPTA**:
```python
# 1. Actualizar club
club.institucion_creadora = nuevo_propietario
club.coordinador = nuevo_coordinador_user
club.save()

# 2. Actualizar solicitud
solicitud.estado = 'aceptada'
solicitud.fecha_respuesta = timezone.now()
solicitud.save()

# 3. Registrar en historial
HistorialClub.objects.create(
    club=club,
    usuario=nuevo_coordinador,
    estado_anterior='propietario_anterior',
    estado_nuevo='propietario_nuevo',
    observaciones=f'Transferencia de propiedad aceptada'
)

# 4. Notificar a ambas partes
notificar_transferencia_aceptada(solicitud)
```

**Si RECHAZA**:
```python
solicitud.estado = 'rechazada'
solicitud.observaciones_respuesta = motivo_rechazo
solicitud.fecha_respuesta = timezone.now()
solicitud.save()

notificar_transferencia_rechazada(solicitud)
```

### Fase 3: Post-Transferencia

**Propietario Anterior**:
- Ahora es miembro regular del club
- Puede salir cuando quiera (botón "Salir" habilitado)
- Recibe notificación de transferencia completada

**Nuevo Propietario**:
- Ahora es propietario del club
- Gestiona membresías y configuración
- Ve badge "Propietario" en lugar de "Salir"

---

## 🎨 Interfaz de Usuario

### Vista: Gestionar Club (Propietario)

```html
<div class="card">
    <div class="card-header bg-warning">
        <h5>⚠️ Opciones de Salida</h5>
    </div>
    <div class="card-body">
        <p>Como propietario, no puedes salir directamente del club. Tienes dos opciones:</p>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card border-primary">
                    <div class="card-body">
                        <h6>🔄 Transferir Propiedad</h6>
                        <p>Transfiere la propiedad a un miembro activo del club.</p>
                        <a href="{% url 'transferir_propiedad_club' club.id %}" 
                           class="btn btn-primary">
                            Transferir Propiedad
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card border-danger">
                    <div class="card-body">
                        <h6>🗑️ Eliminar Club</h6>
                        <p>Solicita la eliminación del club a la federación.</p>
                        <a href="{% url 'eliminar_club' club.id %}" 
                           class="btn btn-danger">
                            Solicitar Eliminación
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Vista: Solicitud de Transferencia

```html
<form method="post">
    {% csrf_token %}
    
    <div class="mb-3">
        <label>Nuevo Propietario</label>
        <select name="nuevo_propietario_id" class="form-control" required>
            <option value="">Seleccione un miembro...</option>
            {% for membresia in miembros_activos %}
                <option value="{{ membresia.institucion.id }}">
                    {{ membresia.institucion.nombre }}
                </option>
            {% endfor %}
        </select>
    </div>
    
    <div class="mb-3">
        <label>Motivo de la Transferencia</label>
        <textarea name="motivo" class="form-control" rows="4" required></textarea>
    </div>
    
    <div class="mb-3">
        <label>Mensaje para el Nuevo Propietario</label>
        <textarea name="mensaje" class="form-control" rows="3"></textarea>
    </div>
    
    <button type="submit" class="btn btn-primary">Enviar Solicitud</button>
</form>
```

### Vista: Responder Transferencia

```html
<div class="card">
    <div class="card-header bg-info text-white">
        <h5>🔄 Solicitud de Transferencia de Propiedad</h5>
    </div>
    <div class="card-body">
        <h6>Club: {{ solicitud.club.nombre }}</h6>
        <p><strong>Propietario Actual:</strong> {{ solicitud.propietario_actual.nombre }}</p>
        <p><strong>Motivo:</strong> {{ solicitud.motivo }}</p>
        {% if solicitud.mensaje_nuevo_propietario %}
            <p><strong>Mensaje:</strong> {{ solicitud.mensaje_nuevo_propietario }}</p>
        {% endif %}
        
        <hr>
        
        <div class="row">
            <div class="col-md-6">
                <form method="post" action="{% url 'aceptar_transferencia' solicitud.id %}">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-success btn-block">
                        ✅ Aceptar Transferencia
                    </button>
                </form>
            </div>
            <div class="col-md-6">
                <button class="btn btn-danger btn-block" data-bs-toggle="modal" 
                        data-bs-target="#rechazarModal">
                    ❌ Rechazar Transferencia
                </button>
            </div>
        </div>
    </div>
</div>
```

---

## 🔔 Sistema de Notificaciones

### Notificación: Solicitud Enviada (Nuevo Propietario)

```
🔄 Solicitud de Transferencia de Propiedad

La institución "[Propietario Actual]" te ha propuesto como nuevo propietario 
del club "[Nombre Club]".

📝 Motivo: [Motivo proporcionado]

💬 Mensaje: [Mensaje opcional]

📊 Información del Club:
- Miembros actuales: X
- Líneas de investigación: [Lista]
- Fecha de fundación: [Fecha]

⚠️ Como propietario, serás responsable de:
- Gestionar membresías
- Aprobar/rechazar solicitudes
- Mantener el club activo

👉 Revisa la solicitud y decide si aceptas esta responsabilidad.
```

### Notificación: Transferencia Aceptada (Propietario Anterior)

```
✅ Transferencia de Propiedad Aceptada

La institución "[Nuevo Propietario]" ha aceptado la transferencia de propiedad 
del club "[Nombre Club]".

🎉 La transferencia se ha completado exitosamente.

📌 Cambios aplicados:
- Nuevo propietario: [Nuevo Propietario]
- Tu rol: Miembro regular
- Ahora puedes salir del club cuando lo desees

💡 Puedes seguir participando como miembro activo del club.
```

### Notificación: Transferencia Rechazada (Propietario Actual)

```
❌ Transferencia de Propiedad Rechazada

La institución "[Nuevo Propietario]" ha rechazado la transferencia de propiedad 
del club "[Nombre Club]".

📝 Motivo: [Motivo del rechazo]

💡 Puedes:
- Intentar con otro miembro activo
- Solicitar la eliminación del club a la federación
```

---

## 🔐 Seguridad y Validaciones

### Validaciones en Solicitud

```python
def transferir_propiedad_club(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    
    # 1. Verificar que es propietario
    if club.institucion_creadora != request.user.userprofile.institution:
        return error("No eres propietario")
    
    # 2. Verificar que club está activo y aprobado
    if club.status != 'aprobado' or not club.activo:
        return error("Club no está activo")
    
    # 3. Verificar que no hay transferencia pendiente
    if SolicitudTransferenciaClub.objects.filter(
        club=club, estado='pendiente'
    ).exists():
        return error("Ya hay una transferencia pendiente")
    
    # 4. Verificar que nuevo propietario es miembro activo
    if not MembresiaClu.objects.filter(
        club=club,
        institucion_id=nuevo_propietario_id,
        estado='aprobada'
    ).exists():
        return error("Debe ser miembro activo del club")
```

### Validaciones en Respuesta

```python
def responder_transferencia(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudTransferenciaClub, id=solicitud_id)
    
    # 1. Verificar que es el destinatario
    if solicitud.nuevo_propietario != request.user.userprofile.institution:
        return error("No eres el destinatario")
    
    # 2. Verificar que está pendiente
    if solicitud.estado != 'pendiente':
        return error("Solicitud ya fue procesada")
    
    # 3. Verificar que sigue siendo miembro activo
    if not MembresiaClu.objects.filter(
        club=solicitud.club,
        institucion=solicitud.nuevo_propietario,
        estado='aprobada'
    ).exists():
        return error("Ya no eres miembro del club")
```

---

## 📈 Ventajas de esta Arquitectura

### ✅ Beneficios

1. **Continuidad**: El club no queda huérfano
2. **Flexibilidad**: Propietario puede retirarse sin eliminar el club
3. **Transparencia**: Proceso claro con notificaciones
4. **Auditoría**: Historial completo de transferencias
5. **Seguridad**: Validaciones en múltiples capas
6. **UX**: Flujo intuitivo y profesional

### 📊 Comparación de Opciones

| Opción | Tiempo | Aprobación | Resultado |
|--------|--------|------------|-----------|
| **Transferir Propiedad** | Inmediato* | Nuevo propietario | Club continúa activo |
| **Eliminar Club** | Días | Federación | Club eliminado |

*Inmediato una vez que el nuevo propietario acepta

---

## 🚀 Implementación Recomendada

### Fase 1: Modelo y Migraciones (Prioritario)
- Crear modelo `SolicitudTransferenciaClub`
- Migración de base de datos
- Funciones de notificación

### Fase 2: Vistas y Lógica (Core)
- Vista: Solicitar transferencia
- Vista: Responder transferencia
- Vista: Listar transferencias pendientes
- Actualización de club tras aceptación

### Fase 3: Templates (UI)
- Template: Formulario de solicitud
- Template: Responder solicitud
- Template: Lista de transferencias
- Actualizar "Gestionar Club" con opciones

### Fase 4: Notificaciones (Comunicación)
- Notificación: Solicitud enviada
- Notificación: Transferencia aceptada
- Notificación: Transferencia rechazada

---

## 🎓 Mejores Prácticas Aplicadas

1. **Principio de Responsabilidad Única**: Cada modelo tiene un propósito claro
2. **Validación en Capas**: Frontend + Backend
3. **Auditoría Completa**: Historial de todas las acciones
4. **Notificaciones Proactivas**: Usuarios siempre informados
5. **Fail-Safe**: Previene estados inconsistentes
6. **UX Intuitiva**: Flujo claro y opciones visibles

---

**Recomendación**: Implementar Transferencia de Propiedad como **Fase 2** del sistema de clubes.

**Prioridad**: 🟡 **MEDIA-ALTA** (mejora significativa de UX y lógica de negocio)

**Esfuerzo Estimado**: 4-6 horas de desarrollo

**Impacto**: Alto - Resuelve caso edge crítico de forma profesional
