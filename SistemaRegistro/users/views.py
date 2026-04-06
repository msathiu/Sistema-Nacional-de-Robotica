import json
import logging
from datetime import date, datetime

import pandas as pd
from django.apps import apps
from django.contrib import messages
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic.edit import UpdateView
from registry.models import (
    AsistenciaEvento,
    Dependencia,
    Estado,
    EstadoEvento,
    Evento,
    Grupo,
    Inscripcion,
    InscripcionGrupoEvento,
    Institucion,
    IntegranteEquipo,
    MembresiaClu,
    Municipio,
    Notificacion,
    Parroquia,
    Participante,
    ParticipanteInstitucion,
)

from .decorators import (
    admin_or_owner_required,
    admin_required,
    fed_central_cannot_create,
    fed_central_required,
    institucional_required,
    not_superuser_required,
)
from .forms import (
    InstitucionCredentialAdminForm,
    InstitucionModalEditForm,
    InstitucionRegistrationForm,
    ParticipanteModalEditForm,
    ParticipanteRegistrationForm,
    SedeRegionalForm,
)
from .models import UserProfile
from .selectors import (
    EventoSelector,
    InstitucionSelector,
    JurisdictionSelector,
    ParticipanteSelector,
)


def _get_evento_institucional(evento_id, institution):
    """
    Resuelve un Evento verificando que la institución tenga pertenencia:
    - Evento institucional propio (institucion=institution)
    - Evento de club donde la institución es creadora del club
    - Evento de club donde la institución es miembro activo del club
    Lanza Http404 si no existe o no pertenece.
    """
    from django.http import Http404

    evento = get_object_or_404(Evento, id=evento_id)
    if (
        evento.institucion == institution
        or (
            evento.club_organizador
            and evento.club_organizador.institucion_creadora == institution
        )
        or (
            evento.club_organizador
            and MembresiaClu.objects.filter(
                club=evento.club_organizador,
                institucion=institution,
                estado="miembro_activo",
            ).exists()
        )
    ):
        return evento
    raise Http404


from .services.evento_service import EventoService
from .services.grupo_service import GrupoService
from .services.identity_service import IdentityService
from .services.institution_service import InstitutionService
from .services.participante_service import ParticipanteService
from .services.report_service import ReportService

logger = logging.getLogger(__name__)


def _mask_identifier_tail(value, visible_digits=4, prefix=""):
    numeric_value = "".join(filter(str.isdigit, str(value or "")))
    if not numeric_value:
        return "N/A"
    masked_length = max(len(numeric_value) - visible_digits, 0)
    masked = ("*" * masked_length) + numeric_value[-visible_digits:]
    return f"{prefix}{masked}" if prefix else masked


def _render_formulario_evento(
    request,
    *,
    perfil,
    evento=None,
    valores_previos=None,
    errores=None,
):
    institution = (
        perfil.institution
        if getattr(perfil, "user_type", None) == "institucional"
        else None
    )
    es_federacion = EventoSelector.es_usuario_federacion_eventos(perfil)
    estado_institucion = EventoSelector.get_estado_contexto(perfil, institution)
    estados = Estado.objects.all().order_by("nombre")
    hoy = date.today().isoformat()
    categorias = [choice[1] for choice in Evento.TIPO_CHOICES]
    clubes_disponibles = EventoSelector.get_clubes_disponibles_para_formulario(perfil)

    if valores_previos is None:
        if evento:
            valores_previos = EventoService.get_initial_form_data(evento)
        else:
            valores_previos = {
                "estado_evento": EstadoEvento.BORRADOR,
                "modalidad": "presencial",
                "fecha_hasta": "",
            }

    # Cancelar redirige según rol. Instituciones siempre vuelven a mis_eventos, federación a admin_eventos.
    url_cancelar = "admin_eventos" if es_federacion else "mis_eventos"

    context = {
        "evento": evento,
        "estados": estados,
        "hoy": hoy,
        "categorias": categorias,
        "estado_institucion": estado_institucion,
        "valores_previos": valores_previos,
        "errores": errores or {},
        "es_federacion": es_federacion,
        "clubes_disponibles": clubes_disponibles,
        "modo_edicion": evento is not None,
        "url_cancelar": url_cancelar,
    }
    return render(request, "users/crear_evento.html", context)


@login_required
@require_http_methods(["POST", "GET"])
def detalle_evento_inscripcion(request, evento_id):
    """
    Vista para ver detalles de un evento e inscribir Equipos.
    Regla: solo un grupo por institución por evento.
    """
    user_profile = request.user.userprofile

    evento = (
        EventoSelector.get_eventos_visibles(user_profile).filter(id=evento_id).first()
    )
    if not evento:
        # La institución creadora no aparece en get_eventos_visibles (excluye propios)
        # pero sí debe poder inscribir en sus propios eventos abiertos
        from registry.models import MembresiaClu

        institution = user_profile.institution
        evento = (
            Evento.objects.filter(
                id=evento_id,
                estado_evento=EstadoEvento.ABIERTO,
            )
            .filter(
                Q(institucion=institution)
                | Q(club_organizador__institucion_creadora=institution)
                | Q(
                    club_organizador_id__in=MembresiaClu.objects.filter(
                        institucion=institution, estado="miembro_activo"
                    ).values_list("club_id", flat=True)
                )
            )
            .first()
        )
    if not evento:
        messages.error(request, "El evento no existe o no tienes permiso para verlo.")
        return redirect("eventos_disponibles")

    # Verificar si la institución del usuario ya tiene un grupo inscrito en este evento
    institucion = user_profile.institution
    grupo_ya_inscrito = (
        InscripcionGrupoEvento.objects.filter(
            evento=evento,
            activo=True,
            grupo__usuario_creador__userprofile__institution=institucion,
        )
        .select_related("grupo")
        .first()
    )

    # Solo mostrar grupos disponibles si la institución aún no tiene uno inscrito
    grupos_disponibles = (
        Grupo.objects.filter(
            usuario_creador=request.user, activo=True, estado_grupo="editable"
        ).exclude(inscripciones__evento=evento)
        if not grupo_ya_inscrito
        else Grupo.objects.none()
    )

    grupos_inscritos = InscripcionGrupoEvento.objects.filter(
        evento=evento, activo=True
    ).select_related("grupo")

    context = {
        "evento": evento,
        "grupos_disponibles": grupos_disponibles,
        "grupos_inscritos": grupos_inscritos,
        "grupo_ya_inscrito": grupo_ya_inscrito,
        "hoy": date.today(),
    }
    return render(request, "users/detalle_evento_inscripcion.html", context)


@login_required
def inscribir_grupo_evento(request, evento_id):
    """
    Vista para inscribir un Equipo en un evento institucional.
    Al inscribir, el grupo pasa a estado 'inscrito' y queda asociado al evento.
    """
    if request.method != "POST":
        return redirect("eventos_disponibles")

    user_profile = request.user.userprofile
    evento = (
        EventoSelector.get_eventos_visibles(user_profile).filter(id=evento_id).first()
    )
    if not evento:
        # Fallback: la institución creadora está excluida de get_eventos_visibles
        # pero sí puede inscribir en sus propios eventos abiertos
        from registry.models import MembresiaClu

        institution = user_profile.institution
        evento = (
            Evento.objects.filter(
                id=evento_id,
                estado_evento=EstadoEvento.ABIERTO,
            )
            .filter(
                Q(institucion=institution)
                | Q(club_organizador__institucion_creadora=institution)
                | Q(
                    club_organizador_id__in=MembresiaClu.objects.filter(
                        institucion=institution, estado="miembro_activo"
                    ).values_list("club_id", flat=True)
                )
            )
            .first()
        )
    if not evento:
        messages.error(
            request, "El evento no existe o no tienes permiso para inscribirte en él."
        )
        return redirect("eventos_disponibles")

    grupo_id = request.POST.get("grupo_id")
    rol = request.POST.get("rol_participacion", "participante") or "participante"

    if not grupo_id:
        messages.error(request, "❌ Debes seleccionar un grupo para inscribir.")
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    try:
        grupo = Grupo.objects.get(
            id=grupo_id, usuario_creador=request.user, activo=True
        )
    except Grupo.DoesNotExist:
        messages.error(request, "❌ El grupo seleccionado no existe o no te pertenece.")
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    if grupo.estado_grupo != "editable":
        messages.error(
            request,
            f"❌ El grupo '{grupo.nombre}' no puede inscribirse porque está en estado "
            f"'{grupo.get_estado_grupo_display()}'. Solo grupos en estado Editable pueden inscribirse.",
        )
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    if not evento.puede_inscribirse:
        messages.error(
            request,
            "❌ Este evento no está disponible para inscripciones en este momento.",
        )
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    if evento.fecha < date.today():
        messages.error(request, "❌ No puedes inscribirte en un evento que ya pasó.")
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    if InscripcionGrupoEvento.objects.filter(evento=evento, grupo=grupo).exists():
        messages.warning(
            request, f"⚠️ El grupo '{grupo.nombre}' ya está inscrito en este evento."
        )
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    # Regla: solo un grupo por institución por evento
    institucion = user_profile.institution
    if InscripcionGrupoEvento.objects.filter(
        evento=evento,
        activo=True,
        grupo__usuario_creador__userprofile__institution=institucion,
    ).exists():
        messages.error(
            request,
            "❌ Tu institución ya tiene un equipo inscrito en este evento. "
            "Solo se permite un equipo por institución.",
        )
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    try:
        with transaction.atomic():
            InscripcionGrupoEvento.objects.create(
                evento=evento, grupo=grupo, rol_participacion=rol, activo=True
            )
            grupo.estado_grupo = "inscrito"
            grupo.evento = evento
            grupo.save(update_fields=["estado_grupo", "evento"])
        messages.success(
            request,
            f"✅ Equipo '{grupo.nombre}' inscrito exitosamente en '{evento.nombre}'.",
        )
    except Exception:
        messages.error(
            request, "❌ Error al procesar la inscripción. Intenta nuevamente."
        )

    return redirect("detalle_evento_inscripcion", evento_id=evento_id)


@login_required
def cancelar_inscripcion_grupo(request, inscripcion_id):
    """
    Cancela la inscripción de un grupo en un evento y revierte el estado del grupo.
    Solo puede hacerlo la institución dueña del grupo, y solo si el evento está abierto.
    """
    if request.method != "POST":
        return redirect("eventos_disponibles")

    inscripcion = get_object_or_404(
        InscripcionGrupoEvento.objects.select_related("grupo", "evento"),
        id=inscripcion_id,
        activo=True,
    )

    grupo = inscripcion.grupo
    evento = inscripcion.evento
    user_profile = request.user.userprofile

    # Verificar que el grupo pertenece a la institución del usuario
    if grupo.usuario_creador != request.user:
        messages.error(request, "❌ No tienes permiso para cancelar esta inscripción.")
        return redirect("detalle_evento_inscripcion", evento_id=evento.id)

    # Solo se puede cancelar si el evento sigue abierto
    if evento.estado_evento != EstadoEvento.ABIERTO:
        messages.error(
            request,
            f"❌ No se puede cancelar la inscripción: el evento está en estado '{evento.get_estado_evento_display()}'.",
        )
        return redirect("detalle_evento_inscripcion", evento_id=evento.id)

    # El grupo no debe estar bloqueado (evento finalizado lo bloquea)
    if grupo.estado_grupo == "bloqueado":
        messages.error(request, "❌ El equipo está bloqueado y no puede desvincularse.")
        return redirect("detalle_evento_inscripcion", evento_id=evento.id)

    try:
        with transaction.atomic():
            inscripcion.delete()
            grupo.estado_grupo = "editable"
            grupo.evento = None
            grupo.save(update_fields=["estado_grupo", "evento"])
        messages.success(
            request,
            f"✅ Inscripción del equipo '{grupo.nombre}' cancelada. El equipo está disponible nuevamente.",
        )
    except Exception:
        messages.error(
            request, "❌ Error al cancelar la inscripción. Intenta nuevamente."
        )

    return redirect("detalle_evento_inscripcion", evento_id=evento.id)


@login_required
def cancelar_inscripcion_grupo_admin(request, inscripcion_id):
    """
    Cancela la inscripción de un grupo desde el panel de administración (fed_central).
    Revierte el estado del grupo, desvincula del evento y envía notificación al creador.
    """
    if request.method != "POST":
        return redirect("admin_eventos")

    if request.user.userprofile.user_type not in ["fed_central", "tecnologico"]:
        messages.error(request, "❌ No tienes permiso para realizar esta acción.")
        return redirect("admin_eventos")

    inscripcion = get_object_or_404(
        InscripcionGrupoEvento.objects.select_related("grupo", "evento"),
        id=inscripcion_id,
        activo=True,
    )

    grupo = inscripcion.grupo
    evento = inscripcion.evento
    observacion = request.POST.get("observacion", "").strip()

    if not observacion:
        messages.error(
            request, "❌ Debes ingresar una observación para cancelar la inscripción."
        )
        return redirect("detalle_evento_gestion_admin", evento_id=evento.id)

    if grupo.estado_grupo == "bloqueado":
        messages.error(request, "❌ El equipo está bloqueado y no puede desvincularse.")
        return redirect("detalle_evento_gestion_admin", evento_id=evento.id)

    try:
        with transaction.atomic():
            inscripcion.delete()
            grupo.estado_grupo = "editable"
            grupo.evento = None
            grupo.save(update_fields=["estado_grupo", "evento"])

            Notificacion.objects.create(
                destinatario=grupo.usuario_creador,
                tipo="sistema",
                titulo=f"Inscripción cancelada: {evento.nombre}",
                mensaje=(
                    f"La Federación ha cancelado la inscripción del equipo «{grupo.nombre}» "
                    f"en el evento «{evento.nombre}».\n\n"
                    f"Motivo: {observacion}\n\n"
                    f"El equipo queda disponible para inscribirse en otros eventos."
                ),
            )

        messages.success(
            request,
            f"✅ Inscripción del equipo '{grupo.nombre}' cancelada. Se notificó a la institución.",
        )
    except Exception:
        messages.error(
            request, "❌ Error al cancelar la inscripción. Intenta nuevamente."
        )

    return redirect("detalle_evento_gestion_admin", evento_id=evento.id)


def home(request):
    """Página principal con opciones de login y registro"""
    return render(request, "users/home.html")


@login_required
@login_required
@require_http_methods(["POST"])
def verificar_participante_duplicado(request):
    """
    Vista AJAX para verificar si existe un participante con datos similares.
    Busca por: cédula personal, cédula escolar, o combinación de nombres+apellidos+fecha_nacimiento

    NUEVO: Retorna información de vinculación con la institución actual.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nombres = data.get("nombres", "").strip()
            apellidos = data.get("apellidos", "").strip()
            fecha_nacimiento = data.get("fecha_nacimiento")
            cedula_personal = data.get("cedula_personal", "").strip()
            cedula_escolar = data.get("cedula_escolar", "").strip()

            # Obtener institución del usuario actual
            perfil = request.user.userprofile
            institucion_actual = perfil.institution

            # Buscar duplicados
            participante_existente = None

            # 1. Buscar por cédula personal (SOLO NÚMEROS en BD)
            if cedula_personal:
                cedula_limpia = "".join(filter(str.isdigit, cedula_personal))
                if cedula_limpia:
                    participante_existente = Participante.objects.filter(
                        cedula=cedula_limpia
                    ).first()

            # 2. Buscar por cédula escolar (SOLO NÚMEROS en BD)
            if not participante_existente and cedula_escolar:
                cedula_escolar_limpia = "".join(filter(str.isdigit, cedula_escolar))
                if cedula_escolar_limpia:
                    participante_existente = Participante.objects.filter(
                        cedula_escolar=cedula_escolar_limpia
                    ).first()

            # 3. Buscar por nombres + apellidos + fecha de nacimiento
            if (
                not participante_existente
                and nombres
                and apellidos
                and fecha_nacimiento
            ):
                participante_existente = Participante.objects.filter(
                    nombres__iexact=nombres,
                    apellidos__iexact=apellidos,
                    fecha_nacimiento=fecha_nacimiento,
                ).first()

            if participante_existente:
                # Verificar si ya está vinculado a la institución actual
                vinculacion = ParticipanteInstitucion.objects.filter(
                    participante=participante_existente, institucion=institucion_actual
                ).first()
                instituciones_vinculadas = (
                    participante_existente.get_instituciones_activas()
                )
                puede_ver_detalle_ampliado = JurisdictionSelector.es_federacion(perfil)

                instituciones_nombres = []
                if puede_ver_detalle_ampliado:
                    instituciones_nombres = [
                        inst.nombre for inst in instituciones_vinculadas
                    ]

                return JsonResponse(
                    {
                        "existe": True,
                        "participante_id": str(participante_existente.id),
                        "ya_vinculado": vinculacion is not None,
                        "vinculacion_activa": vinculacion.status == "activo"
                        if vinculacion
                        else False,
                        "instituciones_vinculadas": instituciones_nombres,
                        "total_instituciones": instituciones_vinculadas.count(),
                        "datos": {
                            "nombres": participante_existente.nombres,
                            "apellidos": participante_existente.apellidos,
                            "fecha_nacimiento": participante_existente.fecha_nacimiento.strftime(
                                "%Y-%m-%d"
                            ),
                            "cedula": _mask_identifier_tail(
                                participante_existente.cedula,
                                prefix=f"{participante_existente.nacionalidad or 'V'}-",
                            ),
                            "cedula_escolar": _mask_identifier_tail(
                                participante_existente.cedula_escolar,
                                prefix="E-",
                            ),
                            "edad": participante_existente.edad,
                        },
                    }
                )
            else:
                return JsonResponse({"existe": False})

        except Exception:
            logger.exception(
                "Error verificando participante duplicado para user_id=%s",
                getattr(request.user, "id", None),
            )
            return JsonResponse(
                {"error": "Ocurrió un error interno al verificar el participante."},
                status=500,
            )

    return JsonResponse({"error": "Método no permitido"}, status=405)


@login_required
@require_http_methods(["POST"])
def vincular_participante_existente(request):
    """
    Vista AJAX para vincular un participante existente a la institución actual.

    Permite agregar participantes que ya existen en el sistema pero no están
    vinculados a la institución actual.
    """
    try:
        data = json.loads(request.body)
        participante_id = data.get("participante_id")

        if not participante_id:
            return JsonResponse(
                {"success": False, "error": "ID de participante requerido"}, status=400
            )

        # Obtener participante
        participante = get_object_or_404(Participante, id=participante_id)

        # Obtener institución del usuario actual
        try:
            perfil = request.user.userprofile
        except UserProfile.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "No tienes un perfil configurado"},
                status=400,
            )

        # Validar que el usuario sea institucional y tenga institución asignada
        if perfil.user_type != "institucional":
            return JsonResponse(
                {
                    "success": False,
                    "error": "Solo usuarios institucionales pueden vincular participantes",
                },
                status=403,
            )

        institucion = perfil.institution
        if not institucion:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Tu usuario no tiene una institución asignada. Contacta al administrador.",
                },
                status=400,
            )

        # Verificar si ya existe vinculación
        vinculacion_existente = ParticipanteInstitucion.objects.filter(
            participante=participante, institucion=institucion
        ).first()

        if vinculacion_existente:
            if vinculacion_existente.status == "activo":
                return JsonResponse(
                    {
                        "success": False,
                        "error": "El participante ya está vinculado activamente a tu institución",
                    },
                    status=400,
                )
            else:
                # Reactivar vinculación existente
                vinculacion_existente.status = "activo"
                vinculacion_existente.fecha_desvinculacion = None
                vinculacion_existente.registrado_por = request.user
                vinculacion_existente.save()

                messages.success(
                    request,
                    f'✅ Participante "{participante.nombre_completo}" reactivado en tu institución.',
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Participante reactivado exitosamente",
                        "accion": "reactivado",
                    }
                )

        # Crear nueva vinculación
        with transaction.atomic():
            ParticipanteInstitucion.objects.create(
                participante=participante,
                institucion=institucion,
                status="activo",
                registrado_por=request.user,
            )

            messages.success(
                request,
                f'✅ Participante "{participante.nombre_completo}" vinculado exitosamente a tu institución.',
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Participante vinculado exitosamente",
                    "accion": "vinculado",
                }
            )

    except Participante.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Participante no encontrado"}, status=404
        )
    except Exception:
        logger.exception(
            "Error vinculando participante existente. user_id=%s participante_id=%s",
            request.user.id,
            locals().get("participante_id"),
        )
        return JsonResponse(
            {
                "success": False,
                "error": "Ocurrió un error interno al vincular el participante.",
            },
            status=500,
        )


@login_required
@fed_central_cannot_create(redirect_to="lista_participantes")
def crear_participante(request):
    """
    Vista optimizada para registrar participantes.
    """
    perfil = request.user.userprofile
    user_type = perfil.user_type
    institucion = perfil.institution

    # Validaciones básicas
    if user_type == "institucional" and not institucion:
        messages.error(request, "No tienes una institución asignada.")
        return redirect("dashboard")

    # Obtener contexto territorial mediante Selectors
    estado_base = ParticipanteSelector.get_estado_para_formulario(perfil, institucion)
    es_admin_central = JurisdictionSelector.es_rector(perfil)

    # Determinar estado seleccionado (POST o base)
    estado_id = request.POST.get("estado")
    if estado_id:
        estado_seleccionado = get_object_or_404(Estado, id=estado_id)
    else:
        estado_seleccionado = estado_base

    context = {
        "participante_form": ParticipanteRegistrationForm(
            request.POST or None,
            initial={"estado": estado_seleccionado.id} if estado_seleccionado else None,
            user_role=user_type,
            user_institution=institucion,
        ),
        "municipios": ParticipanteSelector.get_municipios_para_formulario(
            estado_seleccionado
        ),
        "institucion": institucion,
        "nombre_sede": ParticipanteSelector.get_nombre_sede(perfil, institucion),
        "estado": estado_seleccionado,
        "todos_estados": ParticipanteSelector.get_todos_estados_para_formulario(perfil),
        "es_admin_central": es_admin_central,
        "user_role": user_type,
    }

    if request.method == "POST":
        form = context["participante_form"]
        if form.is_valid():
            try:
                participante = ParticipanteService.crear_participante_con_usuario(
                    cleaned_data=form.cleaned_data,
                    institucion=institucion,
                    registrado_por=request.user,
                    user_type_registrador=user_type,
                    tipo_vinculacion=form.cleaned_data.get(
                        "tipo_vinculacion", "institucional"
                    ),
                    estado_vinculacion=form.cleaned_data.get("vinculacion_estado"),
                )
                messages.success(
                    request,
                    f'✅ Participante "{participante.nombres} {participante.apellidos}" registrado.',
                )
                return redirect("lista_participantes")
            except ValueError as ve:
                messages.error(request, f"❌ {str(ve)}")
            except Exception:
                logger.exception(
                    "Error creando participante desde crear_participante. user_id=%s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "❌ Ocurrió un error interno al registrar el participante. Intenta nuevamente.",
                )

    return render(request, "users/register.html", context)


def register(request):
    """Vista de registro de participante compatible con campos de 7 dígitos"""

    if (
        not request.user.is_authenticated
        or request.user.userprofile.user_type != "institucional"
    ):
        messages.error(request, "No tienes permisos para registrar participantes.")
        return redirect("login")

    perfil_inst = request.user.userprofile.institution
    estado_inst = perfil_inst.estado
    municipios = Municipio.objects.filter(estado=estado_inst).order_by("nombre")

    # ============================================
    # FIX: Obtener nombre de sede para mostrar en el template
    # ============================================
    nombre_sede = None
    if perfil_inst:
        nombre_sede = perfil_inst.nombre
        if hasattr(perfil_inst, "estado") and perfil_inst.estado:
            nombre_sede = f"{perfil_inst.nombre} ({perfil_inst.estado.nombre})"

    if request.method == "POST":
        participante_form = ParticipanteRegistrationForm(
            request.POST,
            initial={"estado": estado_inst.id} if estado_inst else None,
            user_role="institucional",
            user_institution=perfil_inst,
        )

        if participante_form.is_valid():
            try:
                # Usar el servicio pasándole los cleaned_data
                participante = ParticipanteService.crear_participante_con_usuario(
                    cleaned_data=participante_form.cleaned_data,
                    institucion=perfil_inst,
                    registrado_por=request.user,
                    user_type_registrador="institucional",
                    tipo_vinculacion=participante_form.cleaned_data.get(
                        "tipo_vinculacion", "institucional"
                    ),
                    estado_vinculacion=participante_form.cleaned_data.get(
                        "vinculacion_estado"
                    ),
                )

                messages.success(
                    request, f"¡Éxito! Participante {participante.nombres} registrado."
                )
                return redirect("lista_participantes")

            except ValueError as ve:
                messages.error(request, f"❌ {str(ve)}")
            except Exception:
                logger.exception(
                    "Error creando participante desde register legacy. user_id=%s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "❌ Ocurrió un error interno al registrar el participante. Intenta nuevamente.",
                )
    else:
        participante_form = ParticipanteRegistrationForm(
            initial={"estado": estado_inst.id} if estado_inst else None,
            user_role="institucional",
            user_institution=perfil_inst,
        )

    return render(
        request,
        "users/register.html",
        {
            "participante_form": participante_form,
            "municipios": municipios,
            "institucion": perfil_inst,
            "nombre_sede": nombre_sede,
            "estado": estado_inst,
            "estado_id": estado_inst.id if estado_inst else None,
            "user_role": "institucional",
        },
    )


def custom_login(request):
    """Vista de login personalizada con redirección para superusuarios"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)

                # Si es superusuario, redirigir al admin de Django
                if user.is_superuser:
                    messages.success(request, f"¡Bienvenido Superusuario, {username}!")
                    return redirect("/admin/")

                # Para otros usuarios, continuar con la lógica normal
                try:
                    profile = user.userprofile
                    user_type = profile.user_type
                except UserProfile.DoesNotExist:
                    if user.is_staff:
                        user_type = "admin"
                    else:
                        user_type = "participante"

                messages.success(request, f"¡Bienvenido de nuevo, {username}!")
                return redirect("dashboard")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()

    return render(request, "users/login.html", {"form": form})


@login_required
def dashboard(request):
    """Router principal del dashboard con soberanía territorial completa"""
    # Los superusuarios SOLO pueden acceder al admin de Django
    if request.user.is_superuser:
        messages.warning(
            request,
            "Como superusuario, solo puedes acceder al panel de administración.",
        )
        return redirect("/admin/")

    try:
        user_profile = request.user.userprofile
        user_type = user_profile.user_type
        user_estado = user_profile.estado
    except Exception:  # Captura si no existe perfil
        messages.error(request, "No tienes un perfil configurado.")
        return redirect("login")

    # --- LÓGICA PARA ADMINISTRADORES (CENTRAL Y REGIONAL) ---
    if JurisdictionSelector.es_federacion(user_profile):
        # Obtener métricas desde el servicio centralizado (Optimizado con ReportService)
        metrics = ReportService.get_dashboard_stats(user_type, user_estado)

        context = {
            "perfil": user_profile,
            "user_type": user_type,
            "es_central": JurisdictionSelector.es_rector(user_profile),
            "es_regional": user_type == "fed_regional",
            "meses_labels": [
                "Ene",
                "Feb",
                "Mar",
                "Abr",
                "May",
                "Jun",
                "Jul",
                "Ago",
                "Sep",
                "Oct",
                "Nov",
                "Dic",
            ],
            **metrics,
        }
        return render(request, "users/dashboard_admin.html", context)

    # --- REDIRECCIÓN PARA USUARIOS NO ADMINISTRATIVOS ---
    if user_type == "institucional":
        return redirect("dashboard_institucional")
    elif user_type == "participante":
        return redirect("dashboard_participante")

    messages.error(request, "Tipo de usuario no reconocido o acceso denegado.")
    return redirect("home")


@login_required
@not_superuser_required
def dashboard_participante(request):
    """Panel de control exclusivo para participantes"""

    user_profile = request.user.userprofile

    if user_profile.user_type != "participante":
        # Redirigir directamente al dashboard institucional si es el caso
        if user_profile.user_type == "institucional":
            return redirect("dashboard_institucional")
        return redirect("dashboard")

    context = {
        "user": request.user,
        "user_profile": user_profile,
    }

    try:
        participante = Participante.objects.get(user=request.user)
        context["participante"] = participante
    except Participante.DoesNotExist:
        context["participante"] = None

    return render(request, "users/dashboard_participante.html", context)


def crear_usuario_institucional(request, institucion_id):
    # Aquí iría la lógica para crear el usuario asociado a la institución
    # Por ahora, puedes poner un pass o un return básico para que el servidor arranque
    return render(request, "users/algun_template.html")


@login_required
@not_superuser_required
def dashboard_institucional(request):
    try:
        user_profile = request.user.userprofile
    except AttributeError:
        messages.error(request, "No se encontró un perfil asociado a tu cuenta.")
        return redirect("dashboard")

    if user_profile.user_type != "institucional" or not user_profile.institution:
        messages.warning(request, "Acceso restringido a cuentas institucionales.")
        return redirect("dashboard")

    # Obtener métricas desde el servicio (Optimizado con ReportService)
    institution = user_profile.institution
    metrics = ReportService.get_institutional_stats(request.user, institution)

    context = {"institution": institution, **metrics}
    return render(request, "users/dashboard_institucional.html", context)


@login_required
def exportar_participantes_excel(request):
    """Exporta datos de participantes a Excel según permisos del usuario"""

    perfil = request.user.userprofile
    user_type = perfil.user_type

    # 1. Obtener participantes según permisos mediante Selector
    participantes = ParticipanteSelector.get_participantes_para_perfil(perfil)

    if not participantes and user_type not in [
        "fed_central",
        "tecnologico",
        "fed_regional",
        "institucional",
    ]:
        messages.error(request, "No tienes permisos para exportar participantes.")
        return redirect("dashboard")

    # 2. Aplicar filtros si existen en el GET (reutilizar lógica de lista_participantes)
    q = request.GET.get("q")
    participantes = ParticipanteSelector.buscar_participantes(participantes, q)

    estado_f = request.GET.get("estado")
    if estado_f and user_type != "fed_regional":
        participantes = participantes.filter(estado_id=estado_f)

    # Optimizar consulta
    participantes = participantes.select_related("estado", "municipio", "parroquia")

    # Preparar datos para Excel
    data = []
    for p in participantes:
        # Cédula: personal o escolar
        cedula = (
            f"{p.nacionalidad or 'V'}-{p.cedula}"
            if p.cedula
            else (f"E-{p.cedula_escolar}" if p.cedula_escolar else "Sin cédula")
        )

        # Obtener institución desde vinculación activa
        vinculacion = (
            p.vinculaciones.filter(status="activo")
            .select_related("institucion")
            .first()
        )
        institucion_nombre = (
            vinculacion.institucion.nombre if vinculacion else "Federación"
        )

        data.append(
            {
                "Nombres": p.nombres,
                "Apellidos": p.apellidos,
                "Cédula": cedula,
                "Edad": p.edad,
                "Sexo": p.get_sexo_display(),
                "Nacionalidad": p.get_nacionalidad_display(),
                "Email": p.email,
                "Teléfono": f"{p.codigo_area}-{p.numero_telefono}"
                if p.numero_telefono
                else "",
                "Condición TEA": "Sí" if p.condicion_tea else "No",
                "Estado": p.estado.nombre if p.estado else "",
                "Municipio": p.municipio.nombre if p.municipio else "",
                "Parroquia": p.parroquia.nombre if p.parroquia else "",
                "Dirección": p.direccion,
                "Nivel Educativo": p.get_grado_escolar_display()
                if p.grado_escolar
                else "",
                "Institución": institucion_nombre,
                "Representante Legal": p.nombre_representante or "",
                "Teléfono Representante": f"{p.codigo_area_representante}-{p.numero_telefono_representante}"
                if p.numero_telefono_representante
                else "",
                "Fecha Registro": p.fecha_registro.strftime("%Y-%m-%d %H:%M")
                if hasattr(p, "fecha_registro") and p.fecha_registro
                else "",
            }
        )

    # Crear DataFrame
    df = pd.DataFrame(data)

    # Crear respuesta HTTP con nombre dinámico mediante Selector
    filename = f"Participantes_{ParticipanteSelector.get_nombre_sede(perfil) or 'Padron_Nacional'}.xlsx".replace(
        " ", "_"
    )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # Escribir a Excel
    df.to_excel(response, index=False, engine="openpyxl")
    return response


@admin_required
def ver_logs_sistema(request):
    # Usamos LogEntry de Django para mostrar las últimas acciones del panel
    logs = LogEntry.objects.all().select_related("user", "content_type")[:100]
    return render(request, "users/logs_sistema.html", {"logs": logs})


def create_institutional_user(request):
    """Redirige al formulario unificado de institución"""
    messages.info(
        request,
        "Ahora el registro de instituciones incluye la creación de usuarios automáticamente.",
    )
    return redirect("registrar_institucion")


@never_cache
@admin_required
def lista_instituciones(request):
    perfil = request.user.userprofile
    user_type = perfil.user_type

    # 1. Obtener Queryset filtrado por Selector
    instituciones_qs = InstitucionSelector.get_instituciones_para_perfil(perfil)

    # 2. KPIs calculados por Selector
    stats = InstitucionSelector.get_stats_instituciones(instituciones_qs)

    # 3. Construcción de lista con usuarios
    instituciones_con_usuarios = InstitucionSelector.get_instituciones_con_usuarios(
        instituciones_qs
    )

    context = {
        "instituciones_con_usuarios": instituciones_con_usuarios,
        "total_instituciones": stats["total"],
        "instituciones_activas": stats["activas"],
        "instituciones_pendientes": stats["pendientes"],
        "estados": Estado.objects.all(),
        "es_central": user_type == "fed_central",
        "es_regional": user_type == "fed_regional",
        "perfil": perfil,
    }
    return render(request, "users/lista_instituciones.html", context)


def registrar_institucion(request):
    """
    Registro de instituciones con detección de jurisdicción regional.
    """
    perfil_admin = (
        getattr(request.user, "userprofile", None)
        if request.user.is_authenticated
        else None
    )

    # Roles y Permisos mediante Selector
    es_central = JurisdictionSelector.es_rector(perfil_admin)
    es_regional = (perfil_admin.user_type == "fed_regional") if perfil_admin else False
    es_federacion = JurisdictionSelector.es_federacion(perfil_admin)

    # Template dinámico
    base_template = "users/base_dashboard.html" if es_federacion else "base.html"

    if request.method == "POST":
        form = InstitucionRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # ⚡ Verificar si se reactivó una institución eliminada
                if hasattr(form, "_institucion_reactivada"):
                    institucion = form._institucion_reactivada
                    messages.warning(
                        request,
                        f"✅ La institución '{institucion.nombre}' ha sido reactivada exitosamente.\n\n"
                        f"📋 Estado actual: Pendiente de aprobación\n"
                        f"⏰ Tiempo estimado: 24-48 horas\n\n"
                        f"Recibirás una notificación cuando la administración central la apruebe.",
                    )
                    return redirect(
                        "login"
                    )  # Redirigir al login ya que el usuario está desactivado

                # Usar el servicio para creación atómica de institución y usuario (solo para nuevas)
                institucion = InstitutionService.crear_institucion_con_usuario(
                    data=form.cleaned_data,
                    es_central=es_central,
                    es_regional=es_regional,
                    perfil_admin=perfil_admin,
                )

                if es_central:
                    messages.success(
                        request, f"Sede '{institucion.nombre}' activada con éxito."
                    )
                    return redirect("lista_instituciones")
                elif es_federacion:
                    messages.info(
                        request,
                        f"Registro de '{institucion.nombre}' enviado a Sede Central.",
                    )
                    return redirect("lista_instituciones")
                else:
                    return render(
                        request,
                        "users/registro_pendiente.html",
                        {
                            "nombre_inst": institucion.nombre,
                            "email": institucion.email,
                            "base_template": base_template,
                            "tipo_institucion": institucion.tipo_institucion,
                        },
                    )

            except Exception:
                logger.exception(
                    "Error registrando institucion. user_id=%s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "No se pudo completar el registro de la institución. Intenta nuevamente.",
                )
    else:
        # Inicialización del formulario con el estado predeterminado
        initial_data = {}
        if es_regional and perfil_admin.estado:
            initial_data["estado"] = perfil_admin.estado.id

        form = InstitucionRegistrationForm(initial=initial_data)

    context = {
        "form": form,
        "base_template": base_template,
        "dependencias": Dependencia.objects.all(),
        "es_federacion": es_federacion,
        "es_central": es_central,
        "es_regional": es_regional,
        "es_fed_central": es_central,  # Nueva variable para diseño especial
        "estado_fijo_id": perfil_admin.estado.id
        if es_regional and perfil_admin.estado
        else None,
    }

    return render(request, "users/registrar_institucion.html", context)


@login_required
@login_required
def lista_participantes(request):
    """Vista inteligente: Federación (Central/Regional) e Instituciones"""
    perfil = request.user.userprofile
    user_type = perfil.user_type
    institucion_actual = perfil.institution if user_type == "institucional" else None

    # 1. Obtener Queryset base desde Selector
    participantes = ParticipanteSelector.get_participantes_para_perfil(perfil)

    # Para institucional con filtro de status: ampliar el queryset base para incluir
    # vinculaciones no activas (el prefetch filtrará por el status solicitado)
    status_f = request.GET.get("status") if user_type == "institucional" else None
    vinc_status_filter = status_f if status_f in ["activo", "inactivo", "suspendido", "egresado"] else "activo"

    if user_type == "institucional" and perfil.institution and vinc_status_filter != "activo":
        # Reemplazar el queryset base para incluir el status solicitado
        participantes = Participante.objects.filter(
            vinculaciones__institucion=perfil.institution,
            vinculaciones__status=vinc_status_filter,
        ).distinct()

    if not participantes and user_type not in [
        "fed_central",
        "tecnologico",
        "fed_regional",
        "institucional",
    ]:
        return redirect("dashboard")

    # 2. Aplicar filtros usando el Selector
    q = request.GET.get("q")
    participantes = ParticipanteSelector.buscar_participantes(participantes, q)

    estado_f = request.GET.get("estado")
    if estado_f and user_type != "fed_regional":
        participantes = participantes.filter(estado_id=estado_f)

    sexo_f = request.GET.get("sexo")
    if sexo_f:
        participantes = participantes.filter(sexo=sexo_f)

    # 3. Lógica para Menores de Edad
    hoy = date.today()
    fecha_limite_menores = date(hoy.year - 18, hoy.month, hoy.day)

    # 4. Métricas KPI
    stats = participantes.aggregate(
        total_participantes=Count("id", distinct=True),
        participantes_hombres=Count("id", filter=Q(sexo="M"), distinct=True),
        participantes_mujeres=Count("id", filter=Q(sexo="F"), distinct=True),
        menores_edad=Count(
            "id", filter=Q(fecha_nacimiento__gt=fecha_limite_menores), distinct=True
        ),
    )

    # 5. Cargar vinculaciones filtrando por el status solicitado
    from django.db.models import Prefetch

    # Para institucional: filtrar el prefetch por su institución Y el status pedido
    # Para otros roles: solo filtrar por status activo (siempre)
    if user_type == "institucional" and institucion_actual:
        prefetch_filter = Q(status=vinc_status_filter, institucion=institucion_actual)
    else:
        prefetch_filter = Q(status="activo")

    vinculaciones_prefetch = Prefetch(
        "vinculaciones",
        queryset=(
            ParticipanteInstitucion.objects.filter(prefetch_filter)
            .select_related("institucion", "estado")
            .order_by("-fecha_vinculacion")
        ),
        to_attr="vinculaciones_activas",
    )

    participantes = participantes.order_by("-fecha_registro").prefetch_related(
        vinculaciones_prefetch
    )

    # 6. Procesar vinculaciones según el rol de usuario
    for p in participantes:
        vinculaciones_activas = getattr(p, "vinculaciones_activas", [])

        if user_type == "institucional" and institucion_actual:
            # Para usuarios institucionales: mostrar SOLO su vinculación con su institución
            vinculacion_suya = next(
                (
                    v
                    for v in vinculaciones_activas
                    if v.institucion_id == institucion_actual.id
                ),
                None,
            )

            if vinculacion_suya:
                p.institucion = vinculacion_suya.institucion
                p.vinculacion_tipo = vinculacion_suya.tipo_vinculacion
                p.vinculacion_status = vinculacion_suya.status
                p.todas_vinculaciones = [vinculacion_suya]  # Solo la de su institución
            else:
                # No debería alcanzarse porque ParticipanteSelector ya filtra por institución
                p.institucion = type(
                    "obj",
                    (object,),
                    {"nombre": "No vinculado", "tipo_institucion": "N/A"},
                )()
                p.vinculacion_tipo = "ninguna"
                p.todas_vinculaciones = []
        else:
            # Para fed_central, fed_regional, etc: mostrar TODAS las vinculaciones
            p.todas_vinculaciones = vinculaciones_activas

            if vinculaciones_activas:
                # Primera vinculación como principal (para compatibilidad con template)
                vinculacion = vinculaciones_activas[0]
                p.vinculacion_tipo = vinculacion.tipo_vinculacion
                p.vinculacion_status = vinculacion.status

                if (
                    vinculacion.tipo_vinculacion == "institucional"
                    and vinculacion.institucion
                ):
                    p.institucion = vinculacion.institucion
                elif vinculacion.tipo_vinculacion == "regional" and vinculacion.estado:
                    p.institucion = type(
                        "obj",
                        (object,),
                        {
                            "nombre": f"Federación Regional ({vinculacion.estado.nombre})",
                            "tipo_institucion": "federacion",
                        },
                    )()
                else:
                    p.institucion = type(
                        "obj",
                        (object,),
                        {
                            "nombre": "Federación Central",
                            "tipo_institucion": "federacion",
                        },
                    )()
            else:
                # Sin vinculación
                p.vinculacion_tipo = "central"
                p.institucion = type(
                    "obj",
                    (object,),
                    {"nombre": "Federación", "tipo_institucion": "federacion"},
                )()
                p.todas_vinculaciones = []

    context = {
        "participantes": participantes,
        "total_participantes": stats.get("total_participantes", 0) or 0,
        "participantes_hombres": stats.get("participantes_hombres", 0) or 0,
        "participantes_mujeres": stats.get("participantes_mujeres", 0) or 0,
        "menores_edad": stats.get("menores_edad", 0) or 0,
        "estados": Estado.objects.all().order_by("nombre"),
        "es_central": user_type == "fed_central",
        "es_regional": user_type == "fed_regional",
        "es_institucional": user_type == "institucional",
        "perfil": perfil,
        "user_type": user_type,
    }
    return render(request, "users/lista_participantes.html", context)


@login_required
def editar_participante(request, pk):
    """
    Vista optimizada para editar participantes.
    """
    perfil = request.user.userprofile
    user_type = perfil.user_type
    institucion = perfil.institution
    participante = get_object_or_404(
        ParticipanteSelector.get_participantes_visibles_para_usuario(request.user),
        pk=pk,
    )

    # Preparar contexto usando Selectors
    context = {
        "participante_form": ParticipanteRegistrationForm(
            request.POST or None,
            instance=participante,
            initial={"estado": participante.estado.id} if participante.estado else None,
            user_role=user_type,
            user_institution=institucion,
        ),
        "participante": participante,
        "perfil": perfil,
        "edad": participante.edad,
        "cedula_personal": "".join(filter(str.isdigit, str(participante.cedula)))
        if participante.cedula
        else "",
        "cedula_escolar": participante.cedula_escolar or "",
        "estado": participante.estado,
        "estado_id": participante.estado.id if participante.estado else None,
        "municipio": participante.municipio,
        "municipios": ParticipanteSelector.get_municipios_para_formulario(
            participante.estado
        ),
        "parroquias": Parroquia.objects.filter(
            municipio=participante.municipio
        ).order_by("nombre")
        if participante.municipio
        else [],
        "todos_estados": ParticipanteSelector.get_todos_estados_para_formulario(perfil),
        "es_admin_central": JurisdictionSelector.es_rector(perfil),
        "user_role": user_type,
    }

    if request.method == "POST":
        form = context["participante_form"]
        if form.is_valid():
            try:
                ParticipanteService.actualizar_participante(
                    participante=participante, cleaned_data=form.cleaned_data
                )
                messages.success(
                    request, f'✅ Datos de "{participante.nombres}" actualizados.'
                )
                return redirect("lista_participantes")
            except Exception:
                logger.exception(
                    "Error actualizando participante. user_id=%s participante_id=%s",
                    request.user.id,
                    participante.id,
                )
                messages.error(
                    request,
                    "❌ Ocurrió un error interno al actualizar el participante.",
                )
        else:
            messages.error(
                request,
                "❌ No se pudo actualizar el participante. Verifica los datos resaltados.",
            )

    return render(request, "users/participante_editar_full.html", context)


@admin_required
def admin_crear_institucion(request):
    if request.method == "POST":
        form = InstitucionRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Usar el servicio para creación administrativa (forzar activa=True)
                data = form.cleaned_data.copy()
                data["activa"] = True
                data["estatus"] = "aprobado"

                InstitutionService.crear_institucion_con_usuario(
                    data=data, es_central=True
                )

                messages.success(
                    request, "Institución creada y activada correctamente."
                )
                return redirect("lista_instituciones")
            except Exception:
                logger.exception(
                    "Error creando institucion desde admin. user_id=%s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "No se pudo crear la institución. Intenta nuevamente.",
                )
    else:
        form = InstitucionRegistrationForm()

    return render(request, "users/admin_crear_institucion.html", {"form": form})


class ParticipanteUpdateView(UpdateView):
    # Modelo que se va a editar
    model = Participante

    # Formulario que se va a usar
    form_class = ParticipanteRegistrationForm

    # Plantilla que mostrará el formulario
    template_name = "users/participante_editar.html"

    # Define a dónde ir después de guardar los cambios
    def get_success_url(self):
        return reverse("dashboard")


@login_required
def estadisticas_por_estado(request):
    return render(request, "users/estadisticas_estados.html")


@login_required
def crear_evento(request):
    """
    Vista unificada para crear eventos.
    """
    perfil = request.user.userprofile
    user_type = perfil.user_type

    # Determinar si es federación mediante Selector
    es_federacion = JurisdictionSelector.es_federacion(perfil)

    # Obtener institución (solo si es institucional)
    institution = perfil.institution if user_type == "institucional" else None

    # Manejar pre-selección de club vía GET
    club_preseleccionado_id = request.GET.get("club_id")
    valores_iniciales = {}
    if club_preseleccionado_id:
        valores_iniciales = {
            "club_organizador": club_preseleccionado_id,
            "tipo_evento": "club",
        }

    estado_institucion = EventoSelector.get_estado_contexto(perfil, institution)
    clubes_disponibles = EventoSelector.get_clubes_disponibles_para_formulario(perfil)

    # Categorías predefinidas desde el modelo (Single Source of Truth)
    from registry.models import Evento

    categorias = [choice[1] for choice in Evento.TIPO_CHOICES]

    if request.method == "POST":
        try:
            # Usar el servicio para crear el evento
            evento = EventoService.crear_evento(
                user=request.user, perfil=perfil, data=request.POST
            )

            if JurisdictionSelector.es_rector(perfil):
                messages.success(
                    request,
                    f"✅ Evento '{evento.nombre}' creado y abierto exitosamente. "
                    f"Tipo: {evento.tipo_evento.upper()}. "
                    f"Visible para: {evento.get_audiencia_display()}.",
                )
                return redirect("admin_eventos")
            else:
                tipo_msg = (
                    "de club" if evento.tipo_evento == "club" else "institucional"
                )
                messages.success(
                    request,
                    f"✅ Evento {tipo_msg} '{evento.nombre}' creado en BORRADOR. "
                    "Envíalo a revisión cuando esté listo para aprobación de Federación Venezolana de Robótica Creativa.",
                )
                return redirect("mis_eventos")

        except ValueError as ve:
            messages.error(request, f"❌ {str(ve)}")
            return _render_formulario_evento(
                request,
                perfil=perfil,
                valores_previos=request.POST,
            )
        except Exception:
            logger.exception(
                "Error creando evento. user_id=%s",
                request.user.id,
            )
            messages.error(
                request,
                "❌ Ocurrió un error interno al crear el evento. Intenta nuevamente.",
            )
            return _render_formulario_evento(
                request,
                perfil=perfil,
                valores_previos=request.POST,
            )

    # Valores por defecto para el formulario
    valores_iniciales = {
        "estado_evento": EstadoEvento.BORRADOR,
        "modalidad": "presencial",
        "fecha_hasta": "",
    }

    # Pre-seleccionar club si se pasa en la URL (GET parameter)
    club_id_get = request.GET.get("club_id")
    if club_id_get:
        try:
            # Validar que el club_id sea válido y esté en clubes_disponibles
            if clubes_disponibles.filter(id=club_id_get).exists():
                valores_iniciales["club_organizador"] = club_id_get
                valores_iniciales["tipo_evento"] = (
                    "club"  # Si se preselecciona un club, el tipo de evento es "club"
                )
        except ValueError:
            pass  # Ignorar si club_id_get no es un entero válido

    return _render_formulario_evento(
        request,
        perfil=perfil,
        valores_previos=valores_iniciales,
    )


@login_required
def eventos_disponibles(request):
    """
    Catálogo de eventos visibles para el usuario.

    Para instituciones:
    - muestra eventos abiertos a su institución según audiencia
    - excluye sus propios eventos de la vista general
    """
    hoy = date.today()

    def _parse_fecha(valor):
        if not valor:
            return None
        try:
            return date.fromisoformat(valor)
        except (TypeError, ValueError):
            return None

    # Filtros del request.
    # Compatibilidad: el template actual envía `estado` para el estado del evento.
    # `estado_geo` queda reservado para el estado geográfico y evita mezclar semánticas.
    query = request.GET.get("q", "").strip()
    estado_evento_filtro = request.GET.get("estado_evento") or request.GET.get("estado")
    estado_geografico_filtro = request.GET.get("estado_geo") or request.GET.get(
        "estado_id"
    )
    tipo_filtro = request.GET.get("tipo")
    modalidad_filtro = request.GET.get("modalidad")
    audiencia_filtro = request.GET.get("audiencia")
    fecha_desde = _parse_fecha(request.GET.get("fecha_desde"))
    fecha_hasta = _parse_fecha(request.GET.get("fecha_hasta"))

    perfil = request.user.userprofile
    eventos = EventoSelector.get_eventos_visibles(perfil).annotate(
        total_inscritos=Count(
            "inscripciones_grupo",
            filter=Q(inscripciones_grupo__activo=True),
            distinct=True,
        )
    )

    if query:
        eventos = eventos.filter(
            Q(nombre__icontains=query)
            | Q(descripcion__icontains=query)
            | Q(tipo__icontains=query)
            | Q(institucion__nombre__icontains=query)
            | Q(club_organizador__nombre__icontains=query)
        )

    if estado_evento_filtro:
        eventos = eventos.filter(estado_evento=estado_evento_filtro)

    if estado_geografico_filtro:
        eventos = eventos.filter(estado_id=estado_geografico_filtro)

    if tipo_filtro:
        eventos = eventos.filter(tipo=tipo_filtro)

    if modalidad_filtro:
        eventos = eventos.filter(modalidad=modalidad_filtro)

    if audiencia_filtro:
        eventos = eventos.filter(audiencia=audiencia_filtro)

    if fecha_desde:
        eventos = eventos.filter(
            Q(fecha_hasta__gte=fecha_desde)
            | Q(fecha_hasta__isnull=True, fecha__gte=fecha_desde)
        )

    if fecha_hasta:
        eventos = eventos.filter(fecha__lte=fecha_hasta)

    eventos_con_inscritos = list(eventos.order_by("fecha", "nombre").distinct())

    eventos_hoy = [
        e for e in eventos_con_inscritos if e.fecha <= hoy <= e.fecha_fin_efectiva
    ]
    eventos_proximos = [e for e in eventos_con_inscritos if e.fecha > hoy]
    eventos_pasados = sorted(
        [e for e in eventos_con_inscritos if e.fecha_fin_efectiva < hoy],
        key=lambda x: x.fecha,
        reverse=True,
    )[:10]
    eventos_activos = [e for e in eventos_con_inscritos if e.fecha_fin_efectiva >= hoy]

    # Agrupar por estado geográfico
    estados_con_eventos = []
    for estado in Estado.objects.all().order_by("nombre"):
        eventos_estado = [e for e in eventos_activos if e.estado_id == estado.id]
        if eventos_estado:
            estados_con_eventos.append({"estado": estado, "eventos": eventos_estado})

    # Estadísticas
    total_eventos = len(eventos_con_inscritos)
    total_activos = len(eventos_activos)

    # Obtener lista de estados geográficos para el filtro
    estados_geograficos = Estado.objects.all().order_by("nombre")

    context = {
        "estados_con_eventos": estados_con_eventos,
        "eventos_activos": eventos_activos,
        "eventos_hoy": eventos_hoy,
        "eventos_proximos": eventos_proximos,
        "eventos_pasados": eventos_pasados,
        "eventos": eventos_con_inscritos,
        "total_eventos": total_eventos,
        "total_activos": total_activos,
        "hoy": hoy,
        "today": hoy,
        "perfil": perfil,
        "filtros": {
            "q": query,
            "estado_evento": estado_evento_filtro,
            "estado": estado_geografico_filtro,
            "tipo": tipo_filtro,
            "modalidad": modalidad_filtro,
            "audiencia": audiencia_filtro,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else "",
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else "",
        },
        "tipos": Evento.TIPO_CHOICES,
        "modalidades": Evento.MODALIDAD_CHOICES,
        "audiencias": Evento.AUDIENCIA_CHOICES,
        "estados_geograficos": estados_geograficos,
    }

    return render(request, "users/eventos_disponibles.html", context)


@admin_required
def gestionar_eventos_institucion(request):
    """
    Tablero Administrativo de Eventos (Federación).
    """
    perfil = request.user.userprofile
    user_type = perfil.user_type
    hoy = date.today()

    # Redirección de seguridad para instituciones
    if user_type == "institucional":
        return redirect("mis_eventos")

    # Actualizar estados automáticos (Mover a un comando o servicio cron si es posible, pero mantener aquí por ahora)
    eventos_a_actualizar = Evento.objects.filter(
        fecha__lte=hoy,
        estado_evento__in=[EstadoEvento.ABIERTO, EstadoEvento.EN_PROCESO],
    )
    for evento in eventos_a_actualizar:
        evento.actualizar_estado_por_fecha()

    # === VISIBILIDAD ADMINISTRATIVA MEDIANTE SELECTOR ===
    # Mantener en listado los eventos activos y los cancelados (para trazabilidad). Eliminados siguen ocultos.
    # Regla: Los eventos de instituciones en estado "borrador" no son visibles para fed_central hasta que se envíen a revisión
    eventos = (
        Evento.objects.select_related(
            "estado",
            "municipio",
            "parroquia",
            "institucion",
            "club_organizador",
            "club_organizador__institucion_creadora",
        )
        .filter(Q(activo=True) | Q(cancelado=True))
        .exclude(
            # Ocultar borradores de instituciones y clubes hasta que sean enviados a revisión
            Q(estado_evento=EstadoEvento.BORRADOR)
            & (Q(institucion__isnull=False) | Q(club_organizador__isnull=False))
        )
    )

    eventos = JurisdictionSelector.filtrar_por_territorio(eventos, perfil)
    es_fed_central = JurisdictionSelector.es_rector(perfil)
    institution = getattr(perfil, "institution", None)

    # Filtros adicionales desde la UI
    q_filtro = request.GET.get("q", "").strip()
    tipo_filtro = request.GET.get("tipo")
    tipo_evento_filtro = request.GET.get("tipo_evento")
    estado_evento_filtro = request.GET.get("estado_evento")
    estado_nacional_filtro = request.GET.get("estado_nacional")

    if q_filtro:
        eventos = eventos.filter(
            Q(nombre__icontains=q_filtro)
            | Q(descripcion__icontains=q_filtro)
            | Q(institucion__nombre__icontains=q_filtro)
            | Q(club_organizador__nombre__icontains=q_filtro)
        )
    if tipo_filtro:
        eventos = eventos.filter(tipo=tipo_filtro)
    if tipo_evento_filtro:
        if tipo_evento_filtro == "federacion":
            eventos = eventos.filter(
                institucion__isnull=True, club_organizador__isnull=True
            )
        else:
            eventos = eventos.filter(tipo_evento=tipo_evento_filtro)
    if estado_evento_filtro:
        if estado_evento_filtro == "cancelado":
            eventos = eventos.filter(cancelado=True)
        else:
            eventos = eventos.filter(
                estado_evento=estado_evento_filtro, cancelado=False
            )

    # Filtro por estado geográfico (ubicación del evento)
    if estado_nacional_filtro:
        eventos = eventos.filter(estado_id=estado_nacional_filtro)

    eventos = eventos.annotate(
        total_inscritos=Count(
            "inscripciones_grupo",
            filter=Q(inscripciones_grupo__activo=True),
            distinct=True,
        )
    ).order_by("-fecha_creacion")

    # Estadísticas Globales
    stats = eventos.aggregate(
        total=Count("id"),
        borrador=Count("id", filter=Q(estado_evento=EstadoEvento.BORRADOR)),
        revision=Count("id", filter=Q(estado_evento=EstadoEvento.REVISION)),
        abiertos=Count("id", filter=Q(estado_evento=EstadoEvento.ABIERTO)),
        rechazados=Count("id", filter=Q(estado_evento=EstadoEvento.RECHAZADO)),
        activos=Count(
            "id",
            filter=Q(
                estado_evento=EstadoEvento.ABIERTO, fecha__gt=hoy, cancelado=False
            ),
        ),
        en_proceso=Count("id", filter=Q(estado_evento=EstadoEvento.EN_PROCESO)),
        finalizados=Count("id", filter=Q(estado_evento=EstadoEvento.FINALIZADO)),
        pausados=Count("id", filter=Q(estado_evento=EstadoEvento.PAUSADO)),
        cancelados=Count("id", filter=Q(cancelado=True)),
    )

    # Métricas de dashboard administrativo
    total_inscripciones = (
        eventos.aggregate(
            total_inscripciones=Count(
                "inscripciones_grupo",
                filter=Q(inscripciones_grupo__activo=True),
            )
        )["total_inscripciones"]
        or 0
    )

    eventos_activos = eventos.filter(
        Q(fecha_hasta__gte=hoy) | Q(fecha_hasta__isnull=True, fecha__gte=hoy),
        cancelado=False,
    ).count()

    for evento in eventos:
        evento.puede_editar = True  # Admin siempre puede gestionar
        evento.puede_modificar_datos = True
        evento.puede_pausar_usuario = evento.puede_pausar(request.user)
        evento.puede_cancelar_usuario = evento.puede_cancelar(request.user)

    stats["pausados_cancelados"] = (stats.get("pausados") or 0) + (
        stats.get("cancelados") or 0
    )

    context = {
        "eventos": eventos,
        "stats": stats,
        "hoy": hoy,
        "total_inscripciones": total_inscripciones,
        "eventos_activos": eventos_activos,
        "estados": Estado.objects.all().order_by("nombre"),
        "tipos": Evento.TIPO_CHOICES,
        "estados_evento": EstadoEvento.choices,
        "es_fed_central": es_fed_central,
        "es_institucional": False,  # En esta vista administrativa
        "institution": institution,
    }

    return render(request, "users/gestionar_eventos.html", context)


@login_required
def aprobar_evento(request, evento_id):
    """
    Aprueba un evento en estado revisión.
    """
    perfil = request.user.userprofile
    if not JurisdictionSelector.es_rector(perfil):
        messages.error(request, "No tienes permiso para aprobar eventos.")
        return redirect("admin_eventos")

    evento = get_object_or_404(
        Evento, id=evento_id, estado_evento=EstadoEvento.REVISION
    )

    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()

        with transaction.atomic():
            if not evento.aprobar(request.user, observaciones):
                messages.error(
                    request, "No se puede aprobar el evento en su estado actual."
                )
                return redirect("admin_eventos")

        messages.success(request, f"Evento '{evento.nombre}' aprobado exitosamente.")
        return redirect("admin_eventos")

    return render(request, "users/aprobar_evento.html", {"evento": evento})


@login_required
def rechazar_evento(request, evento_id):
    """
    Rechaza un evento en estado revisión.
    """
    perfil = request.user.userprofile
    if not JurisdictionSelector.es_rector(perfil):
        messages.error(request, "No tienes permiso para rechazar eventos.")
        return redirect("admin_eventos")

    evento = get_object_or_404(
        Evento, id=evento_id, estado_evento=EstadoEvento.REVISION
    )

    if request.method == "POST":
        observacion = request.POST.get("observacion", "").strip()
        if not observacion:
            messages.error(
                request, "Debes proporcionar una observación para el rechazo."
            )
            return redirect("admin_eventos")

        with transaction.atomic():
            if not evento.rechazar(observaciones=observacion):
                messages.error(
                    request, "No se puede rechazar el evento en su estado actual."
                )
                return redirect("admin_eventos")

        messages.success(request, f"Evento '{evento.nombre}' rechazado.")
        return redirect("admin_eventos")

    return render(request, "users/rechazar_evento.html", {"evento": evento})


@login_required
@institucional_required
def seguimiento_eventos_institucion(request):
    """
    Vista de Mis Eventos para la institución autenticada.
    Muestra eventos:
    - Creados por la institución (eventos institucionales)
    - Creados por clubes donde la institución es creadora
    - Creados por clubes donde la institución es miembro activo
    """
    from django.db.models import Q

    perfil = request.user.userprofile
    institution = perfil.institution

    # Parámetros de filtro GET
    q = request.GET.get("q", "").strip()
    filtro_estado = request.GET.get("estado_evento", "")
    filtro_tipo = request.GET.get("tipo_evento", "")

    # Obtener IDs de clubes donde la institución es miembro activo
    from registry.models.club import MembresiaClu

    clubes_miembro_ids = list(
        MembresiaClu.objects.filter(
            institucion=institution, estado="miembro_activo"
        ).values_list("club_id", flat=True)
    )
    # Cachear en perfil para que el templatetag lo use sin N+1
    perfil._clubes_miembro_ids = set(clubes_miembro_ids)

    # Query base:
    # 1. Eventos institucionales propios
    # 2. Eventos de club creados por un usuario de esta institución (cubre tanto propietario como miembro)
    # Los eventos de club creados por OTRA institución se ven en /eventos/, no aquí.
    base_qs = (
        Evento.objects.filter(
            Q(institucion=institution)
            | Q(
                club_organizador__isnull=False,
                creado_por__userprofile__institution=institution,
            )
        )
        .select_related(
            "estado",
            "municipio",
            "institucion",
            "institucion__estado",
            "club_organizador",
            "club_organizador__institucion_creadora",
            "club_organizador__institucion_creadora__estado",
        )
        .annotate(
            total_inscritos=Count(
                "inscripciones_grupo",
                filter=Q(inscripciones_grupo__activo=True),
                distinct=True,
            )
        )
    )
    if q:
        base_qs = base_qs.filter(nombre__icontains=q)
    if filtro_tipo:
        base_qs = base_qs.filter(tipo_evento=filtro_tipo)

    ESTADOS_OTROS = [
        EstadoEvento.PAUSADO,
        EstadoEvento.CANCELADO,
        EstadoEvento.EN_PROCESO,
        EstadoEvento.FINALIZADO,
    ]

    if filtro_estado:
        # Mostrar solo el estado solicitado en su grupo correspondiente
        eventos_borrador = (
            base_qs.filter(estado_evento=EstadoEvento.BORRADOR)
            if filtro_estado == EstadoEvento.BORRADOR
            else Evento.objects.none()
        )
        eventos_revision = (
            base_qs.filter(estado_evento=EstadoEvento.REVISION)
            if filtro_estado == EstadoEvento.REVISION
            else Evento.objects.none()
        )
        eventos_abiertos = (
            base_qs.filter(estado_evento=EstadoEvento.ABIERTO)
            if filtro_estado == EstadoEvento.ABIERTO
            else Evento.objects.none()
        )
        eventos_rechazados = (
            base_qs.filter(estado_evento=EstadoEvento.RECHAZADO)
            if filtro_estado == EstadoEvento.RECHAZADO
            else Evento.objects.none()
        )
        eventos_otros = (
            base_qs.filter(estado_evento=filtro_estado)
            if filtro_estado in ESTADOS_OTROS
            else Evento.objects.none()
        )
    else:
        eventos_borrador = base_qs.filter(estado_evento=EstadoEvento.BORRADOR).order_by(
            "-fecha_creacion"
        )
        eventos_revision = base_qs.filter(estado_evento=EstadoEvento.REVISION).order_by(
            "-fecha_creacion"
        )
        eventos_abiertos = base_qs.filter(estado_evento=EstadoEvento.ABIERTO).order_by(
            "-fecha"
        )
        eventos_rechazados = base_qs.filter(
            estado_evento=EstadoEvento.RECHAZADO
        ).order_by("-fecha_creacion")
        eventos_otros = base_qs.filter(estado_evento__in=ESTADOS_OTROS).order_by(
            "-fecha"
        )

    grupos_disponibles = (
        Grupo.objects.filter(usuario_creador=request.user, activo=True)
        .prefetch_related("participantes")
        .order_by("nombre")
    )

    stats = {
        "total_borradores": eventos_borrador.count(),
        "total_revision": eventos_revision.count(),
        "total_abiertos": eventos_abiertos.count(),
        "total_rechazados": eventos_rechazados.count(),
        "total_otros": eventos_otros.count(),
        "total": Evento.objects.filter(
            Q(institucion=institution)
            | Q(
                club_organizador__isnull=False,
                creado_por__userprofile__institution=institution,
            )
        ).count(),
    }

    # Queryset unificado para el template (una sola tabla)
    if filtro_estado:
        eventos = base_qs.filter(estado_evento=filtro_estado).order_by(
            "-fecha_creacion"
        )
    else:
        eventos = base_qs.order_by("-fecha_creacion")

    context = {
        "eventos": eventos,
        "eventos_borrador": eventos_borrador,
        "eventos_revision": eventos_revision,
        "eventos_abiertos": eventos_abiertos,
        "eventos_rechazados": eventos_rechazados,
        "eventos_otros": eventos_otros,
        "grupos_disponibles": grupos_disponibles,
        "stats": stats,
        "institution": institution,
        "perfil": perfil,
        # Para repoblar filtros en el template
        "q": q,
        "filtro_estado": filtro_estado,
        "filtro_tipo": filtro_tipo,
    }

    return render(request, "users/seguimiento_eventos.html", context)


@login_required
@institucional_required
def enviar_evento_revision(request, evento_id):
    """
    Envía un evento propio de `borrador` o `rechazado` a `revision`.
    """
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Método no permitido"}, status=405
        )

    try:
        institution = request.user.userprofile.institution
        evento = _get_evento_institucional(evento_id, institution)

        if evento.estado_evento not in [EstadoEvento.BORRADOR, EstadoEvento.RECHAZADO]:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Solo puedes enviar a revisión eventos en borrador o rechazados.",
                },
                status=400,
            )

        evento.estado_evento = EstadoEvento.REVISION
        evento.save(update_fields=["estado_evento"])

        messages.success(
            request, f'✅ Evento "{evento.nombre}" enviado a revisión exitosamente'
        )
        return JsonResponse({"success": True})

    except Evento.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": "Evento no encontrado o no está disponible para envío.",
            },
            status=404,
        )
    except Exception:
        logger.exception(
            "Error enviando evento a revision. user_id=%s evento_id=%s",
            request.user.id,
            evento_id,
        )
        return JsonResponse(
            {
                "success": False,
                "error": "Ocurrió un error interno al enviar el evento a revisión.",
            },
            status=500,
        )


@login_required
@login_required
def editar_evento(request, evento_id):
    """
    Vista unificada para editar un evento existente.
    """
    perfil = request.user.userprofile
    user_type = getattr(perfil, "user_type", None)

    if EventoSelector.es_rector_eventos(perfil):
        evento = get_object_or_404(Evento, id=evento_id)
        if evento.estado_evento in [EstadoEvento.CANCELADO, EstadoEvento.FINALIZADO]:
            messages.error(
                request,
                "Los eventos cancelados o finalizados no pueden editarse desde el panel rector.",
            )
            return redirect("admin_eventos")
        redirect_destino = "admin_eventos"
    elif user_type == "institucional":
        evento = _get_evento_institucional(
            evento_id, request.user.userprofile.institution
        )
        if not evento.puede_ser_editado():
            messages.error(
                request,
                "Solo puedes editar eventos en borrador o rechazados. "
                "Para los demas estados usa las acciones de gestion correspondientes.",
            )
            return redirect("mis_eventos")
        redirect_destino = "mis_eventos"
    else:
        messages.error(request, "No tienes permisos para editar este evento.")
        return redirect("dashboard")

    if request.method == "POST":
        try:
            EventoService.actualizar_evento(
                evento=evento, perfil=perfil, data=request.POST
            )
            messages.success(
                request, f"✅ Evento '{evento.nombre}' actualizado correctamente."
            )
            return redirect(redirect_destino)
        except ValueError as ve:
            messages.error(request, f"❌ {str(ve)}")
            return _render_formulario_evento(
                request,
                perfil=perfil,
                evento=evento,
                valores_previos=request.POST,
            )
        except Exception:
            logger.exception(
                "Error actualizando evento. user_id=%s evento_id=%s",
                request.user.id,
                evento_id,
            )
            messages.error(
                request,
                "❌ Ocurrió un error interno al actualizar el evento.",
            )

    return _render_formulario_evento(request, perfil=perfil, evento=evento)


@login_required
@institucional_required
def cambiar_estado_evento(request, evento_id):
    """
    Vista institucional para cancelar un evento propio segun la maquina de estados.
    """
    if request.method == "POST":
        evento = _get_evento_institucional(
            evento_id, request.user.userprofile.institution
        )

        nuevo_estado = request.POST.get("estado_evento")
        motivo = request.POST.get("motivo", "").strip()

        if nuevo_estado == EstadoEvento.CANCELADO and evento.puede_cancelar(
            request.user
        ):
            try:
                EventoService.gestionar_estado(
                    evento=evento,
                    user=request.user,
                    nuevo_estado=EstadoEvento.CANCELADO,
                    observacion=motivo,
                )
                messages.warning(
                    request,
                    f"Evento '{evento.nombre}' cancelado correctamente.",
                )
            except ValueError as ve:
                messages.error(request, f"❌ {str(ve)}")
        elif nuevo_estado == EstadoEvento.CANCELADO:
            messages.error(request, "No tienes permiso para cancelar este evento.")
        else:
            messages.error(
                request,
                "Los cambios de estado distintos a cancelado no pueden hacerse desde esta vista.",
            )

    return redirect("admin_eventos")


@admin_required
@require_http_methods(["POST"])
def gestionar_estado_evento(request, evento_id):
    """
    Gestion centralizada de pausa, reapertura y cancelacion por ente rector.
    """
    perfil = request.user.userprofile
    if not EventoSelector.es_rector_eventos(perfil):
        messages.error(
            request, "No tienes permiso para gestionar el estado de este evento."
        )
        return redirect("admin_eventos")

    evento = get_object_or_404(Evento, id=evento_id)

    # Procesar fechas si existen
    nueva_fecha = None
    if request.POST.get("nueva_fecha"):
        try:
            nueva_fecha = datetime.strptime(
                request.POST.get("nueva_fecha"), "%Y-%m-%d"
            ).date()
        except ValueError:
            messages.error(request, "Fecha desde no válida.")
            return redirect("admin_eventos")

    nueva_fecha_hasta = None
    if request.POST.get("nueva_fecha_hasta"):
        try:
            nueva_fecha_hasta = datetime.strptime(
                request.POST.get("nueva_fecha_hasta"), "%Y-%m-%d"
            ).date()
        except ValueError:
            messages.error(request, "Fecha hasta no válida.")
            return redirect("admin_eventos")

    try:
        EventoService.gestionar_estado(
            evento=evento,
            user=request.user,
            nuevo_estado=request.POST.get("estado_evento"),
            observacion=request.POST.get("observacion", "").strip(),
            nueva_fecha=nueva_fecha,
            nueva_fecha_hasta=nueva_fecha_hasta,
        )
        messages.success(request, f"✅ Estado de '{evento.nombre}' actualizado.")
    except ValueError as ve:
        messages.error(request, f"❌ {str(ve)}")
    except Exception:
        logger.exception(
            "Error gestionando estado de evento. user_id=%s evento_id=%s",
            request.user.id,
            evento_id,
        )
        messages.error(
            request,
            "❌ Ocurrió un error interno al gestionar el estado del evento.",
        )

    return redirect("admin_eventos")


@login_required
@institucional_required
@require_http_methods(["POST"])
def cancelar_evento(request, evento_id):
    """
    Vista para cancelar un evento por parte de la institución.
    """
    evento = _get_evento_institucional(evento_id, request.user.userprofile.institution)
    motivo = request.POST.get("motivo", "").strip()

    try:
        EventoService.gestionar_estado(
            evento=evento,
            user=request.user,
            nuevo_estado=EstadoEvento.CANCELADO,
            observacion=motivo,
        )
        messages.warning(request, f"⚠️ Evento '{evento.nombre}' ha sido cancelado.")
    except ValueError as ve:
        messages.error(request, f"❌ {str(ve)}")
    except Exception:
        logger.exception(
            "Error cancelando evento. user_id=%s evento_id=%s",
            request.user.id,
            evento_id,
        )
        messages.error(
            request,
            "❌ Ocurrió un error interno al cancelar el evento.",
        )

    return redirect("admin_eventos")


@login_required
@institucional_required
@require_http_methods(["POST"])
def eliminar_evento(request, evento_id):
    """
    Vista única y optimizada para eliminar un evento.
    """
    try:
        perfil = request.user.userprofile
        evento = get_object_or_404(Evento, id=evento_id, institucion=perfil.institution)

        EventoService.eliminar_evento(evento, request.user)
        messages.success(request, "✅ Evento eliminado correctamente.")
    except ValueError as ve:
        messages.error(request, f"❌ {str(ve)}")
    except Exception:
        logger.exception(
            "Error eliminando evento. user_id=%s evento_id=%s",
            request.user.id,
            evento_id,
        )
        messages.error(
            request,
            "❌ Ocurrió un error interno al eliminar el evento.",
        )

    return redirect("mis_eventos")


@login_required
def detalle_evento(request, evento_id):
    """
    Vista para ver detalles de un evento.
    """
    perfil = request.user.userprofile
    user_type = perfil.user_type

    # Obtener el evento
    evento = get_object_or_404(
        Evento.objects.select_related(
            "estado", "municipio", "parroquia", "institucion"
        ),
        id=evento_id,
        activo=True,
    )

    # Validar permisos según el tipo de usuario
    if user_type not in ["fed_central", "tecnologico"]:
        # fed_regional: solo eventos de su estado
        if user_type == "fed_regional":
            if evento.estado != perfil.estado:
                messages.error(request, "No tienes permiso para ver este evento.")
                return redirect("dashboard")
        # institucional: solo eventos públicos o de su institución
        elif user_type == "institucional":
            evento_visible = (
                EventoSelector.get_eventos_visibles(perfil)
                .filter(id=evento.id)
                .exists()
            )
            if not evento_visible:
                messages.error(request, "No tienes permiso para ver este evento.")
                return redirect("eventos_disponibles")

    context = {
        "evento": evento,
        "puede_inscribirse": evento.puede_inscribirse
        if hasattr(evento, "puede_inscribirse")
        else False,
        "es_fed_central": EventoSelector.es_rector_eventos(perfil),
    }
    return render(request, "users/detalle_evento.html", context)


# ============================================
# VISTAS AJAX
# ============================================


# ============================================
# VISTAS AJAX PARA CARGAR UBICACIONES (UNIFICADO)
# ============================================


@login_required
def ajax_municipios(request):
    """
    Vista AJAX unificada para cargar municipios de un estado.
    Soporta parámetros 'estado_id' o 'id_estado'.
    """
    estado_id = request.GET.get("estado_id") or request.GET.get("id_estado")
    if estado_id:
        try:
            municipios = (
                Municipio.objects.filter(estado_id=estado_id)
                .order_by("nombre")
                .values("id", "nombre")
            )
            # Normalizar nombres de llaves para compatibilidad con JS antiguo
            data = [{"id": m["id"], "nombre": m["nombre"]} for m in municipios]
            return JsonResponse(data, safe=False)
        except (ValueError, TypeError):
            pass
    return JsonResponse([], safe=False)


@login_required
def ajax_parroquias(request):
    """
    Vista AJAX unificada para cargar parroquias de un municipio.
    Soporta parámetros 'municipio_id' o 'id_municipio'.
    """
    municipio_id = request.GET.get("municipio_id") or request.GET.get("id_municipio")
    if municipio_id:
        try:
            parroquias = (
                Parroquia.objects.filter(municipio_id=municipio_id)
                .order_by("nombre")
                .values("id", "nombre")
            )
            data = [{"id": p["id"], "nombre": p["nombre"]} for p in parroquias]
            return JsonResponse(data, safe=False)
        except (ValueError, TypeError):
            pass
    return JsonResponse([], safe=False)


@login_required
def inscripcion_evento_url(request, evento_id):
    # Aquí se renderiza el mismo formulario pero con su propia URL

    evento = get_object_or_404(Evento, id=evento_id)

    # Evitar doble inscripción
    if Inscripcion.objects.filter(evento=evento, lider=request.user).exists():
        messages.warning(request, "Ya estás inscrita en este evento.")
        return redirect("eventos_disponibles")

    if request.method == "POST":
        modalidad = request.POST.get("modalidad")
        nombre = request.POST.get("nombre_proyecto")
        descripcion = request.POST.get("descripcion")

        inscripcion = Inscripcion.objects.create(
            evento=evento,
            lider=request.user,
            modalidad=modalidad,
            nombre_proyecto=nombre,
            descripcion_proyecto=descripcion,
        )

        if modalidad == "equipo":
            integrantes_ids = request.POST.getlist("integrantes[]")
            for uid in integrantes_ids:
                if int(uid) != request.user.id:
                    IntegranteEquipo.objects.create(
                        inscripcion=inscripcion, usuario_id=uid
                    )

        messages.success(request, "Inscripción realizada correctamente")
        return redirect("eventos_disponibles")

    return render(request, "registry/inscribirse_evento.html", {"evento": evento})


@login_required
def buscar_usuarios(request):
    q = request.GET.get("q", "").strip()[:50]  # Limitar longitud

    if len(q) < 2:  # Requerir mínimo 2 caracteres
        return JsonResponse([], safe=False)

    usuarios = User.objects.filter(username__icontains=q)[:10]

    data = [
        {"id": u.id, "username": u.username, "nombre": f"{u.first_name} {u.last_name}"}
        for u in usuarios
    ]

    return JsonResponse(data, safe=False)


@login_required
def agregar_grupo(request):
    """Vista para agregar un grupo con validaciones completas"""
    # Obtener participantes de la institución del usuario
    try:
        perfil = request.user.userprofile
        institucion = perfil.institution

        # Obtener participantes vinculados activamente a la institución
        participantes = (
            Participante.objects.filter(
                vinculaciones__institucion=institucion, vinculaciones__status="activo"
            )
            .distinct()
            .order_by("nombres", "apellidos")
        )
    except (AttributeError, UserProfile.DoesNotExist):
        participantes = []

    if request.method == "POST":
        nombre_grupo = request.POST.get("nombre_grupo", "").strip()
        miembros_ids = request.POST.getlist("miembros")

        # Validaciones backend
        errores = []

        # 1. Validar nombre del grupo
        if not nombre_grupo:
            errores.append("❌ El nombre del grupo es obligatorio")
        elif len(nombre_grupo) < 3:
            errores.append("❌ El nombre del grupo debe tener al menos 3 caracteres")
        elif len(nombre_grupo) > 150:
            errores.append("❌ El nombre del grupo no puede exceder 150 caracteres")

        # 2. Validar selección de miembros
        if not miembros_ids or len(miembros_ids) == 0:
            errores.append("❌ Debes seleccionar al menos un miembro para el equipo")

        # Si hay errores, mostrar y retornar al formulario
        if errores:
            for error in errores:
                messages.error(request, error)
            return render(
                request,
                "users/agregar_grupo.html",
                {
                    "participantes": participantes,
                    "nombre_grupo_prev": nombre_grupo,
                    "miembros_prev": miembros_ids,
                },
            )

        # Si las validaciones pasan, crear el grupo
        try:
            with transaction.atomic():
                # Crear grupo
                nuevo_grupo = Grupo.objects.create(
                    nombre=nombre_grupo,
                    usuario_creador=request.user,
                    institucion=institucion,
                    criterio="proyecto",  # Valor por defecto
                    activo=True,
                )

                # Agregar miembros
                for miembro_id in miembros_ids:
                    try:
                        participante = Participante.objects.get(
                            id=miembro_id,
                            vinculaciones__institucion=institucion,
                            vinculaciones__status="activo",
                        )
                        nuevo_grupo.participantes.add(participante)
                    except Participante.DoesNotExist:
                        pass

                messages.success(
                    request,
                    f"✅ ¡Equipo '{nombre_grupo}' creado exitosamente con {len(miembros_ids)} miembro(s)!",
                )
                return redirect("mis_grupos")

        except Exception:
            logger.exception(
                "Error creando grupo legacy. user_id=%s",
                request.user.id,
            )
            messages.error(
                request,
                "❌ Ocurrió un error interno al crear el equipo.",
            )
            return render(
                request,
                "users/agregar_grupo.html",
                {
                    "participantes": participantes,
                    "nombre_grupo_prev": nombre_grupo,
                    "miembros_prev": miembros_ids,
                },
            )

    return render(request, "users/agregar_grupo.html", {"participantes": participantes})


@login_required
def ver_grupo(request, nombre_grupo):
    """Vista para mostrar un grupo con miembros, representante y eventos (prototipo)"""
    # Tomamos los grupos guardados en sesión
    grupos = request.session.get("grupos", [])
    grupo = next((g for g in grupos if g["nombre"] == nombre_grupo), None)

    if not grupo:
        grupo = {"nombre": nombre_grupo, "miembros": ["Juan Pérez", "María Gómez"]}

    # Datos de ejemplo
    representante = "Juan Pérez"
    eventos = [
        "Competencia Regional de Robótica 2024",
        "Taller de Programación Avanzada",
    ]

    context = {"grupo": grupo, "representante": representante, "eventos": eventos}

    return render(request, "users/ver_grupo.html", context)


# 1. ACTIVAR / VALIDAR
@login_required
@require_http_methods(["POST"])
def aprobar_institucion(request, institucion_id):
    perfil_admin = request.user.userprofile
    institucion = get_object_or_404(Institucion, id=institucion_id)

    # Validación de Jurisdicción Regional
    if (
        perfil_admin.user_type == "fed_regional"
        and institucion.estado != perfil_admin.estado
    ):
        return JsonResponse(
            {
                "status": "error",
                "message": f"No tienes permiso sobre sedes fuera de {perfil_admin.estado.nombre}.",
            },
            status=403,
        )

    try:
        if institucion.estatus == "pendiente":
            if InstitutionService.aprobar_primera_vez(institucion, request.user):
                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"Institución {institucion.nombre} aprobada con éxito. Código RNR: {institucion.codigo}",
                    }
                )

        elif institucion.estatus == "aprobado":
            InstitutionService.toggle_status(
                institucion, is_active=True, admin_user=request.user
            )
            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Acceso habilitado para {institucion.nombre}.",
                }
            )

        return JsonResponse(
            {
                "status": "error",
                "message": f"Estado no válido ({institucion.estatus}).",
            },
            status=400,
        )

    except PermissionDenied:
        return JsonResponse(
            {
                "status": "error",
                "message": "No tienes permisos para aprobar esta institución.",
            },
            status=403,
        )
    except Exception:
        logger.exception("Error en aprobar_institucion")
        return JsonResponse(
            {"status": "error", "message": "Ocurrió un error interno."}, status=500
        )


@login_required
@require_http_methods(["POST"])
def desactivar_institucion(request, institucion_id):
    perfil_admin = request.user.userprofile
    inst = get_object_or_404(Institucion, id=institucion_id)

    if perfil_admin.user_type == "fed_regional" and inst.estado != perfil_admin.estado:
        return JsonResponse(
            {"status": "error", "message": "No tienes permiso sobre esta región."},
            status=403,
        )

    try:
        InstitutionService.toggle_status(inst, is_active=False, admin_user=request.user)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "success"})
        messages.warning(request, f"Acceso suspendido para: {inst.nombre}")
    except Exception:
        logger.exception(
            "Error desactivando institucion. user_id=%s institucion_id=%s",
            request.user.id,
            institucion_id,
        )
        return JsonResponse(
            {"status": "error", "message": "Ocurrió un error interno."},
            status=500,
        )

    return redirect("lista_instituciones")


# 3. GESTIONAR CREDENCIALES (Cambio de contraseña)
@admin_required
@require_http_methods(["POST"])
def gestionar_credenciales(request, institucion_id):
    inst = get_object_or_404(Institucion, id=institucion_id)
    usuario = inst.usuario

    if not usuario:
        messages.error(
            request,
            "No se pudo actualizar las credenciales de esta institucion.",
        )
        return redirect("lista_instituciones")

    form = InstitucionCredentialAdminForm(request.POST, target_user=usuario)
    if not form.is_valid():
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
        return redirect("lista_instituciones")

    try:
        usuario.set_password(form.cleaned_data["password"])
        usuario.save(update_fields=["password"])
        logger.info(
            "Cambio administrativo de credenciales de institucion",
            extra={
                "actor_user_id": request.user.id,
                "target_user_id": usuario.id,
                "institucion_id": inst.id,
            },
        )
        messages.success(request, "Credenciales actualizadas correctamente.")
    except Exception:
        logger.exception(
            "Error al actualizar credenciales administrativas",
            extra={"actor_user_id": request.user.id, "institucion_id": inst.id},
        )
        messages.error(
            request,
            "No se pudo actualizar las credenciales de esta institucion.",
        )

    return redirect("lista_instituciones")


@admin_or_owner_required
@require_http_methods(["POST"])
def editar_institucion_modal(request, institucion_id):
    Institucion = apps.get_model("registry", "Institucion")
    inst = get_object_or_404(Institucion, id=institucion_id)
    user_vinculado = inst.usuario
    form = InstitucionModalEditForm(
        request.POST,
        instance=inst,
        target_user=user_vinculado,
    )

    if not form.is_valid():
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
        return redirect("lista_instituciones")

    try:
        form.save()

        if user_vinculado:
            user_vinculado.email = inst.email
            nueva_clave = form.cleaned_data.get("new_password")
            if nueva_clave:
                user_vinculado.set_password(nueva_clave)
                messages.info(
                    request,
                    f"Credenciales de {user_vinculado.username} actualizadas correctamente.",
                )
            user_vinculado.save()

        messages.success(request, f"Sede {inst.nombre} actualizada correctamente.")
    except Exception:
        logger.exception(
            "Error al editar institucion desde modal",
            extra={"institucion_id": institucion_id, "actor_user_id": request.user.id},
        )
        messages.error(
            request,
            "No se pudo actualizar la institucion. Intenta nuevamente.",
        )
    return redirect("lista_instituciones")


# ELIMINAR
@admin_required
@require_http_methods(["POST"])
def eliminar_institucion(request, institucion_id):
    """
    Mueve la institución a la papelera (eliminado=True)
    y desactiva su estatus (activa=False).
    """
    # Buscamos la institución por el ID que viene de la URL
    institucion = get_object_or_404(Institucion, id=institucion_id)

    if request.method == "POST":
        # 1. Cambiamos los estados según lo solicitado
        institucion.eliminado = True
        institucion.activa = False  # <--- Aquí forzamos el estado inactivo

        # 2. Guardamos la fecha si el campo existe en tu modelo
        if hasattr(institucion, "fecha_eliminacion"):
            institucion.fecha_eliminacion = timezone.now()

        institucion.save()

        # 3. Seguridad: Desactivamos el acceso de sus usuarios asociados
        # para que no puedan iniciar sesión mientras la sede esté "borrada"
        User.objects.filter(userprofile__institution=institucion).update(
            is_active=False
        )

        messages.warning(
            request,
            f"La institución '{institucion.nombre}' ha sido desactivada y movida a la papelera.",
        )
        return redirect("lista_instituciones")

    return redirect("lista_instituciones")


def estadisticas_demografia(request):
    # Cálculos para las tarjetas KPI
    context = {
        "total_participantes": Participante.objects.count(),
        "total_instituciones": Institucion.objects.count(),
        "total_eventos": Evento.objects.count(),
        # Calculando porcentaje de mujeres
        "mujeres_count": Participante.objects.filter(genero="F").count(),
        # Datos para el gráfico de barras (Estados)
        "datos_estados": Institucion.objects.values("estado")
        .annotate(total=Count("id"))
        .order_by("-total"),
    }
    return render(request, "tu_app/estadisticas.html", context)


def mapa_interactivo(request):
    # 1. Creamos un diccionario de mapeo (Nombre en DB -> Código del Mapa)
    mapeo_codigos = {
        "Amazonas": "ve-am",
        "Anzoátegui": "ve-an",
        "Apure": "ve-ap",
        "Aragua": "ve-ar",
        "Barinas": "ve-ba",
        "Bolívar": "ve-bo",
        "Carabobo": "ve-ca",
        "Cojedes": "ve-co",
        "Delta Amacuro": "ve-da",
        "Distrito Capital": "ve-dc",
        "Falcón": "ve-fa",
        "Guárico": "ve-gu",
        "Lara": "ve-la",
        "Mérida": "ve-me",
        "Miranda": "ve-mi",
        "Monagas": "ve-mo",
        "Nueva Esparta": "ve-ne",
        "Portuguesa": "ve-po",
        "Sucre": "ve-su",
        "Táchira": "ve-ta",
        "Trujillo": "ve-tr",
        "Vargas": "ve-va",
        "Yaracuy": "ve-ya",
        "Zulia": "ve-zu",
    }

    # 2. Consultamos la base de datos agrupando por estado
    # Esto cuenta las instituciones por cada estado de una sola vez
    conteo_db = Institucion.objects.values("estado__nombre").annotate(total=Count("id"))

    # 3. Construimos el JSON que entiende el JavaScript
    mapa_data = {}
    for registro in conteo_db:
        nombre_estado = registro["estado__nombre"]
        if nombre_estado in mapeo_codigos:
            codigo_mapa = mapeo_codigos[nombre_estado]
            mapa_data[codigo_mapa] = registro["total"]

    return render(request, "users/mapa_interactivo.html", {"mapa_data": mapa_data})


def dashboard_mapa(request):
    # Ejemplo de cómo agrupar instituciones por estado
    from django.db.models import Count

    # Asumiendo que tu modelo Institucion tiene un campo 'estado'
    conteo = Institucion.objects.values("estado").annotate(total=Count("id"))

    # Crear el diccionario: {'Miranda': 10, 'Zulia': 5...}
    mapa_data = {item["estado"]: item["total"] for item in conteo}

    return render(request, "tu_template.html", {"mapa_data": mapa_data})


@institucional_required
def detalle_evento_institucion(request, evento_id):
    """Ver detalles de un evento para usuario institucional.
    Permite ver eventos propios Y eventos públicos/visibles del catálogo.
    Muestra solo los equipos inscritos de la propia institución.
    """
    user_profile = request.user.userprofile
    institucion = user_profile.institution

    # Evento propio: institucional de esta institución, o de club creado por esta institución
    es_propio = Evento.objects.filter(
        Q(institucion=institucion)
        | Q(
            club_organizador__isnull=False,
            creado_por__userprofile__institution=institucion,
        ),
        id=evento_id,
    ).exists()

    es_visible = (
        EventoSelector.get_eventos_visibles(user_profile).filter(id=evento_id).exists()
    )

    if not es_propio and not es_visible:
        messages.error(request, "El evento no existe o no tienes permiso para verlo.")
        return redirect("eventos_disponibles")

    evento = get_object_or_404(
        Evento.objects.select_related(
            "estado", "municipio", "parroquia", "institucion"
        ),
        id=evento_id,
    )

    # Solo mostrar inscripciones de la propia institución
    inscripciones = (
        evento.inscripciones_grupo.filter(
            grupo__usuario_creador__userprofile__institution=institucion
        )
        .select_related("grupo")
        .prefetch_related("grupo__tutores")
    )

    context = {
        "evento": evento,
        "inscripciones": inscripciones,
        "total_inscritos": inscripciones.count(),
        "es_fed_central": False,
    }
    return render(request, "users/detalle_evento_gestion.html", context)


@login_required
def ajax_dependencias(request):
    q = request.GET.get("q", "").strip()[:100]  # Limitar longitud
    queryset = Dependencia.objects.filter(activa=True).order_by("nombre")
    if q:
        queryset = queryset.filter(nombre__icontains=q)
    data = [{"id": d.id, "nombre": d.nombre} for d in queryset[:30]]
    return JsonResponse(data, safe=False)


@login_required
def mi_perfil(request):
    """Redirige al perfil adecuado segun el rol del usuario"""
    perfil = request.user.userprofile
    if perfil.user_type == "institucional":
        return redirect("mi_perfil_institucional")
    return redirect("mi_perfil_federacion")


@login_required
def mi_perfil_institucional(request):
    usuario = request.user
    open_password_modal = False
    password_form = PasswordChangeForm(user=usuario)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "password_change":
            password_form = PasswordChangeForm(user=usuario, data=request.POST)
            if password_form.is_valid():
                updated_user = password_form.save()
                update_session_auth_hash(request, updated_user)
                messages.success(request, "Contraseña actualizada correctamente.")
                return redirect("mi_perfil_institucional")

            open_password_modal = True
            messages.error(
                request,
                "No se pudo actualizar la contraseña. Revisa los campos e intenta nuevamente.",
            )
        elif form_type == "editar_perfil":
            try:
                institucion = Institucion.objects.filter(
                    userprofile__user=usuario
                ).first()
                if institucion:
                    InstitutionService.actualizar_institucion(
                        institucion=institucion, data=request.POST
                    )
                    messages.success(request, "Perfil actualizado correctamente.")
                else:
                    messages.error(request, "No se encontró la institución asociada.")
            except Exception:
                logger.exception(
                    "Error actualizando perfil institucional. user_id=%s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "No se pudo actualizar el perfil institucional. Intenta nuevamente.",
                )
            return redirect("mi_perfil_institucional")

    institucion = Institucion.objects.filter(userprofile__user=usuario).first()
    if not institucion:
        institucion = Institucion.objects.filter(email=usuario.email).first()

    context = {
        "usuario": usuario,
        "institucion": institucion,
        "fecha_unido": usuario.date_joined,
        "password_form": password_form,
        "open_password_modal": open_password_modal,
        "estados": Estado.objects.all().order_by("nombre"),
    }
    return render(request, "users/mi_perfil.html", context)


@login_required
def mis_grupos(request):
    usuario = request.user

    if request.method == "POST":
        accion = request.POST.get("accion")
        grupo_id = request.POST.get("grupo_id")

        try:
            if accion == "eliminar":
                GrupoService.eliminar_grupo(grupo_id, usuario)
                messages.success(request, "El Equipo ha sido eliminado correctamente.")
            elif accion == "editar":
                GrupoService.editar_grupo(
                    grupo_id=grupo_id,
                    usuario=usuario,
                    nuevo_nombre=request.POST.get("nombre_grupo"),
                    eliminar_indices=request.POST.getlist("eliminar_participante"),
                    nuevas_cedulas=request.POST.getlist("nuevo_participante_cedula[]"),
                )
                messages.success(
                    request, "El equipo ha sido actualizado correctamente."
                )
            else:
                GrupoService.crear_grupo(
                    usuario=usuario,
                    nombre_grupo=request.POST.get("nombre_grupo"),
                    tutor_id=request.POST.get("tutores[]"),
                    cedulas_participantes=request.POST.getlist(
                        "participante_cedulas[]"
                    ),
                )
                messages.success(request, "¡El equipo ha sido registrado!")

            return redirect("mis_grupos")

        except ValueError as ve:
            messages.error(request, str(ve))
            return redirect("mis_grupos")
        except Exception:
            logger.exception(
                "Error operando sobre mis_grupos. user_id=%s accion=%s grupo_id=%s",
                request.user.id,
                accion,
                grupo_id,
            )
            messages.error(
                request,
                "No se pudo completar la operación sobre el equipo. Intenta nuevamente.",
            )
            return redirect("mis_grupos")

    # LÓGICA GET
    grupos = (
        Grupo.objects.filter(usuario_creador=usuario, activo=True)
        .prefetch_related("tutores", "participantes")
        .order_by("-fecha_registro")
    )

    context = {
        "grupos": grupos,
        "total_participantes": sum(grupo.participantes.count() for grupo in grupos),
    }
    return render(request, "users/mis_grupos.html", context)


@login_required
@require_http_methods(["GET"])
def api_buscar_participante(request, cedula):
    """
    API para buscar personas por cédula.
    Busca primero en Participantes, luego en Tutores.
    Retorna los datos encontrados para autocompletar formularios.
    """
    perfil = request.user.userprofile
    user_type = getattr(perfil, "user_type", None)
    cedula_limpia = "".join(filter(str.isdigit, cedula or ""))

    if user_type not in ["institucional", "fed_central", "fed_regional", "tecnologico"]:
        return JsonResponse({"encontrado": False}, status=403)

    if len(cedula_limpia) < 5:
        return JsonResponse({"encontrado": False})

    participantes = ParticipanteSelector.get_participantes_para_perfil(perfil).filter(
        cedula=cedula_limpia
    )

    try:
        p = participantes.get()
        return JsonResponse(
            {
                "encontrado": True,
                "tipo": "participante",
                "id": p.id,
                "nombre": p.nombres,
                "apellido": p.apellidos,
                "edad": p.edad,
            }
        )
    except Participante.DoesNotExist:
        pass

    # 2. Buscar en el modelo Tutor (si no se encontró en Participante)
    try:
        from registry.models import Tutor

        tutor_query = Tutor.objects.filter(cedula=cedula_limpia)
        if user_type == "institucional" and perfil.institution:
            tutor_query = tutor_query.filter(
                vinculaciones__institucion=perfil.institution,
                vinculaciones__status="activo",
            )
        elif user_type == "fed_regional" and perfil.estado:
            tutor_query = tutor_query.filter(
                Q(vinculaciones__estado=perfil.estado)
                | Q(vinculaciones__institucion__estado=perfil.estado),
                vinculaciones__status="activo",
            )
        else:
            tutor_query = tutor_query.filter(vinculaciones__status="activo")

        t = tutor_query.distinct().get()
        return JsonResponse(
            {
                "encontrado": True,
                "tipo": "tutor",
                "id": str(t.id),
                "nombre": t.nombres,
                "apellido": t.apellidos,
                "edad": None,
            }
        )
    except (Tutor.DoesNotExist, ImportError):
        return JsonResponse({"encontrado": False})


def obtener_datos_persona(request):
    """API para buscar datos por cédula y autocompletar"""
    cedula = request.GET.get("cedula")
    # Lógica para buscar en Participantes o Tutores existentes
    # data = { 'nombres': 'Juan', 'apellidos': 'Perez', ... }
    return JsonResponse({"status": "success", "data": {}})


@login_required
def dashboard_central(request):
    hoy = timezone.now().date()

    # KPIs Básicos
    total_participantes = Participante.objects.count()
    total_instituciones = Institucion.objects.count()  # Usando el nombre corregido
    total_eventos = Evento.objects.filter(fecha__gte=hoy).count()

    # Cobertura: Ajustado al nombre del campo que vimos en errores anteriores
    cobertura_nacional = Institucion.objects.values("estado").distinct().count()

    # 1. Gráfica de Barras: Distribución de Instituciones por Estado
    stats_estados = (
        Institucion.objects.values("estado")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )

    labels_estados = [item["estado"] for item in stats_estados]
    data_estados = [item["total"] for item in stats_estados]

    # 2. Gráfica de Línea: Crecimiento por mes
    # Usamos 'fecha_registro' si existe, si no, puedes usar 'id' para probar
    crecimiento_inst = (
        Institucion.objects.filter(fecha_registro__year=hoy.year)
        .values("fecha_registro__month")
        .annotate(total=Count("id"))
        .order_by("fecha_registro__month")
    )

    data_crecimiento = [0] * 12
    for item in crecimiento_inst:
        # Django a veces devuelve el mes en una llave diferente según la DB
        mes_num = item.get("fecha_registro__month")
        if mes_num:
            data_crecimiento[mes_num - 1] = item["total"]

    # 3. Género
    porcentaje_mujeres = 0
    if total_participantes > 0:
        mujeres = Participante.objects.filter(genero="Femenino").count()
        porcentaje_mujeres = round((mujeres / total_participantes) * 100)

    context = {
        "total_participantes": total_participantes,
        "total_instituciones": total_instituciones,
        "total_eventos": total_eventos,
        "cobertura_nacional": cobertura_nacional,
        "labels_estados": labels_estados,
        "data_estados": data_estados,
        "data_crecimiento": data_crecimiento,
        "porcentaje_mujeres": porcentaje_mujeres,
        "pendientes_aprobacion": 0,
    }
    return render(request, "users/dashboard_central.html", context)


@login_required
def registrar_club(request):
    """
    Ruta legacy conservada por compatibilidad.
    Redirige al flujo oficial de creacion de clubes dentro del modulo registry.
    """
    perfil = getattr(request.user, "userprofile", None)
    if not perfil:
        messages.error(request, "No tienes un perfil configurado.")
        return redirect("dashboard")

    if perfil.user_type not in ["institucional", "fed_central", "fed_regional"]:
        messages.error(request, "No tienes permiso para crear clubes.")
        return redirect("dashboard")

    if request.method == "POST":
        messages.info(
            request,
            "La ruta anterior de registro fue reemplazada por el flujo oficial de clubes.",
        )

    return redirect("crear_club")


@login_required
def registrar_sede(request):
    # Obtenemos el perfil del usuario logueado
    perfil_usuario = request.user.userprofile

    # Verificamos permisos de forma estricta
    is_admin_central = perfil_usuario.user_type == "fed_central"

    if not is_admin_central:
        messages.error(
            request, "Acceso denegado: Se requiere nivel de Administración Central."
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = SedeRegionalForm(request.POST)
        if form.is_valid():
            try:
                # Usar IdentityService para crear el usuario regional
                user, profile = IdentityService.create_user_with_profile(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    user_type="fed_regional",
                    estado=form.cleaned_data["estado"],
                    phone=f"{form.cleaned_data['codigo_area']}{form.cleaned_data['numero_telefono']}",
                    cedula=form.cleaned_data["cedula"],
                )

                # Guardar nombres y apellidos en el objeto User de Django
                user.first_name = form.cleaned_data["nombres"].upper()
                user.last_name = form.cleaned_data["apellidos"].upper()
                user.save(update_fields=["first_name", "last_name"])

                # Activar usuario inmediatamente
                IdentityService.toggle_user_status(user, is_active=True)

                messages.success(
                    request,
                    f"✅ ¡Éxito! Nodo Regional {profile.estado.nombre} activado correctamente.",
                )
                return redirect("gestionar_sedes")
            except Exception:
                logger.exception(
                    "Error creando sede regional. user_id=%s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "❌ Ocurrió un error interno al crear la sede regional.",
                )
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SedeRegionalForm()

    # IMPORTANTE: Pasar las variables que base_dashboard.html necesita
    return render(
        request,
        "users/registrar_sede.html",
        {
            "form": form,
            "es_central": is_admin_central,
            "perfil": perfil_usuario,
            "user_type": perfil_usuario.user_type,
        },
    )


@login_required
def gestionar_usuarios_sedes(request):
    if request.user.userprofile.user_type != "fed_central":
        return redirect("dashboard")

    estados = Estado.objects.all()

    todas_sedes = UserProfile.objects.filter(user_type="fed_regional").select_related(
        "user", "estado"
    )

    total_sedes = todas_sedes.count()
    sedes_activas = todas_sedes.filter(user__is_active=True).count()

    disponibilidad_sistema = (
        round((sedes_activas / total_sedes * 100), 1) if total_sedes > 0 else 100.0
    )

    return render(
        request,
        "users/gestionar_sedes.html",
        {
            "sedes": todas_sedes,
            "estados": estados,
            "es_central": True,
            "disponibilidad_sistema": disponibilidad_sistema,
            "sedes_activas": sedes_activas,
            "total_sedes": total_sedes,
        },
    )


@login_required
@fed_central_required
@require_http_methods(["POST"])
def editar_sede_regional(request, user_id):
    """
    Procesa la edición de un comisionado/sede regional desde el modal.
    """
    user_to_edit = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user_to_edit)

    # Preparar datos base para re-renderizar en caso de error
    def render_with_errors(error_msg):
        sedes = UserProfile.objects.filter(user_type="fed_regional").select_related(
            "user", "estado"
        )
        estados = Estado.objects.all()
        return render(
            request,
            "users/gestionar_sedes.html",
            {
                "sedes": sedes,
                "estados": estados,
                "es_central": True,
                "modal_error": error_msg,
                "edit_user_id": user_id,
                "edit_data": request.POST,
            },
        )

    try:
        # 1. Validar Contraseñas ANTES de guardar cualquier cambio
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password:
            # A. Coincidencia
            if new_password != confirm_password:
                return render_with_errors(
                    "❌ Las contraseñas no coinciden. No se ha realizado ningún cambio."
                )

            # B. Longitud mínima
            if len(new_password) < 8:
                return render_with_errors(
                    "❌ La contraseña es demasiado corta. Debe tener al menos 8 caracteres."
                )

            # C. Complejidad (Mayúsculas, Minúsculas, Especiales)
            import re

            if not re.search(r"[A-Z]", new_password):
                return render_with_errors(
                    "❌ La contraseña debe contener al menos una letra mayúscula."
                )
            if not re.search(r"[a-z]", new_password):
                return render_with_errors(
                    "❌ La contraseña debe contener al menos una letra minúscula."
                )
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_]", new_password):
                return render_with_errors(
                    "❌ La contraseña debe contener al menos un caracter especial o un guión."
                )

        # 2. Si las contraseñas coinciden y cumplen requisitos (o están vacías), proceder
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        cod_area = request.POST.get("cod_area")
        phone_num = request.POST.get("phone_num")

        # Validar campos obligatorios
        if not first_name or not last_name or not email:
            return render_with_errors(
                "❌ Los campos Nombres, Apellidos y Correo son obligatorios."
            )

        # Actualizar datos de User
        user_to_edit.first_name = first_name.upper()
        user_to_edit.last_name = last_name.upper()
        user_to_edit.email = email.lower()

        # Aplicar contraseña si fue proporcionada
        msg_password = ""
        if new_password:
            user_to_edit.set_password(new_password)
            msg_password = " y contraseña"

        user_to_edit.save()

        # Actualizar datos de Profile
        if cod_area and phone_num:
            profile.phone = f"{cod_area}{phone_num}"
        profile.save()

        messages.success(
            request,
            f"✅ Datos{msg_password} de {user_to_edit.get_full_name() or user_to_edit.username} actualizados.",
        )
    except Exception:
        logger.exception(
            "Error editando sede regional. user_id=%s target_user_id=%s",
            request.user.id,
            user_id,
        )
        return render_with_errors(
            "❌ Ocurrió un error interno al actualizar la sede regional."
        )

    return redirect("gestionar_sedes")


@login_required
def mi_perfil_federacion(request):
    perfil = request.user.userprofile
    user = request.user
    open_password_modal = False
    password_form = PasswordChangeForm(user=user)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "password_change":
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                updated_user = password_form.save()
                update_session_auth_hash(request, updated_user)
                messages.success(request, "Contrasena actualizada correctamente.")
                return redirect("mi_perfil_federacion")

            open_password_modal = True
            messages.error(
                request,
                "No se pudo actualizar la contrasena. Revisa los campos e intenta nuevamente.",
            )
        else:
            # Procesar actualizacion de datos basicos
            user.first_name = request.POST.get("first_name")
            user.last_name = request.POST.get("last_name")
            user.email = request.POST.get("email")

            # Actualizar datos del perfil
            perfil.phone = request.POST.get("telefono")

            # Solo el superusuario o central puede cambiarse de estado
            if perfil.user_type == "fed_central":
                nuevo_estado_id = request.POST.get("estado")
                if nuevo_estado_id:
                    perfil.estado = Estado.objects.get(id=nuevo_estado_id)

            user.save()
            perfil.save()

            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("mi_perfil_federacion")

    context = {
        "perfil": perfil,
        "user": user,
        "estados": Estado.objects.all(),
        "password_form": password_form,
        "open_password_modal": open_password_modal,
        # Para el menú lateral
        "es_central": perfil.user_type == "fed_central",
        "es_regional": perfil.user_type == "fed_regional",
    }
    return render(request, "users/perfil_federacion.html", context)


# Vista para eliminar (AJAX o POST directo)
@login_required
@fed_central_required
@require_POST
def eliminar_sede(request, user_id):
    profile_to_delete = get_object_or_404(
        UserProfile.objects.select_related("user", "estado"),
        user_id=user_id,
        user_type="fed_regional",
    )
    user_to_delete = profile_to_delete.user

    if request.user.id == user_to_delete.id:
        messages.error(
            request, "No puedes eliminar tu propia sede desde esta pantalla."
        )
        return redirect("gestionar_sedes")

    nombre = user_to_delete.get_full_name() or user_to_delete.username
    estado_nombre = (
        profile_to_delete.estado.nombre if profile_to_delete.estado else "Sin estado"
    )

    LogEntry.objects.log_action(
        user_id=request.user.id,
        content_type_id=ContentType.objects.get_for_model(User).pk,
        object_id=str(user_to_delete.pk),
        object_repr=user_to_delete.get_username(),
        action_flag=DELETION,
        change_message=(
            f"Sede regional eliminada: {nombre} ({user_to_delete.username}) - {estado_nombre}"
        ),
    )
    logger.info(
        "Sede regional eliminada",
        extra={
            "actor_user_id": request.user.id,
            "target_user_id": user_to_delete.id,
            "target_username": user_to_delete.username,
            "target_estado": estado_nombre,
        },
    )

    user_to_delete.delete()
    messages.success(request, f"La sede de {nombre} ha sido eliminada permanentemente.")
    return redirect("gestionar_sedes")


@login_required
def participante_detail(request, pk):
    """Muestra una vista compacta del participante (legacy)."""
    participante = get_object_or_404(
        ParticipanteSelector.get_participantes_visibles_para_usuario(request.user),
        pk=pk,
    )
    return render(request, "users/participante_detail.html", {"p": participante})


@login_required
def participante_edit(request, pk):
    participante = get_object_or_404(
        ParticipanteSelector.get_participantes_visibles_para_usuario(request.user),
        pk=pk,
    )
    if request.method == "POST":
        form = ParticipanteModalEditForm(request.POST, instance=participante)
        if form.is_valid():
            form.save()  # Aquí Django guarda automáticamente nombres, apellidos, etc.
            messages.success(request, "Datos actualizados correctamente.")
        else:
            # Esto te dirá en consola o pantalla exactamente qué campo falló
            for field, errors in form.errors.items():
                messages.error(request, f"Error en {field}: {errors.as_text()}")

    return redirect("lista_participantes")


@login_required
@require_http_methods(["POST"])
def cambiar_estado_participante(request, pk):
    """
    Cambia el status de la vinculación ParticipanteInstitucion para la institución
    del usuario autenticado. Solo accesible por usuarios institucionales.
    """
    perfil = request.user.userprofile
    if perfil.user_type != "institucional" or not perfil.institution:
        return JsonResponse({"success": False, "error": "Sin permiso."}, status=403)

    vinculacion = get_object_or_404(
        ParticipanteInstitucion,
        participante_id=pk,
        institucion=perfil.institution,
    )

    nuevo_status = request.POST.get("status")
    if nuevo_status not in ["activo", "inactivo", "suspendido"]:
        return JsonResponse({"success": False, "error": "Estado no válido."}, status=400)

    try:
        vinculacion.status = nuevo_status
        if nuevo_status != "activo":
            from django.utils import timezone
            vinculacion.fecha_desvinculacion = timezone.now()
        else:
            vinculacion.fecha_desvinculacion = None
        vinculacion.save(update_fields=["status", "fecha_desvinculacion"])
        return JsonResponse({
            "success": True,
            "nuevo_status": nuevo_status,
            "message": f"Participante {'habilitado' if nuevo_status == 'activo' else 'suspendido'} correctamente.",
        })
    except Exception:
        logger.exception(
            "Error cambiando estado de participante. user_id=%s participante_id=%s",
            request.user.id, pk,
        )
        return JsonResponse({"success": False, "error": "Error interno."}, status=500)


@login_required
@require_POST
def participante_delete(request, pk):
    """Elimina el registro del padrón. Exclusivo para fed_central."""
    perfil = request.user.userprofile
    if perfil.user_type not in ["fed_central", "tecnologico"]:
        logger.warning(
            "Intento de eliminación de participante sin permiso. user_id=%s user_type=%s participante_id=%s",
            request.user.id, perfil.user_type, pk,
        )
        messages.error(request, "❌ No tienes permiso para eliminar participantes del padrón.")
        return redirect("lista_participantes")

    participante = get_object_or_404(Participante, pk=pk)
    nombre = f"{participante.nombres} {participante.apellidos}"
    participante.delete()
    messages.success(request, f"El registro de {nombre} ha sido eliminado.")
    return redirect("lista_participantes")


@login_required
def detalle_evento_gestion(request, evento_id):
    """
    Vista para ver detalles del evento y gestionar inscritos
    """
    try:
        # Obtener el perfil del usuario para verificar permisos
        user_profile = request.user.userprofile

        # fed_central puede ver todos los eventos
        if user_profile.user_type == "fed_central":
            evento = get_object_or_404(Evento, id=evento_id)
        else:
            # Usuarios institucionales: pueden ver eventos propios (institucionales o de club)
            institution = user_profile.institution
            evento = (
                Evento.objects.filter(
                    Q(institucion=institution)
                    | Q(club_organizador__institucion_creadora=institution)
                )
                .filter(id=evento_id)
                .first()
            )
            if not evento:
                raise Evento.DoesNotExist

        inscripciones = (
            evento.inscripciones_grupo.all()
            .select_related("grupo", "grupo__institucion")
            .prefetch_related("grupo__tutores")
        )

        context = {
            "evento": evento,
            "inscripciones": inscripciones,
            "total_inscritos": inscripciones.count(),
            "es_fed_central": EventoSelector.es_rector_eventos(user_profile),
        }
        return render(request, "users/detalle_evento_gestion.html", context)

    except Evento.DoesNotExist:
        messages.error(request, "El evento no existe o no tienes permiso para verlo.")
        return redirect(
            "admin_eventos"
            if EventoSelector.es_rector_eventos(user_profile)
            else "mis_eventos"
        )


# ============================================
# API ENDPOINTS
# ============================================


@login_required
def api_participantes_grupo(request, grupo_id):
    """
    API endpoint para obtener los participantes de un grupo en formato JSON
    """
    try:
        # Obtener el perfil del usuario para verificar permisos
        user_profile = request.user.userprofile

        # fed_central puede ver todos los grupos
        if user_profile.user_type == "fed_central":
            grupo = get_object_or_404(Grupo, id=grupo_id)
        else:
            # Para usuarios institucionales, verificar si tienen acceso al grupo
            # a través de un evento que pueden ver (según reglas de audiencia)
            grupo = Grupo.objects.filter(id=grupo_id).first()
            if not grupo:
                return JsonResponse(
                    {"success": False, "error": "El grupo no existe."}, status=404
                )

            institucion = user_profile.institution
            # RESTRICCIÓN DE SEGURIDAD: Solo permitir ver participantes si el grupo pertenece a la institución del usuario
            if grupo.usuario_creador.userprofile.institution != institucion:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No tienes permiso para ver los participantes de este grupo.",
                    },
                    status=403,
                )

        # Obtener participantes con sus datos
        participantes = grupo.participantes.all().order_by("apellidos", "nombres")

        # Construir respuesta JSON
        participantes_data = []
        for participante in participantes:
            participantes_data.append(
                {
                    "id": str(participante.id),
                    "nombre": participante.nombres,
                    "apellido": participante.apellidos,
                    "cedula": f"{participante.nacionalidad}-{participante.cedula}"
                    if participante.cedula
                    else (participante.cedula_escolar or "-"),
                    "edad": participante.edad,
                    "sexo": participante.get_sexo_display()
                    if participante.sexo
                    else "-",
                    "grado": participante.get_grado_escolar_display(),
                    "telefono": participante.telefono_completo,
                }
            )

        return JsonResponse(
            {
                "success": True,
                "participantes": participantes_data,
                "total": len(participantes_data),
                "grupo_nombre": grupo.nombre,
            }
        )

    except Grupo.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": "El grupo no existe o no tienes permiso para verlo.",
            },
            status=404,
        )
    except Exception:
        logger.exception(
            "Error obteniendo participantes de grupo. user_id=%s grupo_id=%s",
            request.user.id,
            grupo_id,
        )
        return JsonResponse(
            {
                "success": False,
                "error": "Ocurrió un error interno al consultar los participantes del grupo.",
            },
            status=500,
        )


@login_required
@admin_required
def detalle_institucion_api(request, institucion_id):
    """
    Vista API para obtener detalles completos de una institución (AJAX)
    """
    from django.http import JsonResponse

    perfil = request.user.userprofile
    user_type = perfil.user_type

    try:
        institucion = Institucion.objects.select_related(
            "estado", "municipio", "parroquia"
        ).get(id=institucion_id, eliminado=False)

        # Verificar territorio mediante Selector
        if user_type == "fed_regional" and institucion.estado != perfil.estado:
            return JsonResponse(
                {"error": "No tienes permiso sobre esta región"}, status=403
            )

        # Construir respuesta
        # Para particulares, usar cédula en lugar de RIF
        if institucion.tipo_institucion == "particular":
            rif_o_cedula = (
                f"{institucion.particular_nacionalidad}-{institucion.particular_cedula}"
                if institucion.particular_cedula
                else "N/A"
            )
            nombre_completo = (
                f"{institucion.particular_nombres} {institucion.particular_apellidos}"
                if institucion.particular_nombres
                else institucion.nombre
            )
        else:
            rif_o_cedula = institucion.rif or "N/A"
            nombre_completo = institucion.nombre

        # Obtener usuario vinculado
        usuario_username = institucion.usuario.username if institucion.usuario else None

        # Obtener dependencia_rel
        dependencia_rel_nombre = (
            institucion.dependencia_rel.nombre if institucion.dependencia_rel else None
        )

        # Obtener fecha de eliminación si aplica
        fecha_elim = (
            institucion.fecha_eliminacion.strftime("%d/%m/%Y %H:%M")
            if institucion.fecha_eliminacion
            else None
        )

        data = {
            "nombre": nombre_completo,
            "codigo": institucion.codigo or "N/A",
            "rif": rif_o_cedula,
            "email": institucion.email or "N/A",
            "telefono": institucion.telefono or "N/A",
            "telefono_codigo": institucion.telefono_codigo or "N/A",
            "telefono_numero": institucion.telefono_numero or "N/A",
            "direccion": institucion.direccion or "N/A",
            "estado": institucion.estado.nombre if institucion.estado else "N/A",
            "municipio": institucion.municipio.nombre
            if institucion.municipio
            else "N/A",
            "parroquia": institucion.parroquia.nombre
            if institucion.parroquia
            else "N/A",
            "tipo_institucion": institucion.get_tipo_institucion_display()
            if hasattr(institucion, "get_tipo_institucion_display")
            else (institucion.tipo_institucion or "N/A"),
            "tipo_institucion_key": institucion.tipo_institucion or "otra",
            "naturaleza": institucion.get_naturaleza_display()
            if hasattr(institucion, "get_naturaleza_display")
            else (getattr(institucion, "naturaleza", None) or "N/A"),
            "codigo_mppe": getattr(institucion, "codigo_mppe", None) or "N/A",
            "dependencia": institucion.dependencia or "N/A",
            "dependencia_rel": dependencia_rel_nombre or "N/A",
            # Nuevos campos agregados
            "tipo_federado": institucion.get_tipo_federado_display()
            if hasattr(institucion, "get_tipo_federado_display")
            else (institucion.tipo_federado or "N/A"),
            "tipo_federado_key": institucion.tipo_federado or "N/A",
            "federado": institucion.federado,
            "categoria": institucion.categoria or "N/A",
            "subcategoria": institucion.subcategoria or "N/A",
            "institucion_procedencia": institucion.institucion_procedencia or "N/A",
            "usuario_vinculado": usuario_username or "N/A",
            # Campos de particular
            "particular_nombres": institucion.particular_nombres or "N/A",
            "particular_apellidos": institucion.particular_apellidos or "N/A",
            "particular_nacionalidad": institucion.particular_nacionalidad or "N/A",
            "particular_cedula": institucion.particular_cedula or "N/A",
            "estatus": institucion.estatus or "pendiente",
            "activa": institucion.activa,
            "eliminado": institucion.eliminado,
            "fecha_registro": institucion.fecha_registro.isoformat()
            if institucion.fecha_registro
            else "",
            "fecha_eliminacion": fecha_elim,
        }

        return JsonResponse(data)

    except Institucion.DoesNotExist:
        return JsonResponse({"error": "Institución no encontrada"}, status=404)
    except Exception:
        logger.exception(
            "Error obteniendo detalle de institucion via API. user_id=%s institucion_id=%s",
            request.user.id,
            institucion_id,
        )
        return JsonResponse(
            {
                "error": "Ocurrió un error interno al obtener el detalle de la institución."
            },
            status=500,
        )


@login_required
def toggle_submenu(request):
    """
    Endpoint HTMX para expandir/colapsar un submenu del sidebar.
    Persiste el estado en la sesión y re-renderiza solo el sidebar.
    """
    from django.template.loader import render_to_string

    label = request.GET.get("label", "")
    if not label:
        return HttpResponse(status=400)

    # Generar slug del label (mismo método que en context_processor)
    slug = (
        label.lower()
        .replace(" ", "-")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

    # Toggle en sesión
    expanded = request.session.get("expanded_submenus", [])
    if slug in expanded:
        expanded.remove(slug)
    else:
        expanded.append(slug)
    request.session["expanded_submenus"] = expanded
    request.session.modified = True

    # Re-renderizar el sidebar con el nuevo estado
    from users.context_processors import sidebar_menu

    context = sidebar_menu(request)
    html = render_to_string("users/partials/_sidebar.html", context, request=request)
    return HttpResponse(html)


# ============================================
# ASISTENCIA A EVENTOS
# ============================================


@login_required
@require_http_methods(["GET", "POST"])
def registro_asistencia(request, evento_id):
    """
    GET: muestra la lista de participantes con su estado de asistencia.
    POST: guarda masivamente los estados de asistencia.
    Solo accesible por el organizador del evento o federación.
    """
    perfil = request.user.userprofile
    es_rector = EventoSelector.es_rector_eventos(perfil)

    evento = get_object_or_404(Evento, id=evento_id, activo=True)

    # Verificar permiso: organizador o federación
    if not es_rector:
        institucion = perfil.institution
        es_organizador = (
            evento.institucion == institucion
            or (
                evento.club_organizador
                and evento.club_organizador.institucion_creadora == institucion
            )
            or (
                evento.creado_por
                and evento.creado_por.userprofile.institution == institucion
            )
        )
        if not es_organizador:
            messages.error(
                request,
                "No tienes permiso para gestionar la asistencia de este evento.",
            )
            return redirect("mis_eventos")

    # Solo disponible en en_proceso o finalizado
    if evento.estado_evento not in [EstadoEvento.EN_PROCESO, EstadoEvento.FINALIZADO]:
        messages.warning(
            request,
            "La asistencia solo puede registrarse cuando el evento está En Proceso o Finalizado.",
        )
        return redirect("detalle_evento_gestion", evento_id=evento_id)

    if request.method == "POST":
        with transaction.atomic():
            for key, valor in request.POST.items():
                if key.startswith("asistencia_"):
                    participante_id = key.replace("asistencia_", "")
                    observacion = request.POST.get(f"obs_{participante_id}", "").strip()
                    AsistenciaEvento.objects.filter(
                        evento=evento, participante_id=participante_id
                    ).update(
                        asistencia=valor,
                        observacion=observacion,
                        fecha_asistencia=timezone.now() if valor == "asistio" else None,
                    )
        messages.success(request, "✅ Asistencia guardada correctamente.")
        return redirect("registro_asistencia", evento_id=evento_id)

    # GET: cargar asistencias agrupadas por equipo
    asistencias = (
        AsistenciaEvento.objects.filter(evento=evento)
        .select_related("participante", "grupo")
        .order_by("grupo__nombre", "participante__apellidos")
    )

    # Agrupar por equipo
    equipos = {}
    for a in asistencias:
        nombre_grupo = a.grupo.nombre if a.grupo else "Sin equipo"
        equipos.setdefault(nombre_grupo, []).append(a)

    context = {
        "evento": evento,
        "equipos": equipos,
        "total": asistencias.count(),
        "asistieron": asistencias.filter(asistencia="asistio").count(),
        "ausentes": asistencias.filter(asistencia="ausente").count(),
        "pendientes": asistencias.filter(asistencia="pendiente").count(),
        "CHOICES": AsistenciaEvento.ASISTENCIA_CHOICES,
        "puede_editar": evento.estado_evento == EstadoEvento.EN_PROCESO,
    }
    return render(request, "users/registro_asistencia.html", context)
