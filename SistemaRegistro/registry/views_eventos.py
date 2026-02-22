"""Vistas para gestión de eventos de club."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Club, Evento, Grupo, InscripcionGrupoEvento


@login_required
def crear_evento_club(request, club_id):
    """Crear evento de club (solo propietario del club)."""
    club = get_object_or_404(Club, id=club_id)
    
    # Validar que el usuario es propietario del club
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect('dashboard')
    
    institucion = request.user.userprofile.institution
    if club.institucion_creadora != institucion:
        messages.error(request, "No tienes permiso para crear eventos de este club.")
        return redirect('detalle_club', club_id=club.id)
    
    # Validar que el club esté aprobado
    if club.status != 'aprobado':
        messages.error(request, "Solo clubes aprobados pueden crear eventos.")
        return redirect('detalle_club', club_id=club.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                from registry.models import Estado, Municipio, Parroquia
                
                estado_id = request.POST.get('estado')
                municipio_id = request.POST.get('municipio')
                parroquia_id = request.POST.get('parroquia')
                direccion = request.POST.get('direccion', '')
                
                estado_obj = Estado.objects.get(id=estado_id) if estado_id else None
                municipio_obj = Municipio.objects.get(id=municipio_id) if municipio_id else None
                parroquia_obj = Parroquia.objects.get(id=parroquia_id) if parroquia_id else None
                
                ubicacion_completa = direccion
                if parroquia_obj:
                    ubicacion_completa = f"{direccion}, {parroquia_obj.nombre}"
                elif municipio_obj:
                    ubicacion_completa = f"{direccion}, {municipio_obj.nombre}"
                elif estado_obj:
                    ubicacion_completa = f"{direccion}, {estado_obj.nombre}"
                
                evento = Evento.objects.create(
                    nombre=request.POST.get('nombre'),
                    tipo=request.POST.get('categoria', 'competencia'),
                    categoria=request.POST.get('categoria', ''),
                    descripcion=request.POST.get('descripcion', ''),
                    fecha=request.POST.get('fecha'),
                    modalidad=request.POST.get('modalidad', 'presencial'),
                    ubicacion=ubicacion_completa,
                    estado=estado_obj,
                    municipio=municipio_obj,
                    parroquia=parroquia_obj,
                    direccion=direccion,
                    capacidad_maxima=request.POST.get('capacidad_maxima') or None,
                    requisitos=request.POST.get('requisitos', ''),
                    tipo_evento='club',
                    club_organizador=club,
                    creado_por=request.user,
                    estado_evento='borrador',
                    activo=True
                )
                
                messages.success(
                    request,
                    f'Evento "{evento.nombre}" creado exitosamente en estado BORRADOR. '
                    'Envíalo a revisión cuando esté listo.'
                )
                return redirect('eventos_club', club_id=club.id)
        except Exception as e:
            messages.error(request, f"Error al crear evento: {str(e)}")
    
    # Obtener datos para el formulario
    from registry.models import Estado
    from datetime import date
    
    estados = Estado.objects.all().order_by('nombre')
    hoy = date.today().isoformat()
    
    # Obtener estado del club (si tiene)
    estado_club = None
    if club.institucion_creadora and hasattr(club.institucion_creadora, 'estado'):
        estado_club = club.institucion_creadora.estado
    
    # Categorías predefinidas
    categorias = [
        "Competencia",
        "Taller",
        "Seminario",
        "Conferencia",
        "Exhibición",
        "Hackathon",
        "Feria",
        "Encuentro",
        "Capacitación",
        "Otro",
    ]
    
    context = {
        'club': club,
        'tipos': Evento.TIPO_CHOICES,
        'modalidades': Evento.MODALIDAD_CHOICES,
        'estados': estados,
        'hoy': hoy,
        'estado_club': estado_club,
        'categorias': categorias,
        'valores_previos': {},
    }
    return render(request, 'registry/evento_club_crear_nuevo.html', context)


@login_required
def listar_eventos_club(request, club_id):
    """Listar eventos de un club."""
    club = get_object_or_404(Club, id=club_id)
    
    # Validar acceso
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect('dashboard')
    
    user_type = request.user.userprofile.user_type
    institucion = request.user.userprofile.institution
    
    # Federación puede ver todos
    if user_type in ['fed_central', 'fed_regional', 'superuser']:
        eventos = club.eventos.all()
    # Propietario del club ve todos sus eventos
    elif club.institucion_creadora == institucion:
        eventos = club.eventos.all()
    # Miembros del club solo ven eventos aprobados
    else:
        es_miembro = club.membresias.filter(
            institucion=institucion,
            estado='aprobada'
        ).exists()
        
        if es_miembro:
            eventos = club.eventos.filter(estado_evento='aprobado')
        else:
            messages.error(request, "No tienes acceso a los eventos de este club.")
            return redirect('detalle_club', club_id=club.id)
    
    eventos = eventos.select_related('creado_por').order_by('-fecha')
    
    context = {
        'club': club,
        'eventos': eventos,
        'es_propietario': club.institucion_creadora == institucion,
    }
    return render(request, 'registry/evento_club_lista.html', context)


@login_required
def enviar_evento_revision(request, evento_id):
    """Enviar evento de club a revisión."""
    evento = get_object_or_404(Evento, id=evento_id, tipo_evento='club')
    
    # Validar permisos
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect('dashboard')
    
    institucion = request.user.userprofile.institution
    if evento.club_organizador.institucion_creadora != institucion:
        messages.error(request, "No tienes permiso para modificar este evento.")
        return redirect('eventos_club', club_id=evento.club_organizador.id)
    
    # Validar estado
    if evento.estado_evento not in ['borrador', 'rechazado']:
        messages.warning(
            request,
            f"El evento ya está en revisión o aprobado. Estado: {evento.get_estado_evento_display()}"
        )
        return redirect('eventos_club', club_id=evento.club_organizador.id)
    
    if request.method == 'POST':
        evento.estado_evento = 'pendiente'
        evento.save(update_fields=['estado_evento'])
        
        messages.success(
            request,
            f'Evento "{evento.nombre}" enviado a revisión correctamente.'
        )
        return redirect('eventos_club', club_id=evento.club_organizador.id)
    
    context = {
        'evento': evento,
        'es_reenvio': evento.estado_evento == 'rechazado',
    }
    return render(request, 'registry/evento_club_enviar_revision.html', context)


@staff_member_required
def revisar_eventos_club(request):
    """Vista para que federación revise eventos de club pendientes."""
    eventos_pendientes = Evento.objects.pendientes_aprobacion().select_related(
        'club_organizador', 'creado_por'
    ).order_by('-fecha_creacion')
    
    context = {
        'eventos_pendientes': eventos_pendientes,
    }
    return render(request, 'registry/revisar_eventos_club.html', context)


@staff_member_required
def aprobar_evento_club(request, evento_id):
    """Aprobar evento de club."""
    evento = get_object_or_404(Evento, id=evento_id, tipo_evento='club')
    
    if evento.estado_evento != 'pendiente':
        messages.error(request, "Este evento no puede ser aprobado en su estado actual.")
        return redirect('revisar_eventos_club')
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()
        
        if not observaciones:
            messages.error(request, "Debes agregar un comentario de aprobación.")
            return render(request, 'registry/aprobar_evento_club.html', {'evento': evento})
        
        try:
            with transaction.atomic():
                evento.estado_evento = 'aprobado'
                evento.fecha_aprobacion = timezone.now()
                evento.aprobado_por = request.user
                evento.observaciones_aprobacion = observaciones
                evento.save(update_fields=[
                    'estado_evento', 'fecha_aprobacion', 'aprobado_por', 'observaciones_aprobacion'
                ])
                
                messages.success(
                    request,
                    f'Evento "{evento.nombre}" ha sido APROBADO. '
                    'El club puede comenzar a recibir inscripciones.'
                )
        except Exception as e:
            messages.error(request, f"Error al aprobar evento: {str(e)}")
            return redirect('revisar_eventos_club')
        
        return redirect('revisar_eventos_club')
    
    context = {'evento': evento}
    return render(request, 'registry/aprobar_evento_club.html', context)


@staff_member_required
def rechazar_evento_club(request, evento_id):
    """Rechazar evento de club."""
    evento = get_object_or_404(Evento, id=evento_id, tipo_evento='club')
    
    if evento.estado_evento != 'pendiente':
        messages.error(request, "Este evento no puede ser rechazado en su estado actual.")
        return redirect('revisar_eventos_club')
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()
        
        if not observaciones:
            messages.error(request, "Debes especificar el motivo del rechazo.")
            return render(request, 'registry/rechazar_evento_club.html', {'evento': evento})
        
        evento.estado_evento = 'rechazado'
        evento.observaciones_aprobacion = observaciones
        evento.save(update_fields=['estado_evento', 'observaciones_aprobacion'])
        
        messages.success(request, f'Evento "{evento.nombre}" ha sido RECHAZADO.')
        return redirect('revisar_eventos_club')
    
    context = {'evento': evento}
    return render(request, 'registry/rechazar_evento_club.html', context)


@login_required
def detalle_evento_club(request, evento_id):
    """Ver detalle de un evento de club."""
    evento = get_object_or_404(
        Evento.objects.select_related(
            'club_organizador', 
            'creado_por',
            'creado_por__userprofile__institution'
        ),
        id=evento_id,
        tipo_evento='club'
    )
    
    # Validar acceso
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect('dashboard')
    
    user_type = request.user.userprofile.user_type
    institucion = request.user.userprofile.institution
    
    # Federación puede ver todos
    puede_ver = user_type in ['fed_central', 'fed_regional', 'superuser']
    
    # Propietario del club puede ver todos sus eventos
    if not puede_ver:
        puede_ver = evento.club_organizador.institucion_creadora == institucion
    
    # Miembros del club solo ven eventos aprobados
    if not puede_ver and evento.estado_evento == 'aprobado':
        puede_ver = evento.club_organizador.membresias.filter(
            institucion=institucion,
            estado='aprobada'
        ).exists()
    
    if not puede_ver:
        messages.error(request, "No tienes acceso a este evento.")
        return redirect('dashboard')
    
    # Obtener inscripciones
    inscripciones = evento.inscripciones_grupo.filter(
        activo=True
    ).select_related('grupo').order_by('-fecha_inscripcion')
    
    # Verificar si el usuario puede inscribir grupos
    puede_inscribir = False
    if evento.puede_inscribirse:
        puede_inscribir = evento.club_organizador.membresias.filter(
            institucion=institucion,
            estado='aprobada'
        ).exists()
    
    context = {
        'evento': evento,
        'inscripciones': inscripciones,
        'puede_inscribir': puede_inscribir,
        'es_propietario': evento.club_organizador.institucion_creadora == institucion,
    }
    return render(request, 'registry/evento_club_detalle.html', context)


@login_required
def inscribir_grupo_evento_club(request, evento_id):
    """Inscribir grupo a evento de club."""
    evento = get_object_or_404(Evento, id=evento_id, tipo_evento='club')
    
    # Validar que el evento acepta inscripciones
    if not evento.puede_inscribirse:
        messages.error(request, "Este evento no acepta inscripciones en este momento.")
        return redirect('detalle_evento_club', evento_id=evento.id)
    
    # Validar que el usuario es miembro del club
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect('dashboard')
    
    institucion = request.user.userprofile.institution
    es_miembro = evento.club_organizador.membresias.filter(
        institucion=institucion,
        estado='aprobada'
    ).exists()
    
    if not es_miembro:
        messages.error(
            request,
            f"Solo instituciones miembros del club '{evento.club_organizador.nombre}' "
            "pueden inscribir grupos a este evento."
        )
        return redirect('detalle_evento_club', evento_id=evento.id)
    
    if request.method == 'POST':
        grupo_id = request.POST.get('grupo_id')
        rol = request.POST.get('rol_participacion', 'participante')
        
        grupo = get_object_or_404(Grupo, id=grupo_id, usuario_creador=request.user)
        
        # Validar que el grupo esté editable
        if grupo.estado_grupo != 'editable':
            messages.error(request, "Solo se pueden inscribir grupos en estado editable.")
            return redirect('detalle_evento_club', evento_id=evento.id)
        
        # Validar que no esté ya inscrito
        if InscripcionGrupoEvento.objects.filter(evento=evento, grupo=grupo).exists():
            messages.warning(request, "Este grupo ya está inscrito en el evento.")
            return redirect('detalle_evento_club', evento_id=evento.id)
        
        try:
            with transaction.atomic():
                InscripcionGrupoEvento.objects.create(
                    evento=evento,
                    grupo=grupo,
                    rol_participacion=rol
                )
                
                # Cambiar estado del grupo a inscrito
                grupo.estado_grupo = 'inscrito'
                grupo.evento = evento
                grupo.save(update_fields=['estado_grupo', 'evento'])
                
                messages.success(
                    request,
                    f'Grupo "{grupo.nombre}" inscrito exitosamente al evento.'
                )
        except Exception as e:
            messages.error(request, f"Error al inscribir grupo: {str(e)}")
        
        return redirect('detalle_evento_club', evento_id=evento.id)
    
    # GET - Mostrar formulario
    grupos_editables = Grupo.objects.filter(
        usuario_creador=request.user,
        estado_grupo='editable'
    )
    
    context = {
        'evento': evento,
        'grupos': grupos_editables,
        'roles': InscripcionGrupoEvento.ROL_CHOICES,
    }
    return render(request, 'registry/inscribir_grupo_evento_club.html', context)
