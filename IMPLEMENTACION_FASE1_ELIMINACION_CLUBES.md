# 🚀 IMPLEMENTACIÓN FASE 1: Sistema de Eliminación de Clubes

**Prioridad:** 🔴 CRÍTICA  
**Tiempo Estimado:** 7-10 horas  
**Funcionalidades:** Eliminación de Clubes + Notificaciones

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Paso 1: Migración de Base de Datos
- [ ] Crear migración para campos en Club
- [ ] Crear modelo SolicitudEliminacionClub
- [ ] Ejecutar migraciones
- [ ] Verificar en base de datos

### Paso 2: Backend (Vistas)
- [ ] Vista: eliminar_club
- [ ] Vista: revisar_solicitudes_eliminacion
- [ ] Vista: aprobar_eliminacion_club
- [ ] Vista: rechazar_eliminacion_club
- [ ] Función: enviar_notificacion_club

### Paso 3: URLs
- [ ] Configurar 4 URLs nuevas

### Paso 4: Templates
- [ ] club_eliminar.html
- [ ] revisar_solicitudes_eliminacion.html
- [ ] aprobar_eliminacion_club.html
- [ ] rechazar_eliminacion_club.html
- [ ] Templates de email (5)

### Paso 5: Integración
- [ ] Agregar botón "Eliminar" en clubes_lista.html
- [ ] Agregar enlace en menú de federación
- [ ] Actualizar filtros para excluir eliminados

### Paso 6: Testing
- [ ] Eliminar club en borrador
- [ ] Solicitar eliminación de club aprobado
- [ ] Aprobar solicitud de eliminación
- [ ] Rechazar solicitud de eliminación
- [ ] Verificar notificaciones por email

---

## 📝 PASO 1: MIGRACIÓN DE BASE DE DATOS

### 1.1 Crear archivo de migración

```bash
cd SistemaRegistro
python manage.py makemigrations registry --name agregar_sistema_eliminacion_clubes
```

### 1.2 Editar migración generada

**Archivo:** `SistemaRegistro/registry/migrations/0016_agregar_sistema_eliminacion_clubes.py`

```python
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('registry', '0015_club_mejorado'),
    ]

    operations = [
        # Agregar campos al modelo Club
        migrations.AddField(
            model_name='club',
            name='eliminado',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='club',
            name='fecha_eliminacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='club',
            name='motivo_eliminacion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='club',
            name='eliminado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='clubes_eliminados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Crear modelo SolicitudEliminacionClub
        migrations.CreateModel(
            name='SolicitudEliminacionClub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.TextField(verbose_name='Motivo de la solicitud')),
                ('estado', models.CharField(
                    choices=[
                        ('pendiente', 'Pendiente'),
                        ('aprobada', 'Aprobada'),
                        ('rechazada', 'Rechazada')
                    ],
                    default='pendiente',
                    max_length=20,
                    db_index=True
                )),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('fecha_respuesta', models.DateTimeField(blank=True, null=True)),
                ('observaciones_federacion', models.TextField(blank=True)),
                ('club', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='solicitudes_eliminacion',
                    to='registry.club'
                )),
                ('institucion_solicitante', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='registry.institucion'
                )),
                ('revisado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='solicitudes_eliminacion_revisadas',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Solicitud de Eliminación de Club',
                'verbose_name_plural': 'Solicitudes de Eliminación de Clubes',
                'ordering': ['-fecha_solicitud'],
            },
        ),
        
        # Agregar índice
        migrations.AddIndex(
            model_name='solicitudeliminacionclub',
            index=models.Index(fields=['estado', 'fecha_solicitud'], name='idx_sol_elim_estado'),
        ),
    ]
```

### 1.3 Ejecutar migración

```bash
python manage.py migrate
```

---

## 📝 PASO 2: ACTUALIZAR MODELO

**Archivo:** `SistemaRegistro/registry/models.py`

Agregar al final del archivo (después de la clase MembresiaClu):

```python
class SolicitudEliminacionClub(models.Model):
    """Modelo para gestionar solicitudes de eliminación de clubes aprobados."""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    club = models.ForeignKey(
        Club, 
        on_delete=models.CASCADE,
        related_name='solicitudes_eliminacion'
    )
    institucion_solicitante = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE
    )
    motivo = models.TextField(
        verbose_name="Motivo de la solicitud"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        db_index=True
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    observaciones_federacion = models.TextField(blank=True)
    revisado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_eliminacion_revisadas'
    )
    
    class Meta:
        verbose_name = "Solicitud de Eliminación de Club"
        verbose_name_plural = "Solicitudes de Eliminación de Clubes"
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['estado', 'fecha_solicitud'], name='idx_sol_elim_estado'),
        ]
    
    def __str__(self):
        return f"Solicitud eliminación: {self.club.nombre} ({self.estado})"
```

---

## 📝 PASO 3: VISTAS BACKEND

**Archivo:** `SistemaRegistro/registry/views_institucional.py`

Agregar al final del archivo:

```python
@login_required
def eliminar_club(request, club_id):
    """
    Elimina un club según su estado:
    - BORRADOR/RECHAZADO: Eliminación directa (hard delete)
    - APROBADO/PENDIENTE: Crea solicitud de eliminación
    """
    if (
        not hasattr(request.user, "userprofile")
        or request.user.userprofile.user_type != "institucional"
    ):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    club = get_object_or_404(Club, id=club_id)
    institucion = request.user.userprofile.institution
    
    # Verificar permisos
    if club.institucion_creadora != institucion:
        messages.error(request, "No tienes permiso para eliminar este club.")
        return redirect("clubes_lista")
    
    # Verificar si ya está eliminado
    if club.eliminado:
        messages.warning(request, "Este club ya está eliminado.")
        return redirect("clubes_lista")
    
    if request.method == "POST":
        if club.status in ["borrador", "rechazado"]:
            # CASO 1: Eliminación directa (hard delete)
            nombre = club.nombre
            club.delete()
            messages.success(request, f'Club "{nombre}" eliminado permanentemente.')
            return redirect("clubes_lista")
        
        elif club.status in ["aprobado", "pendiente", "en_revision"]:
            # CASO 2: Solicitud de eliminación
            motivo = request.POST.get("motivo", "").strip()
            
            if not motivo:
                messages.error(request, "Debes proporcionar un motivo para la eliminación.")
                return render(request, "registry/club_eliminar.html", {"club": club})
            
            # Verificar si ya existe una solicitud pendiente
            solicitud_existente = SolicitudEliminacionClub.objects.filter(
                club=club,
                estado="pendiente"
            ).exists()
            
            if solicitud_existente:
                messages.warning(
                    request,
                    "Ya existe una solicitud de eliminación pendiente para este club."
                )
                return redirect("clubes_lista")
            
            # Crear solicitud
            SolicitudEliminacionClub.objects.create(
                club=club,
                institucion_solicitante=institucion,
                motivo=motivo
            )
            
            messages.success(
                request,
                f'Solicitud de eliminación enviada a la federación para el club "{club.nombre}".'
            )
            return redirect("clubes_lista")
        
        else:
            messages.error(
                request,
                "No se puede eliminar un club en este estado."
            )
            return redirect("clubes_lista")
    
    # GET - Mostrar formulario
    context = {
        "club": club,
        "puede_eliminar_directo": club.status in ["borrador", "rechazado"],
        "requiere_aprobacion": club.status in ["aprobado", "pendiente", "en_revision"],
    }
    return render(request, "registry/club_eliminar.html", context)


@staff_member_required
def revisar_solicitudes_eliminacion(request):
    """Vista para que federación revise solicitudes de eliminación."""
    solicitudes_pendientes = (
        SolicitudEliminacionClub.objects.filter(estado="pendiente")
        .select_related("club", "institucion_solicitante")
        .order_by("-fecha_solicitud")
    )
    
    context = {
        "solicitudes_pendientes": solicitudes_pendientes,
    }
    return render(request, "registry/revisar_solicitudes_eliminacion.html", context)


@staff_member_required
def aprobar_eliminacion_club(request, solicitud_id):
    """Aprueba una solicitud de eliminación (soft delete)."""
    solicitud = get_object_or_404(SolicitudEliminacionClub, id=solicitud_id)
    
    if solicitud.estado != "pendiente":
        messages.error(request, "Esta solicitud ya fue procesada.")
        return redirect("revisar_solicitudes_eliminacion")
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Marcar solicitud como aprobada
                solicitud.estado = "aprobada"
                solicitud.fecha_respuesta = timezone.now()
                solicitud.revisado_por = request.user
                solicitud.save()
                
                # Soft delete del club
                club = solicitud.club
                club.eliminado = True
                club.fecha_eliminacion = timezone.now()
                club.eliminado_por = request.user
                club.motivo_eliminacion = solicitud.motivo
                club.activo = False
                club.save()
                
                messages.success(
                    request,
                    f'Club "{club.nombre}" eliminado correctamente.'
                )
        except Exception as e:
            messages.error(request, f"Error al eliminar club: {str(e)}")
        
        return redirect("revisar_solicitudes_eliminacion")
    
    context = {"solicitud": solicitud}
    return render(request, "registry/aprobar_eliminacion_club.html", context)


@staff_member_required
def rechazar_eliminacion_club(request, solicitud_id):
    """Rechaza una solicitud de eliminación."""
    solicitud = get_object_or_404(SolicitudEliminacionClub, id=solicitud_id)
    
    if solicitud.estado != "pendiente":
        messages.error(request, "Esta solicitud ya fue procesada.")
        return redirect("revisar_solicitudes_eliminacion")
    
    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()
        
        solicitud.estado = "rechazada"
        solicitud.fecha_respuesta = timezone.now()
        solicitud.revisado_por = request.user
        solicitud.observaciones_federacion = observaciones
        solicitud.save()
        
        messages.success(
            request,
            f'Solicitud de eliminación rechazada para el club "{solicitud.club.nombre}".'
        )
        return redirect("revisar_solicitudes_eliminacion")
    
    context = {"solicitud": solicitud}
    return render(request, "registry/rechazar_eliminacion_club.html", context)
```

Actualizar imports al inicio del archivo:

```python
from .models import (
    Club,
    Evento,
    Grupo,
    InscripcionGrupoEvento,
    MembresiaClu,
    Participante,
    SolicitudEliminacionClub,  # NUEVO
)
```

---

## 📝 PASO 4: ACTUALIZAR VISTAS EXISTENTES

**Archivo:** `SistemaRegistro/registry/views_institucional.py`

Actualizar las vistas para excluir clubes eliminados:

```python
@login_required
def clubes_lista(request):
    """Lista de clubes - Diferenciando creados, aprobados y disponibles."""
    # ... código existente ...
    
    # 1. MIS CLUBES CREADOS (todos los estados, excluir eliminados)
    mis_clubes_creados = Club.objects.filter(
        institucion_creadora=institucion,
        eliminado=False  # NUEVO
    ).order_by("-fecha_creacion")
    
    # 2. MIS CLUBES APROBADOS
    mis_clubes_aprobados = mis_clubes_creados.filter(
        status="aprobado",
        activo=True,
        eliminado=False  # NUEVO
    )
    
    # 3. CLUBES DISPONIBLES
    clubes_disponibles = (
        Club.objects.filter(
            activo=True,
            status="aprobado",
            eliminado=False,  # NUEVO
            estado_vinculacion__in=["abierto", "invitacion"],
        )
        .exclude(institucion_creadora=institucion)
        .annotate(
            num_membresias=Count("membresias", filter=Q(membresias__estado="aprobada"))
        )
    )
    
    # ... resto del código ...
```

Hacer lo mismo en `directorio_clubes_aprobados`:

```python
@login_required
def directorio_clubes_aprobados(request):
    """Directorio público de todos los clubes aprobados."""
    # ... código existente ...
    
    clubes_aprobados = (
        Club.objects.filter(
            status="aprobado",
            activo=True,
            eliminado=False  # NUEVO
        )
        .select_related("institucion_creadora")
        .annotate(
            num_membresias=Count("membresias", filter=Q(membresias__estado="aprobada"))
        )
        .order_by("-fecha_aprobacion")
    )
    
    # ... resto del código ...
```

---

## 📝 PASO 5: URLS

**Archivo:** `SistemaRegistro/registry/urls.py`

Agregar después de las URLs de clubes existentes:

```python
urlpatterns = [
    # ... URLs existentes ...
    
    # Eliminación de clubes
    path(
        "clubes/<int:club_id>/eliminar/",
        views_institucional.eliminar_club,
        name="eliminar_club",
    ),
    
    # Federación - Solicitudes de eliminación
    path(
        "admin/clubes/solicitudes-eliminacion/",
        views_institucional.revisar_solicitudes_eliminacion,
        name="revisar_solicitudes_eliminacion",
    ),
    path(
        "admin/clubes/solicitudes-eliminacion/<int:solicitud_id>/aprobar/",
        views_institucional.aprobar_eliminacion_club,
        name="aprobar_eliminacion_club",
    ),
    path(
        "admin/clubes/solicitudes-eliminacion/<int:solicitud_id>/rechazar/",
        views_institucional.rechazar_eliminacion_club,
        name="rechazar_eliminacion_club",
    ),
]
```

---

## 📝 PASO 6: TEMPLATES

Continuará en siguiente mensaje debido a límite de caracteres...
