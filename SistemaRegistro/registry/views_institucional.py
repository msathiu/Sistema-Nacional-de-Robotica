"""Vistas para el módulo institucional de gestión de grupos, eventos y clubes."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    Club,
    Evento,
    Grupo,
    InscripcionGrupoEvento,
    MembresiaClu,
    Participante,
)


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
def crear_grupo(request):
    """Crear un nuevo grupo."""
    if request.user.userprofile.user_type != "institucional":
        return redirect("dashboard")

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Crear grupo
                grupo = Grupo.objects.create(
                    nombre=request.POST.get("nombre"),
                    criterio=request.POST.get("criterio"),
                    tutor_nombre=request.POST.get("tutor_nombre"),
                    tutor_apellidos=request.POST.get("tutor_apellidos"),
                    tutor_cedula=request.POST.get("tutor_cedula"),
                    tutor_telefono=request.POST.get("tutor_telefono"),
                    usuario_creador=request.user,
                )

                # Agregar participantes
                participantes_ids = request.POST.getlist("participantes[]")
                if participantes_ids:
                    grupo.participantes.set(participantes_ids)

                messages.success(
                    request, f'Grupo "{grupo.nombre}" creado exitosamente.'
                )
                return redirect("grupos_institucion")
        except Exception as e:
            messages.error(request, f"Error al crear el grupo: {str(e)}")

    # GET
    institucion = request.user.userprofile.institution
    participantes = Participante.objects.filter(institucion=institucion, activo=True)

    context = {
        "participantes": participantes,
        "criterios": Grupo.CRITERIO_CHOICES,
    }
    return render(request, "registry/grupo_crear.html", context)


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
            grupo.participantes.set(participantes_ids)

            messages.success(request, "Grupo actualizado exitosamente.")
            return redirect("grupos_institucion")
        except Exception as e:
            messages.error(request, f"Error al actualizar: {str(e)}")

    institucion = request.user.userprofile.institution
    participantes = Participante.objects.filter(institucion=institucion, activo=True)

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
@require_http_methods(["POST"])
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

    if evento.estado_evento not in ["abierto"]:
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
    """Lista de clubes."""
    if request.user.userprofile.user_type != "institucional":
        return redirect("dashboard")

    institucion = request.user.userprofile.institution

    # Clubes propios
    mis_clubes = Club.objects.filter(institucion_creadora=institucion)

    # Clubes disponibles para postular
    clubes_disponibles = Club.objects.filter(
        activo=True, estado_vinculacion__in=["abierto", "invitacion"]
    ).exclude(institucion_creadora=institucion)

    context = {
        "mis_clubes": mis_clubes,
        "clubes_disponibles": clubes_disponibles,
    }
    return render(request, "registry/clubes_lista.html", context)


@login_required
def crear_club(request):
    """Crear un nuevo club."""
    if request.user.userprofile.user_type != "institucional":
        return redirect("dashboard")

    if request.method == "POST":
        try:
            institucion = request.user.userprofile.institution

            club = Club.objects.create(
                nombre=request.POST.get("nombre"),
                siglas=request.POST.get("siglas"),
                descripcion=request.POST.get("descripcion"),
                ubicacion=request.POST.get("ubicacion"),
                fecha_fundacion=request.POST.get("fecha_fundacion") or None,
                linea_1=request.POST.get("linea_1"),
                linea_2=request.POST.get("linea_2") or None,
                linea_3=request.POST.get("linea_3") or None,
                estado_vinculacion=request.POST.get("estado_vinculacion"),
                cupo_maximo=request.POST.get("cupo_maximo", 10),
                requisitos=request.POST.get("requisitos", ""),
                institucion_creadora=institucion,
            )

            messages.success(request, f'Club "{club.nombre}" creado exitosamente.')
            return redirect("clubes_lista")
        except Exception as e:
            messages.error(request, f"Error al crear club: {str(e)}")

    context = {
        "lineas": Club.LINEAS_INVESTIGACION_CHOICES,
        "estados_vinculacion": Club.ESTADO_VINCULACION_CHOICES,
    }
    return render(request, "registry/club_crear.html", context)


@login_required
def postular_club(request, club_id):
    """Postular a un club."""
    club = get_object_or_404(Club, id=club_id)
    institucion = request.user.userprofile.institution

    if club.estado_vinculacion == "cerrado":
        messages.error(request, "Este club no acepta postulaciones.")
        return redirect("clubes_lista")

    # Verificar si ya existe una solicitud
    if MembresiaClu.objects.filter(club=club, institucion=institucion).exists():
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
            )
            messages.success(request, "Solicitud enviada exitosamente.")
            return redirect("clubes_lista")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
        "club": club,
    }
    return render(request, "registry/club_postular.html", context)


@login_required
def buscar_participante(request):
    """API para buscar participantes por cédula."""
    cedula = request.GET.get("cedula", "").strip()

    if not cedula:
        return JsonResponse({"found": False})

    institucion = request.user.userprofile.institution

    try:
        participante = Participante.objects.get(cedula=cedula, institucion=institucion)

        return JsonResponse(
            {
                "found": True,
                "id": participante.id,
                "nombres": participante.nombres,
                "apellidos": participante.apellidos,
                "fecha_nacimiento": participante.fecha_nacimiento.isoformat(),
                "sexo": participante.sexo,
                "grado_escolar": participante.grado_escolar,
            }
        )
    except Participante.DoesNotExist:
        return JsonResponse({"found": False})
