"""Vistas administrativas para gestión de eventos por fed_central."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect

from .models import Evento


@staff_member_required
def admin_todos_eventos(request):
    """
    Vista unificada para gestión de TODOS los eventos.
    Agrupa por estado y audiencia.
    """
    # Todos los eventos pendientes de aprobación
    eventos_pendientes = Evento.objects.filter(
        estado_evento='pendiente'
    ).select_related(
        'institucion', 'club_organizador', 'estado', 'creado_por'
    ).order_by('-fecha_creacion')
    
    # Eventos aprobados
    eventos_aprobados = Evento.objects.filter(
        estado_evento='aprobado'
    ).select_related(
        'institucion', 'club_organizador', 'estado', 'creado_por'
    ).order_by('-fecha_creacion')
    
    # Eventos rechazados
    eventos_rechazados = Evento.objects.filter(
        estado_evento='rechazado'
    ).select_related(
        'institucion', 'club_organizador', 'estado', 'creado_por'
    ).order_by('-fecha_creacion')
    
    # Estadísticas
    stats = {
        'total_pendientes': eventos_pendientes.count(),
        'total_aprobados': eventos_aprobados.count(),
        'total_rechazados': eventos_rechazados.count(),
        'pendientes_publicos': eventos_pendientes.filter(audiencia='publica').count(),
        'pendientes_club': eventos_pendientes.filter(audiencia='club_exclusivo').count(),
        'pendientes_privados': eventos_pendientes.filter(audiencia='institucional_privado').count(),
    }
    
    context = {
        'eventos_pendientes': eventos_pendientes,
        'eventos_aprobados': eventos_aprobados,
        'eventos_rechazados': eventos_rechazados,
        'stats': stats,
    }
    
    return render(request, 'registry/admin_todos_eventos.html', context)



@staff_member_required
def aprobar_evento(request, evento_id):
    """Aprobar cualquier tipo de evento (unificado)."""
    evento = get_object_or_404(Evento, id=evento_id)
    
    if evento.estado_evento != 'pendiente':
        messages.error(request, "Solo se pueden aprobar eventos en estado pendiente.")
        return redirect('admin_todos_eventos')
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()
        
        with transaction.atomic():
            evento.estado_evento = 'aprobado'
            evento.aprobado_por = request.user
            evento.observaciones_aprobacion = observaciones
            evento.save(update_fields=['estado_evento', 'aprobado_por', 'observaciones_aprobacion'])
            
            messages.success(
                request,
                f'✅ Evento "{evento.nombre}" aprobado. Visible para: {evento.get_audiencia_display()}'
            )
    
    return redirect('admin_todos_eventos')


@staff_member_required
def rechazar_evento(request, evento_id):
    """Rechazar cualquier tipo de evento (unificado)."""
    evento = get_object_or_404(Evento, id=evento_id)
    
    if evento.estado_evento != 'pendiente':
        messages.error(request, "Solo se pueden rechazar eventos en estado pendiente.")
        return redirect('admin_todos_eventos')
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()
        
        if not observaciones:
            messages.error(request, "Debes especificar el motivo del rechazo.")
            return redirect('admin_todos_eventos')
        
        with transaction.atomic():
            evento.estado_evento = 'rechazado'
            evento.observaciones_aprobacion = observaciones
            evento.save(update_fields=['estado_evento', 'observaciones_aprobacion'])
            
            messages.warning(
                request,
                f'❌ Evento "{evento.nombre}" rechazado'
            )
    
    return redirect('admin_todos_eventos')
