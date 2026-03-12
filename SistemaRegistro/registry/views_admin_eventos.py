"""Vistas administrativas para gestión de eventos por fed_central.

Reglas de negocio para eventos:
- fed_central crea eventos: Quedan automáticamente aprobados y visibles para todas las instituciones
- Instituciones crean eventos: Quedan en borrador y deben enviarse a revisión para ser aprobados por fed_central
- Una vez aprobados, los eventos son visibles para todas las instituciones
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Evento


@staff_member_required
def admin_todos_eventos(request):
    """
    Vista unificada para gestión de TODOS los eventos.
    
    Muestra eventos agrupados por estado:
    - Pendientes: Eventos de instituciones esperando aprobación de fed_central
    - Aprobados: Eventos aprobados (tanto de fed_central como de instituciones)
    - Rechazados: Eventos rechazados
    - Borradores: Eventos en borrador (solo de instituciones)
    - Publicados: Eventos de fed_central (ya approved y publicados)
    
    Los eventos creados por fed_central aparecen directamente en "Aprobados".
    """
    # Obtener filtros del request
    filtro_estado = request.GET.get('estado')
    filtro_audiencia = request.GET.get('audiencia')
    filtro_tipo = request.GET.get('tipo')
    busqueda = request.GET.get('buscar', '').strip()
    
    # Query base
    eventos_query = Evento.objects.select_related(
        'institucion', 'club_organizador', 'estado', 'creado_por'
    )
    
    # Aplicar filtros
    if filtro_estado:
        eventos_query = eventos_query.filter(estado_evento=filtro_estado)
    if filtro_audiencia:
        eventos_query = eventos_query.filter(audiencia=filtro_audiencia)
    if filtro_tipo:
        eventos_query = eventos_query.filter(tipo_evento=filtro_tipo)
    if busqueda:
        eventos_query = eventos_query.filter(
            Q(nombre__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda)
        )
    
    # Eventos pendientes de aprobación (solo eventos de instituciones)
    eventos_pendientes = eventos_query.filter(
        estado_evento='pendiente'
    ).order_by('-fecha_creacion')
    
    # Eventos aprobados (incluye los de fed_central y los aprobados de instituciones)
    eventos_aprobados = eventos_query.filter(
        estado_evento='aprobado'
    ).order_by('-fecha')
    
    # Eventos rechazados
    eventos_rechazados = eventos_query.filter(
        estado_evento='rechazado'
    ).order_by('-fecha_creacion')
    
    # Eventos en borrador (solo de instituciones)
    eventos_borrador = eventos_query.filter(
        estado_evento='borrador'
    ).order_by('-fecha_creacion')
    
    # Eventos publicados por fed_central (estado aprobado + es_publico=True)
    eventos_fed_central = eventos_query.filter(
        estado_evento='aprobado', es_publico=True
    ).order_by('-fecha')
    
    # Estadísticas generales
    stats = {
        'total_pendientes': Evento.objects.filter(estado_evento='pendiente').count(),
        'total_aprobados': Evento.objects.filter(estado_evento='aprobado').count(),
        'total_rechazados': Evento.objects.filter(estado_evento='rechazado').count(),
        'total_borrador': Evento.objects.filter(estado_evento='borrador').count(),
        'total_fed_central': Evento.objects.filter(es_publico=True, estado_evento='aprobado').count(),
        'pendientes_publicos': eventos_pendientes.filter(audiencia='publica').count(),
        'pendientes_club': eventos_pendientes.filter(audiencia='club_exclusivo').count(),
        'pendientes_privados': eventos_pendientes.filter(audiencia='institucional_privado').count(),
    }
    
    # Obtener lista de todos los eventos para "TODOS LOS EVENTOS"
    todos_los_eventos = eventos_query.order_by('-fecha_creacion')
    
    context = {
        'eventos_pendientes': eventos_pendientes,
        'eventos_aprobados': eventos_aprobados,
        'eventos_rechazados': eventos_rechazados,
        'eventos_borrador': eventos_borrador,
        'eventos_fed_central': eventos_fed_central,
        'todos_los_eventos': todos_los_eventos,
        'stats': stats,
        'filtros': {
            'estado': filtro_estado,
            'audiencia': filtro_audiencia,
            'tipo': filtro_tipo,
            'buscar': busqueda,
        }
    }
    
    return render(request, 'registry/admin_todos_eventos.html', context)



@staff_member_required
def aprobar_evento(request, evento_id):
    """
    Aprobar cualquier tipo de evento (unificado).
    - Eventos de institución: cambian a 'aprobado' y se hacen visibles para todos
    - Eventos fed_central: ya están aprobados por defecto
    """
    evento = get_object_or_404(Evento, id=evento_id)
    
    if evento.estado_evento != 'pendiente':
        messages.error(request, "Solo se pueden aprobar eventos en estado pendiente.")
        return redirect('admin_todos_eventos')
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()
        
        with transaction.atomic():
            # Cambiar estado a aprobado
            evento.estado_evento = 'aprobado'
            evento.aprobado_por = request.user
            evento.observaciones_aprobacion = observaciones
            evento.fecha_aprobacion = timezone.now()
            
            # Si es evento institucional, hacerlo visible para todos
            if evento.tipo_evento == 'institucional':
                evento.es_publico = True
                evento.audiencia = 'publica'
            
            evento.save(update_fields=[
                'estado_evento', 'aprobado_por', 'observaciones_aprobacion', 
                'fecha_aprobacion', 'es_publico', 'audiencia'
            ])
            
            messages.success(
                request,
                f'✅ Evento "{evento.nombre}" aprobado exitosamente. '
                f'Ahora visible para: {evento.get_audiencia_display()}'
            )
    
    return redirect('admin_todos_eventos')


@staff_member_required
def rechazar_evento(request, evento_id):
    """
    Rechazar cualquier tipo de evento (unificado).
    - Evento vuelve a estado 'borrador' para que institución pueda editarlo
    """
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
            # Mantener es_publico = False para que no sea visible
            evento.es_publico = False
            evento.save(update_fields=['estado_evento', 'observaciones_aprobacion', 'es_publico'])
            
            messages.warning(
                request,
                f'❌ Evento "{evento.nombre}" rechazado. La institución puede editarlo y enviarlo nuevamente.'
            )
    
    return redirect('admin_todos_eventos')
