"""
Vistas avanzadas para Fase 4: Calificaciones, Eventos y Restauración
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    CalificacionClub,
    Club,
    ClubEvento,
    Evento,
    HistorialClub,
    Institucion,
)
from .notificaciones import crear_notificacion


@login_required
def calificar_club(request, club_id):
    """Permite a una institución calificar un club."""
    club = get_object_or_404(Club, id=club_id, activo=True, status="aprobado")
    
    # Verificar que el usuario tiene institución
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.institution:
        messages.error(request, "Debe estar asociado a una institución para calificar.")
        return redirect('detalle_club', club_id=club_id)
    
    institucion = request.user.userprofile.institution
    
    # Verificar que la institución es miembro del club
    if not club.membresias.filter(institucion=institucion, estado='miembro_activo').exists():
        messages.error(request, "Solo los miembros del club pueden calificarlo.")
        return redirect('detalle_club', club_id=club_id)
    
    if request.method == 'POST':
        puntuacion = int(request.POST.get('puntuacion'))
        resena = request.POST.get('resena', '').strip()
        
        # Crear o actualizar calificación
        calificacion, created = CalificacionClub.objects.update_or_create(
            club=club,
            institucion=institucion,
            defaults={'puntuacion': puntuacion, 'resena': resena}
        )
        
        if created:
            messages.success(request, "Calificación enviada exitosamente.")
        else:
            messages.success(request, "Calificación actualizada exitosamente.")
        
        return redirect('detalle_club', club_id=club_id)
    
    # Obtener calificación existente si hay
    calificacion_existente = CalificacionClub.objects.filter(
        club=club, institucion=institucion
    ).first()
    
    return render(request, 'registry/calificar_club.html', {
        'club': club,
        'calificacion_existente': calificacion_existente,
    })


@login_required
def vincular_club_evento(request, club_id):
    """Vincula un club a un evento."""
    club = get_object_or_404(Club, id=club_id, activo=True, status="aprobado")
    
    # Verificar permisos
    if not club.puede_editar(request.user):
        messages.error(request, "No tiene permisos para vincular este club a eventos.")
        return redirect('detalle_club', club_id=club_id)
    
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')
        rol = request.POST.get('rol', 'participante')
        
        evento = get_object_or_404(Evento, id=evento_id, activo=True)
        
        # Crear vinculación
        vinculacion, created = ClubEvento.objects.get_or_create(
            club=club,
            evento=evento,
            defaults={'rol': rol}
        )
        
        if created:
            messages.success(request, f"Club vinculado al evento '{evento.nombre}' exitosamente.")
        else:
            messages.info(request, "El club ya está vinculado a este evento.")
        
        return redirect('detalle_club', club_id=club_id)
    
    # Obtener eventos disponibles
    eventos_disponibles = Evento.objects.filter(
        activo=True,
        fecha__gte=timezone.now().date()
    ).exclude(
        clubes_vinculados__club=club
    )
    
    return render(request, 'registry/vincular_club_evento.html', {
        'club': club,
        'eventos_disponibles': eventos_disponibles,
    })


@login_required
def desvincular_club_evento(request, vinculacion_id):
    """Desvincula un club de un evento."""
    vinculacion = get_object_or_404(ClubEvento, id=vinculacion_id)
    
    # Verificar permisos
    if not vinculacion.club.puede_editar(request.user):
        messages.error(request, "No tiene permisos para desvincular este club.")
        return redirect('detalle_club', club_id=vinculacion.club.id)
    
    club_id = vinculacion.club.id
    evento_nombre = vinculacion.evento.nombre
    vinculacion.delete()
    
    messages.success(request, f"Club desvinculado del evento '{evento_nombre}'.")
    return redirect('detalle_club', club_id=club_id)


@login_required
def clubes_eliminados(request):
    """Lista de clubes eliminados (papelera de reciclaje) - Solo federación central."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type not in ['fed_central', 'superuser']:
        messages.error(request, "No tiene permisos para acceder a esta sección.")
        return redirect('dashboard')
    
    clubes = Club.objects.filter(eliminado=True).select_related(
        'institucion_creadora', 'eliminado_por'
    ).order_by('-fecha_eliminacion')
    
    return render(request, 'registry/clubes_eliminados.html', {
        'clubes': clubes,
    })


@login_required
def restaurar_club(request, club_id):
    """Restaura un club eliminado - Solo federación central."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type not in ['fed_central', 'superuser']:
        messages.error(request, "No tiene permisos para restaurar clubes.")
        return redirect('dashboard')
    
    club = get_object_or_404(Club, id=club_id, eliminado=True)
    
    if request.method == 'POST':
        # Restaurar club
        estado_anterior = 'eliminado'
        club.eliminado = False
        club.fecha_eliminacion = None
        club.motivo_eliminacion = ''
        club.eliminado_por = None
        club.activo = True
        club.save()
        
        # Registrar en historial
        HistorialClub.objects.create(
            club=club,
            usuario=request.user,
            estado_anterior=estado_anterior,
            estado_nuevo=club.status,
            observaciones=f"Club restaurado por {request.user.username}"
        )
        
        # Notificar a la institución creadora
        if club.institucion_creadora and club.institucion_creadora.usuario:
            crear_notificacion(
                destinatario=club.institucion_creadora.usuario,
                tipo='sistema',
                titulo='Club Restaurado',
                mensaje=f'El club "{club.nombre}" ha sido restaurado por la federación.',
                club=club
            )
        
        messages.success(request, f"Club '{club.nombre}' restaurado exitosamente.")
        return redirect('clubes_eliminados')
    
    return render(request, 'registry/restaurar_club.html', {
        'club': club,
    })


@login_required
def eliminar_permanente_club(request, club_id):
    """Elimina permanentemente un club de la papelera - Solo federación central."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type not in ['fed_central', 'superuser']:
        messages.error(request, "No tiene permisos para eliminar permanentemente clubes.")
        return redirect('dashboard')
    
    club = get_object_or_404(Club, id=club_id, eliminado=True)
    
    if request.method == 'POST':
        nombre_club = club.nombre
        club.delete()
        
        messages.success(request, f"Club '{nombre_club}' eliminado permanentemente.")
        return redirect('clubes_eliminados')
    
    return render(request, 'registry/eliminar_permanente_club.html', {
        'club': club,
    })
