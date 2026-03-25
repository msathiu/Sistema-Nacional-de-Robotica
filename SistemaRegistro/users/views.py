import json
from datetime import date, datetime

import pandas as pd
from django.apps import apps
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import UpdateView
from registry.forms import ParticipanteForm
from registry.models import (
    Club,
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
    Parroquia,
    Participante,
    ParticipanteInstitucion,
)

from .decorators import (
    admin_or_owner_required,
    admin_required,
    institucional_required,
    not_superuser_required,
    fed_central_cannot_create,
    fed_central_required,
)
from .forms import (
    ClubRegistrationForm,
    InstitucionRegistrationForm,
    ParticipanteModalEditForm,
    ParticipanteRegistrationForm,
    SedeRegionalForm,
)
from .models import Municipios, UserProfile
from .selectors import EventoSelector, JurisdictionSelector, ParticipanteSelector, InstitucionSelector
from .services.identity_service import IdentityService
from .services.participante_service import ParticipanteService
from .services.evento_service import EventoService
from .services.report_service import ReportService
from .services.grupo_service import GrupoService
from .services.institution_service import InstitutionService


def _render_formulario_evento(
    request,
    *,
    perfil,
    evento=None,
    valores_previos=None,
    errores=None,
):
    institution = perfil.institution if getattr(perfil, "user_type", None) == "institucional" else None
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

    evento = EventoSelector.get_eventos_visibles(user_profile).filter(id=evento_id).first()
    if not evento:
        messages.error(request, "El evento no existe o no tienes permiso para verlo.")
        return redirect("eventos_disponibles")

    # Verificar si la institución del usuario ya tiene un grupo inscrito en este evento
    institucion = user_profile.institution
    grupo_ya_inscrito = InscripcionGrupoEvento.objects.filter(
        evento=evento,
        activo=True,
        grupo__usuario_creador__userprofile__institution=institucion,
    ).select_related("grupo").first()

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
    evento = EventoSelector.get_eventos_visibles(user_profile).filter(id=evento_id).first()
    if not evento:
        messages.error(request, "El evento no existe o no tienes permiso para inscribirte en él.")
        return redirect("eventos_disponibles")

    grupo_id = request.POST.get("grupo_id")
    rol = request.POST.get("rol_participacion", "participante") or "participante"

    if not grupo_id:
        messages.error(request, "❌ Debes seleccionar un grupo para inscribir.")
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    try:
        grupo = Grupo.objects.get(id=grupo_id, usuario_creador=request.user, activo=True)
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
        messages.error(request, "❌ Este evento no está disponible para inscripciones en este momento.")
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    if evento.fecha < date.today():
        messages.error(request, "❌ No puedes inscribirte en un evento que ya pasó.")
        return redirect("detalle_evento_inscripcion", evento_id=evento_id)

    if InscripcionGrupoEvento.objects.filter(evento=evento, grupo=grupo).exists():
        messages.warning(request, f"⚠️ El grupo '{grupo.nombre}' ya está inscrito en este evento.")
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
        messages.error(request, "❌ Error al procesar la inscripción. Intenta nuevamente.")

    return redirect("detalle_evento_inscripcion", evento_id=evento_id)


def home(request):
    """Página principal con opciones de login y registro"""
    return render(request, "users/home.html")


@login_required
@require_http_methods(["POST", "GET"])
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

                # Formatear cédula para mostrar con nacionalidad
                cedula_display = (
                    f"{participante_existente.nacionalidad or 'V'}-{participante_existente.cedula}"
                    if participante_existente.cedula
                    else "N/A"
                )
                cedula_escolar_display = (
                    f"E-{participante_existente.cedula_escolar}"
                    if participante_existente.cedula_escolar
                    else "N/A"
                )

                # Obtener instituciones donde está vinculado
                instituciones_vinculadas = (
                    participante_existente.get_instituciones_activas()
                )
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
                        "total_instituciones": len(instituciones_nombres),
                        "datos": {
                            "nombres": participante_existente.nombres,
                            "apellidos": participante_existente.apellidos,
                            "fecha_nacimiento": participante_existente.fecha_nacimiento.strftime(
                                "%Y-%m-%d"
                            ),
                            "cedula": cedula_display,
                            "cedula_escolar": cedula_escolar_display,
                            "edad": participante_existente.edad,
                        },
                    }
                )
            else:
                return JsonResponse({"existe": False})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

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
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Error al vincular participante: {str(e)}"},
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
            user_institution=institucion
        ),
        "municipios": ParticipanteSelector.get_municipios_para_formulario(estado_seleccionado),
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
                    tipo_vinculacion=form.cleaned_data.get('tipo_vinculacion', 'institucional'),
                    estado_vinculacion=form.cleaned_data.get('vinculacion_estado')
                )
                messages.success(request, f'✅ Participante "{participante.nombres} {participante.apellidos}" registrado.')
                return redirect("lista_participantes")
            except ValueError as ve:
                messages.error(request, f"❌ {str(ve)}")
            except Exception as e:
                messages.error(request, f"❌ Error crítico: {str(e)}")

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
            user_institution=perfil_inst
        )

        if participante_form.is_valid():
            try:
                # Usar el servicio pasándole los cleaned_data
                participante = ParticipanteService.crear_participante_con_usuario(
                    cleaned_data=participante_form.cleaned_data,
                    institucion=perfil_inst,
                    registrado_por=request.user,
                    user_type_registrador="institucional",
                    tipo_vinculacion=participante_form.cleaned_data.get('tipo_vinculacion', 'institucional'),
                    estado_vinculacion=participante_form.cleaned_data.get('vinculacion_estado')
                )

                messages.success(
                    request, f"¡Éxito! Participante {participante.nombres} registrado."
                )
                return redirect("lista_participantes")

            except ValueError as ve:
                messages.error(request, f"❌ {str(ve)}")
            except Exception as e:
                messages.error(request, f"❌ Error: {str(e)}")
    else:
        participante_form = ParticipanteRegistrationForm(
            initial={"estado": estado_inst.id} if estado_inst else None,
            user_role="institucional",
            user_institution=perfil_inst
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
                "Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
            ],
            **metrics
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

    context = {
        "institution": institution,
        **metrics
    }
    return render(request, "users/dashboard_institucional.html", context)


@login_required
def exportar_participantes_excel(request):
    """Exporta datos de participantes a Excel según permisos del usuario"""

    perfil = request.user.userprofile
    user_type = perfil.user_type

    # 1. Obtener participantes según permisos mediante Selector
    participantes = ParticipanteSelector.get_participantes_para_perfil(perfil)
    
    if not participantes and user_type not in ["fed_central", "superuser", "tecnologico", "fed_regional", "institucional"]:
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
    filename = f"Participantes_{ParticipanteSelector.get_nombre_sede(perfil) or 'Padron_Nacional'}.xlsx".replace(" ", "_")

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
    instituciones_con_usuarios = InstitucionSelector.get_instituciones_con_usuarios(instituciones_qs)

    context = {
        "instituciones_con_usuarios": instituciones_con_usuarios,
        "total_instituciones": stats["total"],
        "instituciones_activas": stats["activas"],
        "instituciones_pendientes": stats["pendientes"],
        "estados": Estado.objects.all(),
        "es_central": user_type in ["fed_central", "superuser"],
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
                if hasattr(form, '_institucion_reactivada'):
                    institucion = form._institucion_reactivada
                    messages.warning(
                        request,
                        f"✅ La institución '{institucion.nombre}' ha sido reactivada exitosamente.\n\n"
                        f"📋 Estado actual: Pendiente de aprobación\n"
                        f"⏰ Tiempo estimado: 24-48 horas\n\n"
                        f"Recibirás una notificación cuando la administración central la apruebe."
                    )
                    return redirect("login")  # Redirigir al login ya que el usuario está desactivado
                
                # Usar el servicio para creación atómica de institución y usuario (solo para nuevas)
                institucion = InstitutionService.crear_institucion_con_usuario(
                    data=form.cleaned_data,
                    es_central=es_central,
                    es_regional=es_regional,
                    perfil_admin=perfil_admin
                )

                if es_central:
                    messages.success(request, f"Sede '{institucion.nombre}' activada con éxito.")
                    return redirect("lista_instituciones")
                elif es_federacion:
                    messages.info(request, f"Registro de '{institucion.nombre}' enviado a Sede Central.")
                    return redirect("lista_instituciones")
                else:
                    return render(
                        request,
                        "users/registro_pendiente.html",
                        {
                            "nombre_inst": institucion.nombre,
                            "email": institucion.email,
                            "base_template": base_template,
                        },
                    )

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
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

    # 1. Obtener Queryset base desde Selector
    participantes = ParticipanteSelector.get_participantes_para_perfil(perfil)
    
    if not participantes and user_type not in ["fed_central", "superuser", "tecnologico", "fed_regional", "institucional"]:
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

    # 3. Lógica para Menores de Edad (Evitar el FieldError de 'edad')
    # Calculamos la fecha límite: hoy hace 18 años
    hoy = date.today()
    fecha_limite_menores = date(hoy.year - 18, hoy.month, hoy.day)

    # 4. Métricas KPI según rol (evitar duplicados para fed_central)
    # Nota: `participantes` ya viene filtrado por `ParticipanteSelector.get_participantes_para_perfil(perfil)`,
    # que garantiza los criterios territoriales y el tratamiento de duplicados para fed_central/fed_regional.
    stats = participantes.aggregate(
        total_participantes=Count("id", distinct=True),
        participantes_hombres=Count(
            "id", filter=Q(sexo="M"), distinct=True
        ),
        participantes_mujeres=Count(
            "id", filter=Q(sexo="F"), distinct=True
        ),
        menores_edad=Count(
            "id", filter=Q(fecha_nacimiento__gt=fecha_limite_menores), distinct=True
        ),
    )

    # 5. Agregar información de institución a cada participante (optimizado)
    # Evitamos N+1 consultando una sola vez las vinculaciones activas más recientes.
    from django.db.models import Prefetch

    vinculaciones_prefetch = Prefetch(
        "vinculaciones",
        queryset=(
            ParticipanteInstitucion.objects.filter(status="activo")
            .select_related("institucion", "estado")
            .order_by("-fecha_vinculacion")
        ),
        to_attr="vinculaciones_activas",
    )

    participantes = participantes.order_by("-fecha_registro").prefetch_related(vinculaciones_prefetch)

    for p in participantes:
        vinculaciones_activas = getattr(p, "vinculaciones_activas", [])
        vinculacion = vinculaciones_activas[0] if vinculaciones_activas else None

        if vinculacion:
            p.vinculacion_tipo = vinculacion.tipo_vinculacion
            if vinculacion.tipo_vinculacion == "institucional" and vinculacion.institucion:
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
                    {"nombre": "Federación Central", "tipo_institucion": "federacion"},
                )()
        else:
            # Si no tiene vinculación, mostrar "Federación"
            p.vinculacion_tipo = "central"
            p.institucion = type(
                "obj",
                (object,),
                {"nombre": "Federación", "tipo_institucion": "federacion"},
            )()

    context = {
        "participantes": participantes,
        "total_participantes": stats.get("total_participantes", 0) or 0,
        "participantes_hombres": stats.get("participantes_hombres", 0) or 0,
        "participantes_mujeres": stats.get("participantes_mujeres", 0) or 0,
        "menores_edad": stats.get("menores_edad", 0) or 0,
        "estados": Estado.objects.all().order_by("nombre"),
        "es_central": user_type in ["fed_central", "superuser"],
        "es_regional": user_type == "fed_regional",
        "perfil": perfil,
        "user_type": user_type,
    }
    return render(request, "users/lista_participantes.html", context)


@login_required
def editar_participante(request, pk):
    """
    Vista optimizada para editar participantes.
    """
    participante = get_object_or_404(Participante, pk=pk)
    perfil = request.user.userprofile
    user_type = perfil.user_type

    # Validación de permisos territoriales
    if user_type == "institucional":
        vinculacion = participante.vinculaciones.filter(
            institucion=perfil.institution, status="activo"
        ).exists()
        if not vinculacion:
            messages.error(request, "No tienes permisos para editar participantes de otra institución.")
            return redirect("lista_participantes")

    # Preparar contexto usando Selectors
    context = {
        "participante_form": ParticipanteRegistrationForm(
            request.POST or None, 
            instance=participante, 
            initial={"estado": participante.estado.id} if participante.estado else None
        ),
        "participante": participante,
        "perfil": perfil,
        "edad": participante.edad,
        "cedula_personal": "".join(filter(str.isdigit, str(participante.cedula))) if participante.cedula else "",
        "cedula_escolar": participante.cedula_escolar or "",
        "estado": participante.estado,
        "estado_id": participante.estado.id if participante.estado else None,
        "municipio": participante.municipio,
        "municipios": ParticipanteSelector.get_municipios_para_formulario(participante.estado),
        "parroquias": Parroquia.objects.filter(municipio=participante.municipio).order_by("nombre") if participante.municipio else [],
        "todos_estados": ParticipanteSelector.get_todos_estados_para_formulario(perfil),
        "es_admin_central": JurisdictionSelector.es_rector(perfil),
    }

    if request.method == "POST":
        form = context["participante_form"]
        if form.is_valid():
            try:
                ParticipanteService.actualizar_participante(
                    participante=participante,
                    cleaned_data=form.cleaned_data
                )
                messages.success(request, f'✅ Datos de "{participante.nombres}" actualizados.')
                return redirect("lista_participantes")
            except Exception as e:
                messages.error(request, f"❌ Error: {str(e)}")

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
                    data=data,
                    es_central=True
                )

                messages.success(request, "Institución creada y activada correctamente.")
                return redirect("lista_instituciones")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
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
    club_preseleccionado_id = request.GET.get('club_id')
    valores_iniciales = {}
    if club_preseleccionado_id:
        valores_iniciales = {
            'club_organizador': club_preseleccionado_id,
            'tipo_evento': 'club'
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
                user=request.user,
                perfil=perfil,
                data=request.POST
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
                tipo_msg = "de club" if evento.tipo_evento == "club" else "institucional"
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
        except Exception as e:
            messages.error(request, f"❌ Error al crear el evento: {str(e)}")
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
                valores_iniciales["tipo_evento"] = "club" # Si se preselecciona un club, el tipo de evento es "club"
        except ValueError:
            pass # Ignorar si club_id_get no es un entero válido

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
    estado_geografico_filtro = request.GET.get("estado_geo") or request.GET.get("estado_id")
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
    eventos = Evento.objects.select_related(
        "estado", "municipio", "parroquia", "institucion", "club_organizador"
    ).filter(
        Q(activo=True) | Q(cancelado=True)
    ).exclude(
        Q(institucion__isnull=False) & Q(estado_evento=EstadoEvento.BORRADOR)
    )
    
    eventos = JurisdictionSelector.filtrar_por_territorio(eventos, perfil)
    es_fed_central = JurisdictionSelector.es_rector(perfil)
    institution = getattr(perfil, "institution", None)

    # Filtros adicionales desde la UI
    estado_filtro = request.GET.get("estado")
    tipo_filtro = request.GET.get("tipo")
    estado_evento_filtro = request.GET.get("estado_evento")
    federacion_institucion_filtro = request.GET.get("federacion_institucion")
    estado_nacional_filtro = request.GET.get("estado_nacional")

    if estado_filtro:
        eventos = eventos.filter(estado_id=estado_filtro)
    if tipo_filtro:
        eventos = eventos.filter(tipo=tipo_filtro)
    if estado_evento_filtro:
        eventos = eventos.filter(estado_evento=estado_evento_filtro)
    
    # Filtro por Federación o Institución (separado de ubicación)
    if federacion_institucion_filtro:
        if federacion_institucion_filtro == 'federacion':
            # Eventos creados por Federación Central (sin institución)
            eventos = eventos.filter(institucion__isnull=True)
        elif federacion_institucion_filtro == 'todas_instituciones':
            # Eventos de TODAS las instituciones (sin filtrar por institución específica)
            eventos = eventos.filter(institucion__isnull=False)
        elif federacion_institucion_filtro.startswith('inst_'):
            # Eventos de una institución específica
            institucion_id = federacion_institucion_filtro.replace('inst_', '')
            eventos = eventos.filter(institucion_id=institucion_id)
    
    # Filtro por estado nacional (ubicación del evento) - independiente del filtro anterior
    if estado_nacional_filtro:
        eventos = eventos.filter(estado_id=estado_nacional_filtro)

    eventos = eventos.order_by("-fecha_creacion")

    # Estadísticas Globales
    stats = eventos.aggregate(
        total=Count("id"),
        borrador=Count("id", filter=Q(estado_evento=EstadoEvento.BORRADOR)),
        revision=Count("id", filter=Q(estado_evento=EstadoEvento.REVISION)),
        abiertos=Count("id", filter=Q(estado_evento=EstadoEvento.ABIERTO)),
        rechazados=Count("id", filter=Q(estado_evento=EstadoEvento.RECHAZADO)),
        activos=Count(
            "id",
            filter=Q(estado_evento=EstadoEvento.ABIERTO, fecha__gt=hoy, cancelado=False),
        ),
        en_proceso=Count("id", filter=Q(estado_evento=EstadoEvento.EN_PROCESO)),
        finalizados=Count("id", filter=Q(estado_evento=EstadoEvento.FINALIZADO)),
        pausados=Count("id", filter=Q(estado_evento=EstadoEvento.PAUSADO)),
        cancelados=Count("id", filter=Q(cancelado=True)),
    )

    # Métricas de dashboard administrativo
    total_inscripciones = eventos.aggregate(
        total_inscripciones=Count(
            "inscripciones_grupo",
            filter=Q(inscripciones_grupo__activo=True),
        )
    )["total_inscripciones"] or 0

    eventos_activos = eventos.filter(
        Q(fecha_hasta__gte=hoy) | Q(fecha_hasta__isnull=True, fecha__gte=hoy),
        cancelado=False,
    ).count()

    for evento in eventos:
        evento.puede_editar = True  # Admin siempre puede gestionar
        evento.puede_modificar_datos = True
        evento.puede_pausar_usuario = evento.puede_pausar(request.user)
        evento.puede_cancelar_usuario = evento.puede_cancelar(request.user)

    stats["pausados_cancelados"] = (stats.get("pausados") or 0) + (stats.get("cancelados") or 0)

    context = {
        "eventos": eventos,
        "stats": stats,
        "hoy": hoy,
        "total_inscripciones": total_inscripciones,
        "eventos_activos": eventos_activos,
        "estados": Estado.objects.all().order_by("nombre"),
        "instituciones": Institucion.objects.all().order_by("nombre"),
        "tipos": Evento.TIPO_CHOICES,
        "estados_evento": EstadoEvento.choices,
        "es_fed_central": es_fed_central,
        "es_institucional": False, # En esta vista administrativa
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
    
    evento = get_object_or_404(Evento, id=evento_id, estado_evento=EstadoEvento.REVISION)
    
    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()
        
        with transaction.atomic():
            evento.estado_evento = EstadoEvento.ABIERTO
            evento.aprobado_por = request.user
            evento.observaciones_aprobacion = observaciones
            evento.fecha_aprobacion = timezone.now()
            evento.save()
        
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
    
    evento = get_object_or_404(Evento, id=evento_id, estado_evento=EstadoEvento.REVISION)
    
    if request.method == "POST":
        observacion = request.POST.get("observacion", "").strip()
        if not observacion:
            messages.error(request, "Debes proporcionar una observación para el rechazo.")
            return redirect("admin_eventos")
        
        with transaction.atomic():
            if not evento.rechazar(observaciones=observacion):
                messages.error(request, "No se puede rechazar el evento en su estado actual.")
                return redirect("admin_eventos")

        messages.success(request, f"Evento '{evento.nombre}' rechazado.")
        return redirect("admin_eventos")
    
    return render(request, "users/rechazar_evento.html", {"evento": evento})

@login_required
@institucional_required
def seguimiento_eventos_institucion(request):
    """
    Vista de Mis Eventos para la institución autenticada.
    """
    perfil = request.user.userprofile
    institution = perfil.institution

    # Parámetros de filtro GET
    q = request.GET.get("q", "").strip()
    filtro_estado = request.GET.get("estado_evento", "")
    filtro_tipo = request.GET.get("tipo_evento", "")

    base_qs = Evento.objects.filter(institucion=institution).select_related("estado", "municipio")
    if q:
        base_qs = base_qs.filter(nombre__icontains=q)
    if filtro_tipo:
        base_qs = base_qs.filter(tipo_evento=filtro_tipo)

    ESTADOS_OTROS = [EstadoEvento.PAUSADO, EstadoEvento.CANCELADO, EstadoEvento.EN_PROCESO, EstadoEvento.FINALIZADO]

    if filtro_estado:
        # Mostrar solo el estado solicitado en su grupo correspondiente
        eventos_borrador   = base_qs.filter(estado_evento=EstadoEvento.BORRADOR)   if filtro_estado == EstadoEvento.BORRADOR   else Evento.objects.none()
        eventos_revision   = base_qs.filter(estado_evento=EstadoEvento.REVISION)   if filtro_estado == EstadoEvento.REVISION   else Evento.objects.none()
        eventos_abiertos   = base_qs.filter(estado_evento=EstadoEvento.ABIERTO)    if filtro_estado == EstadoEvento.ABIERTO    else Evento.objects.none()
        eventos_rechazados = base_qs.filter(estado_evento=EstadoEvento.RECHAZADO)  if filtro_estado == EstadoEvento.RECHAZADO  else Evento.objects.none()
        eventos_otros      = base_qs.filter(estado_evento=filtro_estado)            if filtro_estado in ESTADOS_OTROS           else Evento.objects.none()
    else:
        eventos_borrador   = base_qs.filter(estado_evento=EstadoEvento.BORRADOR).order_by("-fecha_creacion")
        eventos_revision   = base_qs.filter(estado_evento=EstadoEvento.REVISION).order_by("-fecha_creacion")
        eventos_abiertos   = base_qs.filter(estado_evento=EstadoEvento.ABIERTO).order_by("-fecha")
        eventos_rechazados = base_qs.filter(estado_evento=EstadoEvento.RECHAZADO).order_by("-fecha_creacion")
        eventos_otros      = base_qs.filter(estado_evento__in=ESTADOS_OTROS).order_by("-fecha")

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
        "total": Evento.objects.filter(institucion=institution).count(),
    }

    context = {
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
        evento = get_object_or_404(
            Evento,
            id=evento_id,
            institucion=institution,
        )

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
            {"success": False, "error": "Evento no encontrado o no está disponible para envío."},
            status=404,
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


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
        evento = get_object_or_404(
            Evento,
            id=evento_id,
            institucion=request.user.userprofile.institution,
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
                evento=evento,
                perfil=perfil,
                data=request.POST
            )
            messages.success(request, f"✅ Evento '{evento.nombre}' actualizado correctamente.")
            return redirect(redirect_destino)
        except ValueError as ve:
            messages.error(request, f"❌ {str(ve)}")
            return _render_formulario_evento(
                request,
                perfil=perfil,
                evento=evento,
                valores_previos=request.POST,
            )
        except Exception as e:
            messages.error(request, f"❌ Error al actualizar el evento: {str(e)}")

    return _render_formulario_evento(request, perfil=perfil, evento=evento)


@login_required
@institucional_required
def cambiar_estado_evento(request, evento_id):
    """
    Vista institucional para cancelar un evento propio segun la maquina de estados.
    """
    if request.method == "POST":
        evento = get_object_or_404(
            Evento, id=evento_id, institucion=request.user.userprofile.institution
        )

        nuevo_estado = request.POST.get("estado_evento")
        motivo = request.POST.get("motivo", "").strip()

        if nuevo_estado == EstadoEvento.CANCELADO and evento.puede_cancelar(request.user):
            if evento.cancelar(motivo):
                messages.warning(
                    request,
                    f"Evento '{evento.nombre}' cancelado correctamente.",
                )
            else:
                messages.error(
                    request,
                    "El evento no puede cancelarse desde su estado actual.",
                )
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
        messages.error(request, "No tienes permiso para gestionar el estado de este evento.")
        return redirect("admin_eventos")

    evento = get_object_or_404(Evento, id=evento_id)
    
    # Procesar fechas si existen
    nueva_fecha = None
    if request.POST.get("nueva_fecha"):
        try:
            nueva_fecha = datetime.strptime(request.POST.get("nueva_fecha"), "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Fecha desde no válida.")
            return redirect("admin_eventos")

    nueva_fecha_hasta = None
    if request.POST.get("nueva_fecha_hasta"):
        try:
            nueva_fecha_hasta = datetime.strptime(request.POST.get("nueva_fecha_hasta"), "%Y-%m-%d").date()
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
            nueva_fecha_hasta=nueva_fecha_hasta
        )
        messages.success(request, f"✅ Estado de '{evento.nombre}' actualizado.")
    except ValueError as ve:
        messages.error(request, f"❌ {str(ve)}")
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")

    return redirect("admin_eventos")


@login_required
@institucional_required
@require_http_methods(["POST"])
def cancelar_evento(request, evento_id):
    """
    Vista para cancelar un evento por parte de la institución.
    """
    evento = get_object_or_404(Evento, id=evento_id, institucion=request.user.userprofile.institution)
    motivo = request.POST.get("motivo", "").strip()

    try:
        EventoService.gestionar_estado(
            evento=evento,
            user=request.user,
            nuevo_estado=EstadoEvento.CANCELADO,
            observacion=motivo
        )
        messages.warning(request, f"⚠️ Evento '{evento.nombre}' ha sido cancelado.")
    except ValueError as ve:
        messages.error(request, f"❌ {str(ve)}")
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")

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
    except Exception as e:
        messages.error(request, f"❌ Error al eliminar: {str(e)}")

    return redirect("admin_eventos")


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
    if user_type not in ["fed_central", "superuser"]:
        # fed_regional: solo eventos de su estado
        if user_type == "fed_regional":
            if evento.estado != perfil.estado:
                messages.error(request, "No tienes permiso para ver este evento.")
                return redirect("dashboard")
        # institucional: solo eventos públicos o de su institución
        elif user_type == "institucional":
            evento_visible = EventoSelector.get_eventos_visibles(perfil).filter(
                id=evento.id
            ).exists()
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

        except Exception as e:
            messages.error(request, f"❌ Error al crear el equipo: {str(e)}")
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
    if perfil_admin.user_type == "fed_regional" and institucion.estado != perfil_admin.estado:
        return JsonResponse(
            {"status": "error", "message": f"No tienes permiso sobre sedes fuera de {perfil_admin.estado.nombre}."},
            status=403,
        )

    try:
        if institucion.estatus == 'pendiente':
            if InstitutionService.aprobar_primera_vez(institucion, request.user):
                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"Institución {institucion.nombre} aprobada con éxito. Código RNR: {institucion.codigo}",
                    }
                )
        
        elif institucion.estatus == 'aprobado':
            InstitutionService.toggle_status(institucion, is_active=True, admin_user=request.user)
            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Acceso habilitado para {institucion.nombre}.",
                }
            )

        return JsonResponse(
            {"status": "error", "message": f"Estado no válido ({institucion.estatus})."},
            status=400
        )

    except PermissionDenied as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=403)
    except Exception as e:
        logger.error(f"Error en aprobar_institucion: {str(e)}")
        return JsonResponse({"status": "error", "message": "Ocurrió un error interno."}, status=500)


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
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return redirect("lista_instituciones")


# 3. GESTIONAR CREDENCIALES (Cambio de contraseña)
@admin_required
def gestionar_credenciales(request, institucion_id):
    inst = get_object_or_404(Institucion, id=institucion_id)
    usuario = inst.usuarios.first()  # Suponiendo relación inversa
    if request.method == "POST":
        nueva_pass = request.POST.get("password")
        usuario.set_password(nueva_pass)
        usuario.save()
        messages.success(request, "Contraseña actualizada correctamente.")
        return redirect("lista_instituciones")
    return render(
        request,
        "users/gestionar_credenciales.html",
        {"institucion": inst, "usuario": usuario},
    )


@admin_or_owner_required
def editar_institucion_modal(request, institucion_id):
    Institucion = apps.get_model("registry", "Institucion")
    inst = get_object_or_404(Institucion, id=institucion_id)

    if request.method == "POST":
        try:
            # 1. Actualización de datos de la Institución
            # Usamos or inst.nombre por si el campo llega vacío en el formulario
            inst.nombre = (request.POST.get("nombre") or inst.nombre).upper()
            inst.email = (request.POST.get("email") or inst.email).lower()
            inst.direccion = request.POST.get("direccion") or inst.direccion

            # RIF (Letra + Número)
            rif_letra = request.POST.get("rif_letra")
            rif_num = request.POST.get("rif_numero")
            if rif_letra and rif_num:
                inst.rif = f"{rif_letra}-{rif_num}"

            # Teléfono (Código + Número)
            cod_area = request.POST.get("modal_cod_area")
            num_puro = request.POST.get("modal_num_puro")
            if cod_area and num_puro:
                inst.telefono = f"{cod_area}{num_puro}"

            inst.save()
            print(f"[VISTA] Institución {inst.id} guardada exitosamente.")

            # 2. Sincronización con el Usuario de Django
            user_vinculado = User.objects.filter(username=inst.codigo).first()
            if user_vinculado:
                user_vinculado.email = inst.email

                nueva_clave = request.POST.get("new_password")
                confirm_clave = request.POST.get("confirm_password")

                if nueva_clave:
                    if nueva_clave == confirm_clave:
                        user_vinculado.set_password(nueva_clave)
                        messages.info(
                            request,
                            f"Contraseña de {user_vinculado.username} actualizada.",
                        )
                    else:
                        messages.warning(
                            request, "Sede guardada, pero las claves no coinciden."
                        )

                user_vinculado.save()

            messages.success(request, f"Sede {inst.nombre} actualizada correctamente.")

        except Exception as e:
            print(f"[ERROR EN VISTA] {str(e)}")
            messages.error(request, f"Error al guardar: {str(e)}")

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

    # Evento propio (organizador) o visible en el catálogo institucional
    es_propio = Evento.objects.filter(
        Q(institucion=institucion) | Q(club_organizador__institucion_creadora=institucion),
        id=evento_id,
    ).exists()

    es_visible = EventoSelector.get_eventos_visibles(user_profile).filter(id=evento_id).exists()

    if not es_propio and not es_visible:
        messages.error(request, "El evento no existe o no tienes permiso para verlo.")
        return redirect("eventos_disponibles")

    evento = get_object_or_404(
        Evento.objects.select_related("estado", "municipio", "parroquia", "institucion"),
        id=evento_id,
        activo=True,
    )

    # Solo mostrar inscripciones de la propia institución
    inscripciones = evento.inscripciones_grupo.filter(
        grupo__usuario_creador__userprofile__institution=institucion
    ).select_related("grupo").prefetch_related("grupo__tutores")

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
    if perfil.user_type == 'institucional':
        return redirect('mi_perfil_institucional')
    return redirect('mi_perfil_federacion')


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
                institucion = Institucion.objects.filter(userprofile__user=usuario).first()
                if institucion:
                    InstitutionService.actualizar_institucion(
                        institucion=institucion,
                        data=request.POST
                    )
                    messages.success(request, "Perfil actualizado correctamente.")
                else:
                    messages.error(request, "No se encontró la institución asociada.")
            except Exception as e:
                messages.error(request, f"Error al actualizar: {str(e)}")
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
                    nuevas_cedulas=request.POST.getlist("nuevo_participante_cedula[]")
                )
                messages.success(request, f"El equipo ha sido actualizado correctamente.")
            else:
                GrupoService.crear_grupo(
                    usuario=usuario,
                    nombre_grupo=request.POST.get("nombre_grupo"),
                    tutor_id=request.POST.get("tutores[]"),
                    cedulas_participantes=request.POST.getlist("participante_cedulas[]")
                )
                messages.success(request, f"¡El equipo ha sido registrado!")
            
            return redirect("mis_grupos")

        except ValueError as ve:
            messages.error(request, str(ve))
            return redirect("mis_grupos")
        except Exception as e:
            messages.error(request, f"Error en la operación: {str(e)}")
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


def api_buscar_participante(request, cedula):
    """
    API para buscar personas por cédula.
    Busca primero en Participantes, luego en Tutores.
    Retorna los datos encontrados para autocompletar formularios.
    """
    # 1. Buscar en el modelo Participante
    try:
        p = Participante.objects.get(cedula=cedula)
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

        t = Tutor.objects.get(cedula=cedula, status="activo")
        return JsonResponse(
            {
                "encontrado": True,
                "tipo": "tutor",
                "id": str(t.id),
                "nombre": t.nombres,
                "apellido": t.apellidos,
                "edad": None,
                "telefono": t.telefono,
                "email": t.email,
                "institucion": t.institucion.nombre if t.institucion else None,
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


def registrar_club(request):
    if request.method == "POST":
        form = ClubRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_clubes")
    else:
        form = ClubRegistrationForm()

    return render(request, "registrar_club.html", {"form": form})


@login_required
def registrar_sede(request):
    # Obtenemos el perfil del usuario logueado
    perfil_usuario = request.user.userprofile

    # Verificamos permisos de forma estricta
    is_admin_central = (
        perfil_usuario.user_type == "fed_central" or request.user.is_superuser
    )

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
                    cedula=form.cleaned_data["cedula"]
                )
                
                # Guardar nombres y apellidos en el objeto User de Django
                user.first_name = form.cleaned_data["nombres"].upper()
                user.last_name = form.cleaned_data["apellidos"].upper()
                user.save(update_fields=['first_name', 'last_name'])
                
                # Activar usuario inmediatamente
                IdentityService.toggle_user_status(user, is_active=True)

                messages.success(
                    request,
                    f"✅ ¡Éxito! Nodo Regional {profile.estado.nombre} activado correctamente.",
                )
                return redirect("gestionar_sedes")
            except Exception as e:
                messages.error(request, f"❌ Error al crear la sede: {str(e)}")
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
    if (
        not request.user.is_superuser
        and request.user.userprofile.user_type != "fed_central"
    ):
        return redirect("dashboard")

    sedes = UserProfile.objects.filter(user_type="fed_regional").select_related(
        "user", "estado"
    )
    estados = Estado.objects.all()

    return render(
        request,
        "users/gestionar_sedes.html",
        {"sedes": sedes, "estados": estados, "es_central": True},
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
        sedes = UserProfile.objects.filter(user_type="fed_regional").select_related("user", "estado")
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
                "edit_data": request.POST
            },
        )

    try:
        # 1. Validar Contraseñas ANTES de guardar cualquier cambio
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password:
            # A. Coincidencia
            if new_password != confirm_password:
                return render_with_errors("❌ Las contraseñas no coinciden. No se ha realizado ningún cambio.")
            
            # B. Longitud mínima
            if len(new_password) < 8:
                return render_with_errors("❌ La contraseña es demasiado corta. Debe tener al menos 8 caracteres.")
            
            # C. Complejidad (Mayúsculas, Minúsculas, Especiales)
            import re
            if not re.search(r"[A-Z]", new_password):
                return render_with_errors("❌ La contraseña debe contener al menos una letra mayúscula.")
            if not re.search(r"[a-z]", new_password):
                return render_with_errors("❌ La contraseña debe contener al menos una letra minúscula.")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_]", new_password):
                return render_with_errors("❌ La contraseña debe contener al menos un caracter especial o un guión.")

        # 2. Si las contraseñas coinciden y cumplen requisitos (o están vacías), proceder
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        cod_area = request.POST.get("cod_area")
        phone_num = request.POST.get("phone_num")

        # Validar campos obligatorios
        if not first_name or not last_name or not email:
            return render_with_errors("❌ Los campos Nombres, Apellidos y Correo son obligatorios.")

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

        messages.success(request, f"✅ Datos{msg_password} de {user_to_edit.get_full_name() or user_to_edit.username} actualizados.")
    except Exception as e:
        return render_with_errors(f"❌ Error al actualizar: {str(e)}")

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
            if perfil.user_type in ["fed_central", "superuser"]:
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
        "es_central": perfil.user_type in ["fed_central", "superuser"],
        "es_regional": perfil.user_type == "fed_regional",
    }
    return render(request, "users/perfil_federacion.html", context)


# Vista para eliminar (AJAX o POST directo)
@login_required
def eliminar_sede(request, user_id):
    if request.user.is_superuser or request.user.userprofile.user_type == "fed_central":
        user_to_delete = get_object_or_404(User, id=user_id)
        nombre = user_to_delete.get_full_name()
        user_to_delete.delete()
        messages.success(
            request, f"La sede de {nombre} ha sido eliminada permanentemente."
        )
    return redirect("gestionar_sedes")


def participante_detail(request, pk):
    """Muestra una vista compacta del participante (legacy)."""
    participante = get_object_or_404(Participante, pk=pk)
    return render(request, "users/participante_detail.html", {"p": participante})


@login_required
def participante_edit(request, pk):
    participante = get_object_or_404(Participante, pk=pk)
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


def participante_delete(request, pk):
    """Elimina el registro mediante POST"""
    if request.method == "POST":
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
        if user_profile.user_type == 'fed_central':
            evento = get_object_or_404(Evento, id=evento_id)
        else:
            # Usuarios institucionales: pueden ver eventos propios (institucionales o de club)
            institution = user_profile.institution
            evento = Evento.objects.filter(
                Q(institucion=institution) |
                Q(club_organizador__institucion_creadora=institution)
            ).filter(id=evento_id).first()
            if not evento:
                raise Evento.DoesNotExist
        
        inscripciones = evento.inscripciones_grupo.all().select_related("grupo").prefetch_related("grupo__tutores")

        context = {
            "evento": evento,
            "inscripciones": inscripciones,
            "total_inscritos": inscripciones.count(),
            "es_fed_central": EventoSelector.es_rector_eventos(user_profile),
        }
        return render(request, "users/detalle_evento_gestion.html", context)

    except Evento.DoesNotExist:
        messages.error(request, "El evento no existe o no tienes permiso para verlo.")
        return redirect("admin_eventos" if EventoSelector.es_rector_eventos(user_profile) else "mis_eventos")


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
        if user_profile.user_type == 'fed_central':
            grupo = get_object_or_404(Grupo, id=grupo_id)
        else:
            # Para usuarios institucionales, verificar si tienen acceso al grupo
            # a través de un evento que pueden ver (según reglas de audiencia)
            grupo = Grupo.objects.filter(id=grupo_id).first()
            if not grupo:
                return JsonResponse({
                    'success': False,
                    'error': 'El grupo no existe.'
                }, status=404)
            
            institucion = user_profile.institution
            # RESTRICCIÓN DE SEGURIDAD: Solo permitir ver participantes si el grupo pertenece a la institución del usuario
            if grupo.usuario_creador.userprofile.institution != institucion:
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permiso para ver los participantes de este grupo.'
                }, status=403)
        
        # Obtener participantes con sus datos
        participantes = grupo.participantes.all().order_by('apellidos', 'nombres')
        
        # Construir respuesta JSON
        participantes_data = []
        for participante in participantes:
            participantes_data.append({
                'id': str(participante.id),
                'nombre': participante.nombres,
                'apellido': participante.apellidos,
                'cedula': f"{participante.nacionalidad}-{participante.cedula}" if participante.cedula else (participante.cedula_escolar or '-'),
                'edad': participante.edad,
                'sexo': participante.get_sexo_display() if participante.sexo else '-',
                'grado': participante.get_grado_escolar_display(),
                'telefono': participante.telefono_completo,
            })
        
        return JsonResponse({
            'success': True,
            'participantes': participantes_data,
            'total': len(participantes_data),
            'grupo_nombre': grupo.nombre
        })
        
    except Grupo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'El grupo no existe o no tienes permiso para verlo.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


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
            return JsonResponse({"error": "No tienes permiso sobre esta región"}, status=403)

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
        dependencia_rel_nombre = institucion.dependencia_rel.nombre if institucion.dependencia_rel else None
        
        # Obtener fecha de eliminación si aplica
        fecha_elim = institucion.fecha_eliminacion.strftime("%d/%m/%Y %H:%M") if institucion.fecha_eliminacion else None
        
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
    except Exception as e:
        import traceback

        return JsonResponse(
            {"error": str(e), "traceback": traceback.format_exc()}, status=500
        )
