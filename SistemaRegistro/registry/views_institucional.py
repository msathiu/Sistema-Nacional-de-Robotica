"""Vistas para el módulo institucional de gestión de grupos, eventos y clubes."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    Club,
    Evento,
    Grupo,
    InscripcionGrupoEvento,
    MembresiaClu,
    Participante,
    ParticipanteInstitucion,
    SolicitudEliminacionClub,
    Notificacion,
    HistorialClub,
    ComentarioClub,
)
from .notificaciones import (
    notificar_solicitud_eliminacion,
    notificar_eliminacion_aprobada,
    notificar_eliminacion_rechazada,
    notificar_salida_club,
    notificar_club_rechazado,
)
from .services import AdmissionService


@login_required
def grupos_institucion(request):
    """Lista todos los grupos de la institución."""
    if request.user.userprofile.user_type != "institucional":
        return redirect("dashboard")

    institucion = request.user.userprofile.institution
    grupos = (
        Grupo.objects.filter(usuario_creador=request.user)
        .annotate(num_participantes=Count("participantes"))
        .order_by("-fecha_registro")
    )

    context = {
        "grupos": grupos,
        "total_grupos": grupos.count(),
    }
    return render(request, "registry/grupos_lista.html", context)


@login_required
def editar_grupo(request, grupo_id):
    """Editar un grupo existente."""
    grupo = get_object_or_404(Grupo, id=grupo_id, usuario_creador=request.user)

    # Solo se puede editar si está en estado 'editable'
    if grupo.estado_grupo != "editable":
        messages.warning(request, "Este grupo no puede ser editado.")
        return redirect("grupos_institucion")

    if request.method == "POST":
        try:
            grupo.nombre = request.POST.get("nombre")
            grupo.criterio = request.POST.get("criterio")
            grupo.tutor_nombre = request.POST.get("tutor_nombre")
            grupo.tutor_apellidos = request.POST.get("tutor_apellidos")
            grupo.tutor_cedula = request.POST.get("tutor_cedula")
            grupo.tutor_telefono = request.POST.get("tutor_telefono")
            grupo.save()

            # Actualizar participantes
            participantes_ids = request.POST.getlist("participantes[]")
            # Filtrar IDs vacíos y validar que sean numéricos
            participantes_ids_validos = [
                int(pid) for pid in participantes_ids 
                if pid and pid.strip() and pid.strip().isdigit()
            ]
            grupo.participantes.set(participantes_ids_validos)

            messages.success(request, "Grupo actualizado exitosamente.")
            return redirect("grupos_institucion")
        except Exception as e:
            messages.error(request, f"Error al actualizar: {str(e)}")

    institucion = request.user.userprofile.institution
    # Obtener participantes vinculados a la institución a través de ParticipanteInstitucion
    participantes = Participante.objects.filter(
        vinculaciones__institucion=institucion,
        vinculaciones__status='activo'
    ).distinct()

    context = {
        "grupo": grupo,
        "participantes": participantes,
        "criterios": Grupo.CRITERIO_CHOICES,
    }
    return render(request, "registry/grupo_editar.html", context)


@login_required
def ver_grupo(request, grupo_id):
    """Ver detalles de un grupo."""
    grupo = get_object_or_404(Grupo, id=grupo_id, usuario_creador=request.user)

    context = {
        "grupo": grupo,
        "participantes": grupo.participantes.all(),
        "inscripciones": grupo.inscripciones.all(),
    }
    return render(request, "registry/grupo_detalle.html", context)


@login_required
def eliminar_grupo(request, grupo_id):
    """Eliminar un grupo (solo si está editable)."""
    if request.method == "POST":
        grupo = get_object_or_404(Grupo, id=grupo_id, usuario_creador=request.user)

        if grupo.estado_grupo != "editable":
            messages.error(
                request, "No se puede eliminar un grupo inscrito o bloqueado."
            )
        else:
            nombre = grupo.nombre
            grupo.delete()
            messages.success(request, f'Grupo "{nombre}" eliminado.')

    return redirect("grupos_institucion")


@login_required
def eventos_disponibles_institucion(request):
    """Lista de eventos disponibles para inscripción."""
    if request.user.userprofile.user_type != "institucional":
        return redirect("dashboard")

    hoy = timezone.now().date()
    eventos = Evento.objects.filter(activo=True, fecha__gte=hoy).order_by("fecha")

    context = {
        "eventos": eventos,
    }
    return render(request, "registry/eventos_disponibles.html", context)


@login_required
def inscribir_grupo_evento(request, evento_id):
    """Inscribir un grupo a un evento."""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # Los eventos deben estarapproved o abiertos para permitir inscripciones
    # Esta es la lógica del modelo de eventos dondefed_central aprueba eventos
    if evento.estado_evento not in ["abierto", "aprobado", "publicado"]:
        messages.error(request, "Este evento no está disponible para inscripciones.")
        return redirect("eventos_disponibles_institucion")

    if request.method == "POST":
        grupo_id = request.POST.get("grupo_id")
        rol = request.POST.get("rol_participacion")

        grupo = get_object_or_404(Grupo, id=grupo_id, usuario_creador=request.user)

        # Validar que el grupo esté editable
        if grupo.estado_grupo != "editable":
            messages.error(
                request, "Solo se pueden inscribir grupos en estado editable."
            )
            return redirect("eventos_disponibles_institucion")

        # Validar que no esté ya inscrito
        if InscripcionGrupoEvento.objects.filter(evento=evento, grupo=grupo).exists():
            messages.warning(request, "Este grupo ya está inscrito en el evento.")
            return redirect("eventos_disponibles_institucion")

        try:
            with transaction.atomic():
                # Crear inscripción
                InscripcionGrupoEvento.objects.create(
                    evento=evento, grupo=grupo, rol_participacion=rol
                )

                # Cambiar estado del grupo a 'inscrito'
                grupo.estado_grupo = "inscrito"
                grupo.evento = evento
                grupo.save()

                messages.success(
                    request, f'Grupo "{grupo.nombre}" inscrito exitosamente.'
                )
        except Exception as e:
            messages.error(request, f"Error al inscribir: {str(e)}")

        return redirect("eventos_disponibles_institucion")

    # GET - Mostrar modal
    grupos_editables = Grupo.objects.filter(
        usuario_creador=request.user, estado_grupo="editable"
    )

    context = {
        "evento": evento,
        "grupos": grupos_editables,
        "roles": InscripcionGrupoEvento.ROL_CHOICES,
    }
    return render(request, "registry/inscribir_grupo.html", context)


@login_required
def clubes_lista(request):
    """Lista de clubes - Diferenciando creados, aprobados y disponibles."""
    # Verificar que es usuario institucional o federación
    if not hasattr(request.user, "userprofile"):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    user_type = request.user.userprofile.user_type
    if user_type not in ["institucional", "fed_central", "fed_regional", "superuser"]:
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")

    # Si es federación regional o superuser, redirigir a revisar clubes
    if user_type in ["fed_regional", "superuser"]:
        return redirect("revisar_clubes")
    
    # fed_central puede crear clubes, mostrar su vista especial
    if user_type == "fed_central":
        # Clubes creados por fed_central (sin institución creadora)
        mis_clubes_creados = Club.objects.filter(
            institucion_creadora__isnull=True,
            eliminado=False
        ).order_by("-fecha_creacion")
        
        # Todos los clubes aprobados para visualización
        clubes_aprobados = Club.objects.filter(
            status="aprobado",
            activo=True,
            eliminado=False
        ).order_by("-fecha_aprobacion")
        
        context = {
            "mis_clubes_creados": mis_clubes_creados,
            "clubes_aprobados": clubes_aprobados,
            "total_creados": mis_clubes_creados.count(),
            "total_aprobados": clubes_aprobados.count(),
            "es_fed_central": True,
        }
        return render(request, "registry/clubes_lista.html", context)
    
    institucion = request.user.userprofile.institution

    # 1. MIS CLUBES CREADOS (solo NO eliminados)
    mis_clubes_creados = Club.objects.filter(
        institucion_creadora=institucion,
        eliminado=False  # ✅ FASE 1: Filtrar clubes eliminados
    ).order_by("-fecha_creacion")

    # 2. MIS CLUBES APROBADOS (solo los aprobados de mi institución)
    mis_clubes_aprobados = mis_clubes_creados.filter(
        status="aprobado",
        activo=True
    )

    # 3. CLUBES DISPONIBLES (aprobados de OTRAS instituciones para postular)
    from django.db.models import Subquery, OuterRef
    
    clubes_disponibles = (
        Club.objects.filter(
            activo=True,
            status="aprobado",
            eliminado=False,  # ✅ FASE 1: Filtrar clubes eliminados
            estado_vinculacion__in=["abierto", "invitacion"],
        )
        .exclude(institucion_creadora=institucion)
        .annotate(
            num_membresias=Count("membresias", filter=Q(membresias__estado="miembro_activo")),
            # Anotar el estado de membresía del usuario actual
            mi_estado_membresia=Subquery(
                MembresiaClu.objects.filter(
                    club=OuterRef('pk'),
                    institucion=institucion
                ).values('estado')[:1]
            )
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


@login_required
def crear_club(request):
    """Crear un nuevo club - Se guarda como BORRADOR inicialmente."""
    if not hasattr(request.user, "userprofile"):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    user_type = request.user.userprofile.user_type
    
    # Permitir a institucionales y fed_central
    if user_type not in ["institucional", "fed_central"]:
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")

    if request.method == "POST":
        from registry.forms import ClubForm
        form = ClubForm(request.POST)
        
        if form.is_valid():
            try:
                club = form.save(commit=False)
                
                # Si es fed_central, el club es público y aprobado automáticamente
                if user_type == "fed_central":
                    club.institucion_creadora = None  # Club de federación
                    club.coordinador = request.user
                    club.status = "aprobado"  # Aprobado automáticamente
                    club.fecha_aprobacion = timezone.now()
                else:
                    # Institucional: flujo normal
                    institucion = request.user.userprofile.institution
                    club.institucion_creadora = institucion
                    club.coordinador = request.user
                    club.status = "borrador"
                
                club.save()
                
                # Ahora guardar las líneas manualmente
                club.club_lineas.all().delete()
                from registry.models import ClubLineaInvestigacion
                
                lineas = [
                    (form.cleaned_data.get('linea_investigacion_1'), 'principal', 1),
                    (form.cleaned_data.get('linea_investigacion_2'), 'soporte', 2),
                    (form.cleaned_data.get('linea_investigacion_3'), 'afines', 3),
                ]
                
                for linea, tipo, orden in lineas:
                    if linea:
                        ClubLineaInvestigacion.objects.create(
                            club=club,
                            linea=linea,
                            tipo_linea=tipo,
                            orden=orden
                        )
                
                # Mensaje según tipo de usuario
                if user_type == "fed_central":
                    messages.success(
                        request,
                        f'Club "{club.nombre}" creado exitosamente y APROBADO automáticamente. '
                        f'Las instituciones pueden postularse ahora.'
                    )
                else:
                    messages.success(
                        request,
                        f'Club "{club.nombre}" creado exitosamente en estado BORRADOR. '
                        f'Complete los datos y envíe a revisión.'
                    )
                return redirect("clubes_lista")
            except Exception as e:
                messages.error(request, f"Error al crear club: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        from registry.forms import ClubForm
        form = ClubForm()

    context = {
        "form": form,
        "estados_vinculacion": Club.ESTADO_VINCULACION_CHOICES,
        "es_fed_central": user_type == "fed_central",
    }
    return render(request, "registry/club_crear.html", context)


@login_required
def enviar_club_revision(request, club_id):
    """Envía un club de borrador/rechazado a pendiente de revisión con límite de intentos."""
    if (
        not hasattr(request.user, "userprofile")
        or request.user.userprofile.user_type != "institucional"
    ):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")

    club = get_object_or_404(Club, id=club_id)
    institucion = request.user.userprofile.institution

    # Verificar que el club pertenece a la institución
    if club.institucion_creadora != institucion:
        messages.error(request, "No tienes permiso para modificar este club.")
        return redirect("clubes_lista")
    
    # ✅ FASE 2: Validar que el club no esté eliminado
    if club.eliminado:
        messages.error(
            request,
            "No puedes enviar a revisión un club eliminado. Contacta a la federación si necesitas asistencia."
        )
        return redirect("clubes_lista")

    # Permitir envío desde borrador O rechazado
    if club.status not in ["borrador", "rechazado"]:
        messages.warning(
            request,
            f"El club ya está en revisión o ha sido aprobado. Estado actual: {club.get_status_display()}",
        )
        return redirect("clubes_lista")

    # FASE 2.1: Límite de intentos de reenvío (3 máximo)
    MAX_REENVIOS = 3
    num_reenvios = club.contar_reenvios()
    
    if club.status == "rechazado" and num_reenvios >= MAX_REENVIOS:
        messages.error(
            request,
            f"Has alcanzado el límite de {MAX_REENVIOS} reenvíos para este club. "
            "Por favor, contacta a la federación para asistencia adicional."
        )
        return redirect("clubes_lista")

    if request.method == "POST":
        # FASE 2.2: Validar checklist si es reenvío
        if club.status == "rechazado":
            checklist_items = [
                'correccion_documentacion',
                'correccion_lineas',
                'correccion_descripcion'
            ]
            
            for item in checklist_items:
                if not request.POST.get(item):
                    messages.error(
                        request,
                        "Debes confirmar que has realizado todas las correcciones antes de reenviar."
                    )
                    return redirect(request.path)
        
        estado_anterior = club.status
        club.status = "pendiente"
        club.save(update_fields=["status"])
        
        # Invalidar caché de clubes pendientes
        cache.delete('clubes_pendientes_count')
        
        # Registrar en historial si venía de rechazado
        if estado_anterior == "rechazado":
            HistorialClub.objects.create(
                club=club,
                usuario=request.user,
                estado_anterior=estado_anterior,
                estado_nuevo="pendiente",
                observaciones=f"Club corregido y reenviado a revisión (Intento {num_reenvios + 1}/{MAX_REENVIOS})"
            )
            
            # FASE 2.3: Notificar a federación sobre reenvío
            from .notificaciones import notificar_reenvio_club
            notificar_reenvio_club(club, num_reenvios + 1)
        
        messages.success(
            request, f'Club "{club.nombre}" enviado a revisión correctamente.'
        )
        return redirect("clubes_lista")

    # Obtener último rechazo para mostrar observaciones
    ultimo_rechazo = club.obtener_ultimo_rechazo() if club.status == "rechazado" else None

    context = {
        "club": club,
        "es_reenvio": club.status == "rechazado",
        "num_reenvios": num_reenvios,
        "max_reenvios": MAX_REENVIOS,
        "intentos_restantes": MAX_REENVIOS - num_reenvios,
        "ultimo_rechazo": ultimo_rechazo,
    }
    return render(request, "registry/club_enviar_revision.html", context)


@login_required
def editar_club(request, club_id):
    """Editar un club existente (solo si está en borrador o rechazado)."""
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
        messages.error(request, "No tienes permiso para modificar este club.")
        return redirect("clubes_lista")
    
    # ✅ FASE 2: Validar que el club no esté eliminado
    if club.eliminado:
        messages.error(
            request,
            "No puedes editar un club eliminado. Contacta a la federación si necesitas asistencia."
        )
        return redirect("clubes_lista")

    # Solo editar si está en borrador o rechazado
    if club.status not in ["borrador", "rechazado"]:
        messages.warning(
            request, "No puedes editar un club que está en revisión o aprobado."
        )
        return redirect("clubes_lista")

    if request.method == "POST":
        from registry.forms import ClubForm
        form = ClubForm(request.POST, instance=club)
        
        if form.is_valid():
            try:
                club = form.save()
                messages.success(request, f'Club "{club.nombre}" actualizado exitosamente.')
                return redirect("clubes_lista")
            except Exception as e:
                messages.error(request, f"Error al actualizar club: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        from registry.forms import ClubForm
        form = ClubForm(instance=club)

    context = {
        "club": club,
        "form": form,
        "estados_vinculacion": Club.ESTADO_VINCULACION_CHOICES,
    }
    return render(request, "registry/club_editar.html", context)


@login_required
def postular_club(request, club_id):
    """Postular a un club."""
    club = get_object_or_404(Club, id=club_id)
    institucion = request.user.userprofile.institution

    # Verificar que el club acepta postulaciones
    if not club.puede_postularse:
        messages.error(request, "Este club no acepta postulaciones en estos momentos.")
        return redirect("clubes_lista")

    # Verificar si ya existe una solicitud activa
    if MembresiaClu.objects.filter(
        club=club, institucion=institucion, estado__in=["pendiente_filtro", "visto_bueno_fundadora"]
    ).exists():
        messages.warning(request, "Ya tienes una solicitud activa para este club.")
        return redirect("clubes_lista")

    if request.method == "POST":
        try:
            MembresiaClu.objects.create(
                club=club,
                institucion=institucion,
                carta_intencion=request.POST.get("carta_intencion"),
                propuesta_tecnica=request.POST.get("propuesta_tecnica"),
                representante_legal=request.POST.get("representante_legal"),
                tipo_linea=request.POST.get("tipo_linea", "soporte"),
            )
            messages.success(request, "Solicitud enviada exitosamente.")
            return redirect("clubes_lista")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
        "club": club,
        "tipos_linea": MembresiaClu.TIPO_LINEA_CHOICES,
    }
    return render(request, "registry/club_postular.html", context)


@staff_member_required
def revisar_clubes(request):
    """Vista para que el ADMIN/Federación revise clubes pendientes."""
    # Clubes pendientes de revisión
    clubes_pendientes = (
        Club.objects.filter(status="pendiente")
        .select_related("institucion_creadora")
        .order_by("-fecha_creacion")
    )

    # Clubes en revisión
    clubes_en_revision = (
        Club.objects.filter(status="en_revision")
        .select_related("institucion_creadora")
        .order_by("-fecha_creacion")
    )

    context = {
        "clubes_pendientes": clubes_pendientes,
        "clubes_en_revision": clubes_en_revision,
    }
    return render(request, "registry/revisar_clubes.html", context)


@staff_member_required
def aprobar_club(request, club_id):
    """Aprueba un club con comentario obligatorio y crea membresía automática para el creador."""
    club = get_object_or_404(Club, id=club_id)

    if club.status not in ["pendiente", "en_revision"]:
        messages.error(request, "Este club no puede ser aprobado en su estado actual.")
        return redirect("revisar_clubes")

    if request.method == "POST":
        comentario = request.POST.get("comentario", "").strip()
        
        if not comentario:
            messages.error(request, "Debes agregar un comentario de aprobación.")
            return render(request, "registry/aprobar_club.html", {"club": club})
        
        try:
            with transaction.atomic():
                estado_anterior = club.status
                club.status = "aprobado"
                club.fecha_aprobacion = timezone.now()
                club.save(update_fields=["status", "fecha_aprobacion"])
                
                # Invalidar caché de clubes pendientes
                cache.delete('clubes_pendientes_count')
                
                # Registrar en historial
                HistorialClub.objects.create(
                    club=club,
                    usuario=request.user,
                    estado_anterior=estado_anterior,
                    estado_nuevo="aprobado",
                    observaciones=comentario
                )
                
                # ✅ NUEVO: Crear membresía automática para la institución creadora
                membresia, created = MembresiaClu.objects.get_or_create(
                    club=club,
                    institucion=club.institucion_creadora,
                    defaults={
                        'estado': 'miembro_activo',
                        'fecha_solicitud': timezone.now(),
                        'fecha_respuesta': timezone.now(),
                        'tipo_linea': 'principal',
                        'carta_intencion': 'Membresía automática como institución creadora del club',
                        'propuesta_tecnica': 'Institución fundadora y coordinadora del club',
                        'representante_legal': club.coordinador.get_full_name() or club.coordinador.username,
                        'observaciones': 'Membresía automática otorgada al aprobar el club',
                        'visto_bueno_fundadora': True,
                        'aprobacion_ente_rector': True,
                    }
                )
                
                if created:
                    messages.success(
                        request, 
                        f'Club "{club.nombre}" ha sido APROBADO. '
                        f'La institución creadora ha sido agregada automáticamente como miembro coordinador.'
                    )
                else:
                    messages.success(request, f'Club "{club.nombre}" ha sido APROBADO.')
        except Exception as e:
            messages.error(request, f"Error al aprobar club: {str(e)}")
            return redirect("revisar_clubes")
        
        return redirect("revisar_clubes")
    
    context = {"club": club}
    return render(request, "registry/aprobar_club.html", context)


@staff_member_required
def rechazar_club(request, club_id):
    """Rechaza un club con motivo obligatorio."""
    club = get_object_or_404(Club, id=club_id)

    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()
        
        if not observaciones:
            messages.error(request, "Debes especificar el motivo del rechazo.")
            return render(request, "registry/rechazar_club.html", {"club": club})

        estado_anterior = club.status
        club.status = "rechazado"
        club.save(update_fields=["status"])
        
        # Invalidar caché de clubes pendientes
        cache.delete('clubes_pendientes_count')
        
        # Registrar en historial
        HistorialClub.objects.create(
            club=club,
            usuario=request.user,
            estado_anterior=estado_anterior,
            estado_nuevo="rechazado",
            observaciones=observaciones
        )

        # Notificar al coordinador del club sobre el rechazo
        notificar_club_rechazado(club, observaciones)

        messages.success(request, f'Club "{club.nombre}" ha sido RECHAZADO.')
        return redirect("revisar_clubes")

    context = {"club": club}
    return render(request, "registry/rechazar_club.html", context)


@staff_member_required
def tomar_en_revision_club(request, club_id):
    """Toma un club pendiente y lo pasa a revisión."""
    club = get_object_or_404(Club, id=club_id)
    
    if club.status != "pendiente":
        messages.error(request, "Solo se pueden tomar clubes en estado pendiente.")
        return redirect("revisar_clubes")
    
    if request.method == "POST":
        comentario = request.POST.get("comentario", "")
        
        estado_anterior = club.status
        club.status = "en_revision"
        club.save(update_fields=["status"])
        
        # Invalidar caché de clubes pendientes
        cache.delete('clubes_pendientes_count')
        
        # Registrar en historial
        HistorialClub.objects.create(
            club=club,
            usuario=request.user,
            estado_anterior=estado_anterior,
            estado_nuevo="en_revision",
            observaciones=comentario or f"Club tomado en revisión por {request.user.get_full_name() or request.user.username}"
        )
        
        messages.success(request, f'Club "{club.nombre}" tomado en revisión.')
        return redirect("revisar_clubes")
    
    context = {"club": club}
    return render(request, "registry/tomar_revision_club.html", context)


@staff_member_required
def revisar_membresias(request):
    """
    Vista para que el Ente Rector revise membresías con visto bueno de la Fundadora.
    
    Muestra todas las membresías en diferentes estados:
    - Pendientes de filtro (esperando visto bueno de fundadora)
    - Con visto bueno de fundadora (esperando aprobación del Ente Rector)
    - Miembros activos
    - Rechazadas
    """
    # Membresías pendientes del filtro inicial (Fundadora aún no ha dado visto bueno)
    membresias_pendientes_filtro = (
        MembresiaClu.objects.filter(estado="pendiente_filtro")
        .select_related("club", "institucion")
        .order_by("-fecha_solicitud")
    )

    # Membresías con visto bueno de la Fundadora (esperando aprobación del Ente Rector)
    membresias_con_visto_bueno = (
        MembresiaClu.objects.filter(estado="visto_bueno_fundadora")
        .select_related("club", "institucion")
        .order_by("-fecha_solicitud")
    )
    
    # Membresías activas (ya aprobadas)
    membresias_activas = (
        MembresiaClu.objects.filter(estado="miembro_activo")
        .select_related("club", "institucion")
        .order_by("-fecha_respuesta")
    )
    
    # Membresías rechazadas
    membresias_rechazadas = (
        MembresiaClu.objects.filter(estado="rechazada")
        .select_related("club", "institucion")
        .order_by("-fecha_respuesta")
    )

    # Estadísticas
    total_pendientes = membresias_pendientes_filtro.count()
    total_en_revision = membresias_con_visto_bueno.count()
    total_activas = membresias_activas.count()
    total_rechazadas = membresias_rechazadas.count()

    context = {
        "membresias_pendientes_filtro": membresias_pendientes_filtro,
        "membresias_con_visto_bueno": membresias_con_visto_bueno,
        "membresias_activas": membresias_activas,
        "membresias_rechazadas": membresias_rechazadas,
        # Estadísticas
        "total_pendientes": total_pendientes,
        "total_en_revision": total_en_revision,
        "total_activas": total_activas,
        "total_rechazadas": total_rechazadas,
        "total_pendientes_filtro": total_pendientes,
    }
    return render(request, "registry/revisar_membresias.html", context)


@staff_member_required
def aprobar_membresia(request, membresia_id):
    """
    Aprobación final de membresía por el Ente Rector (Federación Central).
    
    Solo se pueden aprobar membresías que tengan el visto bueno de la Fundadora.
    """
    membresia = get_object_or_404(MembresiaClu, id=membresia_id)

    # Solo se pueden aprobar membresías con visto bueno de la fundadora
    if membresia.estado != "visto_bueno_fundadora":
        messages.error(
            request, 
            "Esta membresía no puede ser aprobada. Debe tener el visto bueno de la Institución Fundadora."
        )
        return redirect("revisar_membresias")

    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()
        
        try:
            # Usar el servicio de admisión para aprobación del Ente Rector
            AdmissionService.aprobar_ente_rector(membresia, request.user, observaciones)
            messages.success(
                request, f'Membresía de "{membresia.institucion.nombre}" APROBADA como Miembro Activo.'
            )
        except Exception as e:
            messages.error(request, f"Error al aprobar membresía: {str(e)}")
        
        return redirect("revisar_membresias")
    
    context = {"membresia": membresia}
    return render(request, "registry/aprobar_membresia_ente_rector.html", context)


@staff_member_required
def rechazar_membresia(request, membresia_id):
    """
    Rechaza una membresía por el Ente Rector.
    
    El Ente Rector puede rechazar membresías en cualquier estado del flujo federado.
    """
    membresia = get_object_or_404(MembresiaClu, id=membresia_id)

    if request.method == "POST":
        motivo = request.POST.get("observaciones", "").strip()
        if not motivo:
            messages.error(request, "Debes proporcionar un motivo de rechazo.")
            context = {"membresia": membresia}
            return render(request, "registry/rechazar_membresia.html", context)

        try:
            # Usar el servicio de admisión para rechazar
            AdmissionService.rechazar_ente_rector(membresia, request.user, motivo)
            messages.success(request, "Membresía RECHAZADA.")
        except Exception as e:
            messages.error(request, f"Error al rechazar membresía: {str(e)}")
        
        return redirect("revisar_membresias")

    context = {
        "membresia": membresia,
    }
    return render(request, "registry/rechazar_membresia.html", context)


@login_required
def buscar_participante(request):
    """
    API para buscar participantes por cédula personal o escolar.

    Retorna los datos del participante para autocompletar formularios.
    """
    cedula = request.GET.get("cedula", "").strip()

    if not cedula:
        return JsonResponse({"found": False})

    institucion = request.user.userprofile.institution

    try:
        # Buscar por cédula personal O cédula escolar
        # Primero buscar el participante
        participante = Participante.objects.filter(
            models.Q(cedula=cedula) | models.Q(cedula_escolar=cedula)
        ).first()
        
        if not participante:
            return JsonResponse({"found": False})
        
        # Verificar que esté vinculado a la institución
        vinculacion = participante.vinculaciones.filter(
            institucion=institucion,
            status='activo'
        ).exists()
        
        if not vinculacion:
            return JsonResponse({"found": False})

        return JsonResponse(
            {
                "found": True,
                "id": participante.id,
                "cedula": participante.cedula,
                "cedula_escolar": participante.cedula_escolar,
                "nombres": participante.nombres,
                "apellidos": participante.apellidos,
                "fecha_nacimiento": participante.fecha_nacimiento.isoformat(),
                "sexo": participante.sexo,
                "email": participante.email,
                "direccion": participante.direccion,
                "codigo_area": participante.codigo_area,
                "numero_telefono": participante.numero_telefono,
                "estado_id": participante.estado_id,
                "municipio_id": participante.municipio_id,
                "parroquia_id": participante.parroquia_id if hasattr(participante, 'parroquia_id') else None,
                "nombre_escuela": participante.nombre_escuela,
                "grado_escolar": participante.grado_escolar,
                "titulo_universitario": participante.titulo_universitario,
                "condicion_tea": participante.condicion_tea,
                "grupo_id": participante.grupo_id if hasattr(participante, 'grupo_id') else None,
                "status": participante.status,
                # Datos del representante
                "nombre_representante": participante.nombre_representante,
                "cedula_representante": participante.cedula_representante,
                "email_representante": participante.email_representante,
            }
        )
    except Participante.DoesNotExist:
        return JsonResponse({"found": False})
    except Participante.MultipleObjectsReturned:
        # Si hay múltiples resultados, retornar el primero
        participante = Participante.objects.filter(
            (models.Q(cedula=cedula) | models.Q(cedula_escolar=cedula)),
            institucion=institucion
        ).first()

        return JsonResponse(
            {
                "found": True,
                "id": participante.id,
                "cedula": participante.cedula,
                "cedula_escolar": participante.cedula_escolar,
                "nombres": participante.nombres,
                "apellidos": participante.apellidos,
                "fecha_nacimiento": participante.fecha_nacimiento.isoformat(),
                "sexo": participante.sexo,
                "email": participante.email,
            }
        )


@login_required
def directorio_clubes_aprobados(request):
    """Directorio público de todos los clubes aprobados."""
    if not hasattr(request.user, "userprofile"):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    user_type = request.user.userprofile.user_type
    if user_type not in ["institucional", "fed_central", "fed_regional", "superuser"]:
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")

    # Obtener todos los clubes aprobados
    clubes_aprobados = (
        Club.objects.filter(
            status="aprobado",
            activo=True
        )
        .select_related("institucion_creadora")
        .annotate(
            num_membresias=Count("membresias", filter=Q(membresias__estado="miembro_activo"))
        )
        .order_by("-fecha_aprobacion")
    )
    
    # Contar instituciones únicas participantes (creadoras + miembros)
    instituciones_creadoras = set(clubes_aprobados.values_list('institucion_creadora_id', flat=True))
    instituciones_miembros = set(
        MembresiaClu.objects.filter(
            club__in=clubes_aprobados,
            estado='miembro_activo'
        ).values_list('institucion_id', flat=True)
    )
    total_instituciones_participantes = len(instituciones_creadoras | instituciones_miembros)

    context = {
        "clubes_aprobados": clubes_aprobados,
        "total_clubes": clubes_aprobados.count(),
        "total_instituciones_participantes": total_instituciones_participantes,
    }
    return render(request, "registry/directorio_clubes_aprobados.html", context)


@login_required
def detalle_club(request, club_id):
    """Vista de detalle de un club - Accesible para federación e instituciones."""
    if not hasattr(request.user, "userprofile"):
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    user_type = request.user.userprofile.user_type
    
    # Permitir acceso a federación e institucionales
    if user_type in ["fed_central", "fed_regional", "superuser"]:
        # Federación puede ver cualquier club
        club = get_object_or_404(Club.objects.select_related("institucion_creadora"), id=club_id)
    elif user_type == "institucional":
        # Institucionales solo ven clubes aprobados
        club = get_object_or_404(
            Club.objects.select_related("institucion_creadora"),
            id=club_id,
            status="aprobado",
            activo=True
        )
    else:
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")

    # Obtener membresías activas
    membresias_activas = club.membresias.filter(
        estado="miembro_activo"
    ).select_related("institucion")

    # Verificar si el usuario ya postuló
    institucion = request.user.userprofile.institution
    ya_postulo = club.membresias.filter(
        institucion=institucion,
        estado__in=["pendiente_filtro", "visto_bueno_fundadora", "miembro_activo"]
    ).exists()
    
    # Verificar si es propietario del club
    es_propietario = club.institucion_creadora == institucion
    
    # Fase 4: Verificar si es miembro
    es_miembro = club.membresias.filter(
        institucion=institucion,
        estado="miembro_activo"
    ).exists()
    
    # Fase 4: Obtener eventos vinculados
    from .models import ClubEvento
    eventos_vinculados = ClubEvento.objects.filter(
        club=club,
        activo=True
    ).select_related("evento")

    # Fase 4: Obtener información de calificaciones
    promedio = club.promedio_calificacion
    total_calif = club.total_calificaciones
    calificaciones_recientes = club.calificaciones_recientes
    mi_calificacion = None
    if es_miembro and institucion:
        mi_calificacion = club.mi_calificacion(institucion)

    context = {
        "club": club,
        "membresias_activas": membresias_activas,
        "ya_postulo": ya_postulo,
        "puede_postular": club.puede_postularse and not ya_postulo,
        "es_propietario": es_propietario,
        "es_miembro": es_miembro,
        "eventos_vinculados": eventos_vinculados,
        "user_type": user_type,
        # Calificaciones
        "promedio_calificacion": promedio,
        "total_calificaciones": total_calif,
        "calificaciones_recientes": calificaciones_recientes,
        "mi_calificacion": mi_calificacion,
    }
    return render(request, "registry/detalle_club.html", context)



@login_required
def eliminar_club(request, club_id):
    """Elimina un club según su estado."""
    if not hasattr(request.user, "userprofile") or request.user.userprofile.user_type != "institucional":
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    club = get_object_or_404(Club, id=club_id)
    institucion = request.user.userprofile.institution
    
    if club.institucion_creadora != institucion:
        messages.error(request, "No tienes permiso para eliminar este club.")
        return redirect("clubes_lista")
    
    if club.eliminado:
        messages.warning(request, "Este club ya está eliminado.")
        return redirect("clubes_lista")
    
    if request.method == "POST":
        if club.status in ["borrador", "rechazado"]:
            nombre = club.nombre
            club.delete()
            messages.success(request, f'Club "{nombre}" eliminado permanentemente.')
            return redirect("clubes_lista")
        
        elif club.status in ["aprobado", "pendiente", "en_revision"]:
            motivo = request.POST.get("motivo", "").strip()
            if not motivo:
                messages.error(request, "Debes proporcionar un motivo para la eliminación.")
                return render(request, "registry/club_eliminar.html", {"club": club})
            
            if SolicitudEliminacionClub.objects.filter(club=club, estado="pendiente").exists():
                messages.warning(request, "Ya existe una solicitud de eliminación pendiente para este club.")
                return redirect("clubes_lista")
            
            solicitud = SolicitudEliminacionClub.objects.create(
                club=club,
                institucion_solicitante=institucion,
                motivo=motivo
            )
            notificar_solicitud_eliminacion(solicitud)
            messages.success(request, f'Solicitud de eliminación enviada a la federación para el club "{club.nombre}".')
            return redirect("clubes_lista")
    
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
    
    context = {"solicitudes_pendientes": solicitudes_pendientes}
    return render(request, "registry/revisar_solicitudes_eliminacion.html", context)


@staff_member_required
def aprobar_eliminacion_club(request, solicitud_id):
    """
    Aprueba una solicitud de eliminación.
    
    Lógica:
    - Si hay otros miembros además del propietario: permite transferir propiedad
    - Si no hay otros miembros: elimina el club (papelera)
    """
    solicitud = get_object_or_404(SolicitudEliminacionClub, id=solicitud_id)
    club = solicitud.club
    
    # Obtener otros miembros activos (excluyendo al propietario actual)
    otros_miembros = club.membresias.filter(
        estado='miembro_activo'
    ).exclude(
        institucion=club.institucion_creadora
    ).select_related('institucion')
    
    if solicitud.estado != "pendiente":
        messages.error(request, "Esta solicitud ya fue procesada.")
        return redirect("revisar_solicitudes_eliminacion")
    
    if request.method == "POST":
        # Determinar acción: transferir o eliminar
        accion = request.POST.get('accion', 'eliminar')
        
        try:
            with transaction.atomic():
                solicitud.estado = "aprobada"
                solicitud.fecha_respuesta = timezone.now()
                solicitud.revisado_por = request.user
                solicitud.save()
                
                if accion == 'transferir' and otros_miembros.exists():
                    # Transferir propiedad a otro miembro
                    nueva_institucion_id = request.POST.get('nuevo_propietario')
                    if nueva_institucion_id:
                        nueva_membresia = otros_miembros.filter(id=nueva_institucion_id).first()
                        if nueva_membresia:
                            antigua_institucion = club.institucion_creadora
                            club.institucion_creadora = nueva_membresia.institucion
                            club.coordinador = nueva_membresia.institucion.usuario
                            club.save()
                            
                            # Notificar transferencia
                            from .notificaciones import notificar_transferencia_propietario
                            notificar_transferencia_propietario(club, antigua_institucion, nueva_membresia.institucion)
                            
                            # Notificar al solicitante que su club fue transferido
                            notificar_eliminacion_aprobada(solicitud)
                            messages.success(
                                request, 
                                f'Club "{club.nombre}" transferido a {nueva_membresia.institucion.nombre}.'
                            )
                    else:
                        messages.error(request, "No seleccionaste un nuevo propietario válido.")
                        return redirect("revisar_solicitudes_eliminacion")
                else:
                    # Eliminar club (no hay otros miembros o se eligió eliminar)
                    club.eliminado = True
                    club.fecha_eliminacion = timezone.now()
                    club.eliminado_por = request.user
                    club.motivo_eliminacion = solicitud.motivo
                    club.activo = False
                    club.save()
                    
                    notificar_eliminacion_aprobada(solicitud)
                    messages.success(request, f'Club "{club.nombre}" eliminado correctamente.')
        except Exception as e:
            messages.error(request, f"Error al procesar solicitud: {str(e)}")
        
        return redirect("revisar_solicitudes_eliminacion")
    
    context = {
        "solicitud": solicitud,
        "club": club,
        "otros_miembros": otros_miembros,
        "tiene_otros_miembros": otros_miembros.exists(),
    }
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
        
        notificar_eliminacion_rechazada(solicitud)
        messages.success(request, f'Solicitud de eliminación rechazada para el club "{solicitud.club.nombre}".')
        return redirect("revisar_solicitudes_eliminacion")
    
    context = {"solicitud": solicitud}
    return render(request, "registry/rechazar_eliminacion_club.html", context)


@login_required
def mis_notificaciones(request):
    """Vista para ver notificaciones del usuario."""
    # Obtener notificaciones del usuario autenticado
    notificaciones = Notificacion.objects.filter(destinatario=request.user).order_by('-fecha_creacion')
    no_leidas = notificaciones.filter(leida=False).count()
    notificaciones = notificaciones[:50]  # Slice al final
    
    context = {
        "notificaciones": notificaciones,
        "no_leidas": no_leidas,
    }
    return render(request, "registry/mis_notificaciones.html", context)


@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación como leída."""
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, destinatario=request.user)
    notificacion.marcar_leida()
    return redirect("mis_notificaciones")


@login_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones como leídas."""
    if request.method == "POST":
        Notificacion.objects.filter(destinatario=request.user, leida=False).update(leida=True)
        messages.success(request, "Todas las notificaciones marcadas como leídas.")
    return redirect("mis_notificaciones")



@login_required
def ver_historial_club(request, club_id):
    """Ver historial completo de cambios de un club - Timeline profesional."""
    club = get_object_or_404(Club, id=club_id)
    
    # Verificar permisos
    user_type = request.user.userprofile.user_type
    
    if user_type == "institucional":
        if club.institucion_creadora != request.user.userprofile.institution:
            messages.error(request, "No tienes permiso para ver este historial.")
            return redirect("clubes_lista")
    elif user_type not in ["fed_central", "fed_regional", "superuser"]:
        messages.error(request, "No tienes permiso para ver este historial.")
        return redirect("dashboard")
    
    # Obtener historial ordenado cronológicamente (más reciente primero)
    historial = club.historial.select_related('usuario').order_by('-fecha')
    
    context = {
        "club": club,
        "historial": historial,
        "es_federacion": user_type in ["fed_central", "fed_regional", "superuser"],
    }
    return render(request, "registry/historial_club.html", context)


@login_required
def agregar_comentario_club(request, club_id):
    """Agregar comentario a un club en revisión."""
    club = get_object_or_404(Club, id=club_id)
    
    # Verificar que el club esté en revisión
    if club.status not in ["pendiente", "en_revision"]:
        messages.error(request, "Solo se pueden comentar clubes en revisión.")
        return redirect("clubes_lista")
    
    # Verificar permisos
    es_federacion = request.user.is_staff
    es_propietario = (
        hasattr(request.user, "userprofile") and
        request.user.userprofile.user_type == "institucional" and
        club.institucion_creadora == request.user.userprofile.institution
    )
    
    if not (es_federacion or es_propietario):
        messages.error(request, "No tienes permiso para comentar en este club.")
        return redirect("clubes_lista")
    
    if request.method == "POST":
        comentario_texto = request.POST.get("comentario", "").strip()
        if comentario_texto:
            ComentarioClub.objects.create(
                club=club,
                usuario=request.user,
                comentario=comentario_texto,
                es_federacion=es_federacion
            )
            messages.success(request, "Comentario agregado exitosamente.")
        else:
            messages.error(request, "El comentario no puede estar vacío.")
    
    return redirect("ver_comentarios_club", club_id=club.id)


@login_required
def ver_comentarios_club(request, club_id):
    """Ver todos los comentarios de un club."""
    club = get_object_or_404(Club, id=club_id)
    
    # Verificar permisos
    es_federacion = request.user.is_staff
    es_propietario = (
        hasattr(request.user, "userprofile") and
        request.user.userprofile.user_type == "institucional" and
        club.institucion_creadora == request.user.userprofile.institution
    )
    
    if not (es_federacion or es_propietario):
        messages.error(request, "No tienes permiso para ver estos comentarios.")
        return redirect("clubes_lista")
    
    comentarios = club.comentarios.all()
    
    context = {
        "club": club,
        "comentarios": comentarios,
        "puede_comentar": club.status in ["pendiente", "en_revision"],
    }
    return render(request, "registry/comentarios_club.html", context)


# ============================================================================
# GESTIÓN DE MEMBRESÍAS
# ============================================================================

@login_required
def gestionar_membresias_club(request, club_id):
    """Vista para que el propietario del club gestione membresías."""
    club = get_object_or_404(Club, id=club_id)
    
    # Verificar que el usuario es propietario del club
    if not hasattr(request.user, "userprofile") or club.institucion_creadora != request.user.userprofile.institution:
        messages.error(request, "No tienes permiso para gestionar este club.")
        return redirect("clubes_lista")
    
    # Obtener membresías por estado federado
    membresias_pendientes = club.membresias.filter(estado="pendiente_filtro").select_related("institucion")
    membresias_con_visto_bueno = club.membresias.filter(estado="visto_bueno_fundadora").select_related("institucion")
    membresias_activas = club.membresias.filter(estado="miembro_activo").select_related("institucion")
    membresias_rechazadas = club.membresias.filter(estado="rechazada").select_related("institucion")
    
    # Métricas
    total_miembros = membresias_activas.count()
    total_pendientes = membresias_pendientes.count() + membresias_con_visto_bueno.count()
    cupos_disponibles = club.cupo_maximo - total_miembros if club.cupo_maximo else None
    
    context = {
        "club": club,
        "membresias_pendientes": membresias_pendientes,
        "membresias_con_visto_bueno": membresias_con_visto_bueno,
        "membresias_activas": membresias_activas,
        "membresias_rechazadas": membresias_rechazadas,
        "total_miembros": total_miembros,
        "total_pendientes": total_pendientes,
        "cupos_disponibles": cupos_disponibles,
    }
    return render(request, "registry/gestionar_membresias_club.html", context)


@login_required
def mis_membresias(request):
    """Vista para que instituciones vean sus membresías a clubes."""
    if not hasattr(request.user, "userprofile") or request.user.userprofile.user_type != "institucional":
        messages.error(request, "Solo instituciones pueden acceder a esta sección.")
        return redirect("dashboard")
    
    institucion = request.user.userprofile.institution
    
    # Obtener membresías por estado federado
    membresias_activas = MembresiaClu.objects.filter(institucion=institucion, estado="miembro_activo").select_related("club")
    membresias_pendientes = MembresiaClu.objects.filter(institucion=institucion, estado__in=["pendiente_filtro", "visto_bueno_fundadora"]).select_related("club")
    membresias_rechazadas = MembresiaClu.objects.filter(institucion=institucion, estado="rechazada").select_related("club")
    
    context = {
        "membresias_aprobadas": membresias_activas,
        "membresias_pendientes": membresias_pendientes,
        "membresias_rechazadas": membresias_rechazadas,
        "total_clubes": membresias_activas.count(),
        "total_activas": membresias_activas.count(),
        "total_pendientes": membresias_pendientes.count(),
        "total_rechazadas": membresias_rechazadas.count(),
    }
    return render(request, "registry/mis_membresias.html", context)


@login_required
def detalle_membresia(request, membresia_id):
    """Vista de detalle de una membresía específica."""
    membresia = get_object_or_404(MembresiaClu.objects.select_related("club", "institucion"), id=membresia_id)
    
    # Verificar permisos
    es_propietario_club = (
        hasattr(request.user, "userprofile") and
        membresia.club.institucion_creadora == request.user.userprofile.institution
    )
    es_institucion_miembro = (
        hasattr(request.user, "userprofile") and
        membresia.institucion == request.user.userprofile.institution
    )
    
    if not (es_propietario_club or es_institucion_miembro):
        messages.error(request, "No tienes permiso para ver esta membresía.")
        return redirect("clubes_lista")
    
    context = {
        "membresia": membresia,
        "es_propietario_club": es_propietario_club,
        "es_institucion_miembro": es_institucion_miembro,
    }
    return render(request, "registry/detalle_membresia.html", context)


@login_required
def aprobar_membresia_club(request, membresia_id):
    """
    Dar visto bueno a solicitud de membresía (Institución Fundadora).
    
    Flujo de Doble Aprobación:
    - Este paso es realizado por la Institución Fundadora del club
    - La membresía pasa de 'pendiente_filtro' a 'visto_bueno_fundadora'
    - Luego el Ente Rector (Federación Central) debe dar la aprobación final
    """
    membresia = get_object_or_404(MembresiaClu, id=membresia_id)
    
    # Verificar que el usuario es propietario del club (Institución Fundadora)
    if not hasattr(request.user, "userprofile") or membresia.club.institucion_creadora != request.user.userprofile.institution:
        messages.error(request, "No tienes permiso para aprobar esta membresía.")
        return redirect("clubes_lista")
    
    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()
        
        try:
            # Usar el servicio de admisión para dar visto bueno
            AdmissionService.dar_visto_bueno_fundadora(membresia, request.user, observaciones)
            messages.success(
                request, 
                f'Visto bueno otorgado a "{membresia.institucion.nombre}". '
                f'La solicitud ha sido enviada al Ente Rector para aprobación final.'
            )
        except Exception as e:
            messages.error(request, f"Error al procesar la solicitud: {str(e)}")
        
        return redirect("gestionar_membresias_club", club_id=membresia.club.id)
    
    context = {"membresia": membresia}
    return render(request, "registry/aprobar_membresia_club.html", context)


@login_required
def rechazar_membresia_club(request, membresia_id):
    """
    Rechazar solicitud de membresía (Institución Fundadora).
    
    La Institución Fundadora puede rechazar solicitudes que no cumplan
    con los requisitos del club.
    """
    membresia = get_object_or_404(MembresiaClu, id=membresia_id)
    
    # Verificar que el usuario es propietario del club (Institución Fundadora)
    if not hasattr(request.user, "userprofile") or membresia.club.institucion_creadora != request.user.userprofile.institution:
        messages.error(request, "No tienes permiso para rechazar esta membresía.")
        return redirect("clubes_lista")
    
    if request.method == "POST":
        motivo = request.POST.get("observaciones", "").strip()
        if not motivo:
            messages.error(request, "Debes proporcionar un motivo de rechazo.")
            return render(request, "registry/rechazar_membresia_club.html", {"membresia": membresia})
        
        try:
            # Usar el servicio de admisión para rechazar
            AdmissionService.rechazar_fundadora(membresia, request.user, motivo)
            messages.success(request, f'Membresía de "{membresia.institucion.nombre}" rechazada.')
        except Exception as e:
            messages.error(request, f"Error al procesar el rechazo: {str(e)}")
        
        return redirect("gestionar_membresias_club", club_id=membresia.club.id)
    
    return render(request, "registry/rechazar_membresia_club.html", {"membresia": membresia})


@login_required
def salir_club(request, membresia_id):
    """Permite a una institución salirse de un club."""
    membresia = get_object_or_404(MembresiaClu, id=membresia_id)
    
    # Verificar que el usuario es la institución miembro
    if not hasattr(request.user, "userprofile") or membresia.institucion != request.user.userprofile.institution:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect("mis_membresias")
    
    # VALIDACIÓN CRÍTICA: El propietario NO puede salirse de su propio club
    if membresia.club.institucion_creadora == membresia.institucion:
        messages.error(
            request,
            "No puedes salir de un club que has creado. Como propietario, tienes dos opciones: "
            "1) Solicitar la eliminación del club a la federación, o "
            "2) Transferir la propiedad a otro miembro activo (funcionalidad futura)."
        )
        return redirect("mis_membresias")
    
    # Solo se puede salir si es miembro activo (estado federado)
    if membresia.estado != "miembro_activo":
        messages.error(request, "Solo puedes salir de clubes donde eres miembro activo.")
        return redirect("mis_membresias")
    
    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        
        # Cambiar estado a rechazada
        membresia.estado = "rechazada"
        membresia.observaciones = f"Salida voluntaria: {motivo}" if motivo else "Salida voluntaria"
        membresia.fecha_respuesta = timezone.now()
        membresia.save()
        
        # Notificar al propietario del club
        notificar_salida_club(membresia, motivo)
        
        # Actualizar cupos del club (reabre si estaba cerrado)
        club = membresia.club
        if club.estado_vinculacion == "cerrado":
            miembros_actuales = club.membresias.filter(estado="miembro_activo").count()
            if miembros_actuales < club.cupo_maximo:
                club.estado_vinculacion = "abierto"
                club.save(update_fields=["estado_vinculacion"])
        
        messages.success(request, f'Has salido exitosamente del club "{club.nombre}".')
        return redirect("mis_membresias")
    
    context = {"membresia": membresia}
    return render(request, "registry/salir_club.html", context)
