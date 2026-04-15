"""Vistas para gestión de tutores."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from users.decorators import fed_central_cannot_create

from .forms import TutorForm
from .models import Grupo, Institucion, Tutor, TutorInstitucion
from .services import TutorService

logger = logging.getLogger(__name__)


# === Funciones auxiliares de permisos ===


def _usuario_puede_gestionar_tutor(user, tutor, institucion=None) -> bool:
    """
    Verifica si un usuario puede gestionar un tutor.

    Reglas:
    - Ente Rector funcional (`fed_central`) puede gestionar cualquier tutor.
    - Usuarios institucionales solo pueden gestionar tutores vinculados a su institución.
    """
    if not hasattr(user, "userprofile"):
        return False

    user_type = user.userprofile.user_type

    # Ente Rector funcional puede gestionar todos
    if user_type == "fed_central":
        return True

    # Usuarios institucionales solo pueden gestionar tutores vinculados a su institución
    user_institution = user.userprofile.institution
    if not user_institution:
        return False

    # Si se especifica institución, verificar que sea la del usuario
    if institucion and institucion != user_institution:
        return False

    # Verificar vinculación activa
    return TutorInstitucion.objects.filter(
        tutor=tutor, institucion=user_institution
    ).exists()


def _usuario_puede_gestionar_grupo(user, grupo) -> bool:
    """
    Verifica si un usuario puede gestionar un grupo.

    Reglas:
    - Ente Rector funcional (`fed_central`) puede gestionar cualquier grupo.
    - Usuarios institucionales solo pueden gestionar grupos que crearon o de su institución.

    Args:
        user: Usuario a verificar.
        grupo: Grupo a gestionar.

    Returns:
        bool: True si tiene permiso, False en caso contrario.
    """
    if not hasattr(user, "userprofile"):
        return False

    user_type = user.userprofile.user_type

    # Ente Rector funcional puede gestionar todos
    if user_type == "fed_central":
        return True

    # El creador del grupo siempre puede gestionarlo
    if grupo.usuario_creador == user:
        return True

    # Usuarios institucionales pueden gestionar grupos de su institución
    # (si el creador pertenece a la misma institución)
    institution = user.userprofile.institution
    if not institution:
        return False

    creador = grupo.usuario_creador
    if (
        hasattr(creador, "userprofile")
        and creador.userprofile.institution == institution
    ):
        return True

    return False


def _usuario_puede_crear_tutor_para_institucion(user, institucion) -> bool:
    """
    Verifica si un usuario puede crear tutores para una institución específica.

    Reglas:
    - Ente Rector funcional (`fed_central`) puede crear tutores para cualquier institución.
    - Usuarios institucionales solo pueden crear tutores para su propia institución.

    Args:
        user: Usuario a verificar.
        institucion: Institución donde se crearía el tutor.

    Returns:
        bool: True si tiene permiso, False en caso contrario.
    """
    if not hasattr(user, "userprofile"):
        return False

    user_type = user.userprofile.user_type

    # Ente Rector funcional puede crear para cualquier institución
    if user_type == "fed_central":
        return True

    # Usuarios institucionales solo pueden crear para su propia institución
    institution = user.userprofile.institution
    if not institution:
        return False

    return institution == institucion


@login_required
def lista_tutores(request):
    """
    Lista tutores con filtrado por jerarquía y territorialidad.
    """
    user_profile = request.user.userprofile
    user_type = user_profile.user_type
    puede_ver_todos = user_type in ["fed_central", "tecnologico"]

    # UX: recordar qué pestaña estaba activa al hacer búsquedas (query param `tab`).
    # IDs de pestañas en el template: `institucionales` y `federacion`.
    tab_activo = request.GET.get("tab", "institucionales").strip()
    if not puede_ver_todos or tab_activo not in ["institucionales", "federacion"]:
        tab_activo = "institucionales"

    # Base de consulta: Vinculaciones
    tutores_base = TutorInstitucion.objects.select_related(
        "tutor", "institucion", "estado"
    )

    # 1. Filtrado por Rol (Territorialidad)
    if puede_ver_todos:
        # Ve todas las vinculaciones
        pass
    elif user_type == "fed_regional":
        # Ve vinculaciones de su estado (Institucionales del estado o Regionales del estado)
        tutores_base = tutores_base.filter(
            Q(institucion__estado=user_profile.estado) | Q(estado=user_profile.estado)
        )
    elif user_type == "institucional":
        # Solo vinculaciones de su institución
        tutores_base = tutores_base.filter(institucion=user_profile.institution)
    else:
        tutores_base = TutorInstitucion.objects.none()

    # 2. Aplicar Filtros de Búsqueda
    institucion_id = request.GET.get("institucion")
    status = request.GET.get("status")
    busqueda = request.GET.get("q", "").strip()

    if institucion_id and puede_ver_todos:
        tutores_base = tutores_base.filter(institucion_id=institucion_id)
    if status:
        tutores_base = tutores_base.filter(status=status)
    if busqueda:
        tutores_base = tutores_base.filter(
            Q(tutor__nombres__icontains=busqueda)
            | Q(tutor__apellidos__icontains=busqueda)
            | Q(tutor__cedula__icontains=busqueda)
        )

    tutores_base = tutores_base.order_by("-fecha_vinculacion")

    # 3. Separación por tipo (Pestañas para Fed Central/Regional)
    tutores_federacion = []
    tutores_institucionales = []

    if user_type in ["fed_central", "fed_regional"]:
        tutores_federacion = tutores_base.filter(
            tipo_vinculacion__in=["central", "regional"]
        )
        tutores_institucionales = tutores_base.filter(tipo_vinculacion="institucional")
    else:
        tutores_institucionales = tutores_base

    # Instituciones para el filtro
    if puede_ver_todos:
        instituciones = Institucion.objects.filter(estatus="aprobado").order_by(
            "nombre"
        )
    elif user_type == "fed_regional":
        instituciones = Institucion.objects.filter(
            estado=user_profile.estado, estatus="aprobado"
        )
    else:
        instituciones = []

    context = {
        "tutores": tutores_base,
        "tutores_federacion": tutores_federacion,
        "tutores_institucionales": tutores_institucionales,
        "instituciones": instituciones,
        "filtros": {"institucion": institucion_id, "status": status, "q": busqueda},
        "puede_ver_todos": puede_ver_todos,
        "user_type": user_type,
        "tab_activo": tab_activo,
    }
    return render(request, "registry/lista_tutores.html", context)


@login_required
def crear_tutor(request):
    """
    Crea un tutor y su vinculación jerárquica.
    """
    user_profile = request.user.userprofile
    user_type = user_profile.user_type

    if request.method == "POST":
        form = TutorForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Datos del Tutor
                    datos_tutor = form.cleaned_data
                    creado_por_fed = user_type in ["fed_central", "fed_regional"]

                    # 2. Registrar/Obtener Tutor (No duplicidad)
                    tutor, creado = (
                        TutorService.buscar_tutor_por_cedula(datos_tutor["cedula"]),
                        False,
                    )
                    if not tutor:
                        tutor = TutorService.crear_tutor(
                            datos_tutor, creado_por_federacion=creado_por_fed
                        )
                        creado = True

                    # 3. Validar y Crear Vinculación según Rol
                    tipo_vin = form.cleaned_data["tipo_vinculacion"]
                    institucion = form.cleaned_data.get("institucion")
                    estado = form.cleaned_data.get("estado")

                    # Seguridad: Forzar estado si es regional
                    if user_type == "fed_regional":
                        estado = user_profile.estado
                        if tipo_vin == "central":
                            tipo_vin = "regional"  # No puede crear central

                    # Seguridad: Forzar institución si es institucional
                    if user_type == "institucional":
                        tipo_vin = "institucional"
                        institucion = user_profile.institution

                    TutorService.vincular_tutor(
                        tutor=tutor,
                        tipo_vinculacion=tipo_vin,
                        institucion=institucion,
                        estado=estado,
                        rol=form.cleaned_data["rol"],
                        usuario=request.user,
                    )

                    msg = f"Tutor {tutor.get_nombre_completo()} registrado y vinculado."
                    messages.success(
                        request,
                        msg if creado else f"Tutor existente vinculado correctamente.",
                    )
                    return redirect("lista_tutores")

            except ValidationError as e:
                form.add_error(None, e.message)
            except Exception:
                logger.exception(
                    "Error creando tutor. user_id=%s",
                    request.user.id,
                )
                messages.error(
                    request,
                    "Ocurrió un error interno al registrar el tutor. Intenta nuevamente.",
                )
    else:
        # Valores iniciales por Rol
        initial = {}
        if user_type == "institucional":
            initial = {
                "tipo_vinculacion": "institucional",
                "institucion": user_profile.institution,
            }
        elif user_type == "fed_regional":
            initial = {"tipo_vinculacion": "regional", "estado": user_profile.estado}

        form = TutorForm(initial=initial)

        # Limitar opciones del formulario por seguridad/UX
        if user_type == "institucional":
            form.fields["tipo_vinculacion"].choices = [
                ("institucional", "Institucional")
            ]
            form.fields["institucion"].queryset = Institucion.objects.filter(
                id=user_profile.institution.id
            )
        elif user_type == "fed_regional":
            form.fields["tipo_vinculacion"].choices = [
                ("institucional", "Institucional"),
                ("regional", "Sede Regional"),
            ]
            form.fields["estado"].queryset = Estado.objects.filter(
                id=user_profile.estado.id
            )
            form.fields["institucion"].queryset = Institucion.objects.filter(
                estado=user_profile.estado, estatus="aprobado"
            )

    context = {"form": form, "titulo": "Registrar Tutor", "boton_texto": "Registrar"}
    return render(request, "registry/form_tutor.html", context)


@login_required
def editar_tutor(request, tutor_id):
    """
    Vista para editar un tutor y su vinculación específica.
    """
    tutor = get_object_or_404(Tutor, id=tutor_id)
    user_profile = request.user.userprofile
    user_type = user_profile.user_type

    # Intentar obtener la vinculación específica (por parámetro o por contexto de usuario)
    vinc_id = request.GET.get("vinc_id")
    vinculacion = None

    if vinc_id:
        vinculacion = get_object_or_404(TutorInstitucion, id=vinc_id, tutor=tutor)
    else:
        # Lógica de fallback: buscar vinculación según el rol
        if user_type == "institucional":
            vinculacion = TutorInstitucion.objects.filter(
                tutor=tutor, institucion=user_profile.institution
            ).first()
        elif user_type == "fed_regional":
            vinculacion = TutorInstitucion.objects.filter(
                tutor=tutor, estado=user_profile.estado
            ).first()

        # Si no se encontró por contexto, tomar la más reciente (para central)
        if not vinculacion:
            vinculacion = TutorInstitucion.objects.filter(tutor=tutor).first()

    # Verificar permisos
    if not vinculacion or not _usuario_puede_gestionar_tutor(
        request.user, tutor, vinculacion.institucion
    ):
        messages.error(
            request,
            "No tiene permiso para editar este perfil de tutor en este contexto.",
        )
        return redirect("lista_tutores")

    if request.method == "POST":
        form = TutorForm(request.POST, instance=tutor)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar cambios en el Tutor (Datos personales)
                    form.save()

                    # 2. Actualizar vinculación si es permitido (solo para central/regional en sus campos)
                    if user_type == "fed_central":
                        vinculacion.tipo_vinculacion = form.cleaned_data[
                            "tipo_vinculacion"
                        ]
                        vinculacion.institucion = form.cleaned_data.get("institucion")
                        vinculacion.estado = form.cleaned_data.get("estado")

                    vinculacion.rol = form.cleaned_data["rol"]
                    vinculacion.save()

                    messages.success(
                        request,
                        f"Tutor {tutor.get_nombre_completo()} actualizado correctamente.",
                    )
                    return redirect("lista_tutores")
            except Exception:
                logger.exception(
                    "Error editando tutor. user_id=%s tutor_id=%s",
                    request.user.id,
                    tutor_id,
                )
                messages.error(
                    request,
                    "Ocurrió un error interno al guardar los cambios del tutor.",
                )
    else:
        # Pre-poblar formulario con datos de la vinculación encontrada
        initial = {
            "tipo_vinculacion": vinculacion.tipo_vinculacion,
            "institucion": vinculacion.institucion,
            "estado": vinculacion.estado,
            "rol": vinculacion.rol,
        }
        form = TutorForm(instance=tutor, initial=initial)

        # --- RESTRICCIÓN DE UI POR ROL ---
        if user_type == "institucional":
            # Bloquear campos de federación para usuarios de institución
            form.fields["tipo_vinculacion"].choices = [
                ("institucional", "Institucional")
            ]
            form.fields["tipo_vinculacion"].widget.attrs["readonly"] = True
            form.fields["institucion"].queryset = Institucion.objects.filter(
                id=user_profile.institution.id
            )
            form.fields["estado"].widget.attrs["disabled"] = True
        elif user_type == "fed_regional":
            # Solo permitir Institucional o Regional de su estado
            form.fields["tipo_vinculacion"].choices = [
                ("institucional", "Institucional"),
                ("regional", "Sede Regional"),
            ]
            form.fields["estado"].queryset = Estado.objects.filter(
                id=user_profile.estado.id
            )

    context = {
        "form": form,
        "tutor": tutor,
        "titulo": "Editar Tutor",
        "boton_texto": "Guardar Cambios",
    }
    return render(request, "registry/form_tutor.html", context)


@login_required
def detalle_tutor(request, tutor_id):
    """
    Vista para ver los detalles de un tutor.
    """
    tutor = get_object_or_404(Tutor.objects.prefetch_related("grupos"), id=tutor_id)

    # Obtener vinculaciones del tutor con instituciones
    vinculaciones = (
        TutorInstitucion.objects.filter(tutor=tutor)
        .select_related("institucion")
        .order_by("-fecha_vinculacion")
    )

    # Grupos asignados
    grupos = tutor.grupos.all().select_related("evento")

    context = {
        "tutor": tutor,
        "vinculaciones": vinculaciones,
        "grupos": grupos,
    }

    return render(request, "registry/detalle_tutor.html", context)


@login_required
def asignar_tutor_grupo(request, grupo_id):
    """
    Vista para asignar tutores a un grupo específico.

    Permisos:
    - Ente Rector puede asignar a cualquier grupo.
    - Usuarios institucionales solo pueden asignar a grupos de su institución.
    """
    grupo = get_object_or_404(Grupo, id=grupo_id)

    # Verificar permisos sobre el grupo
    if not _usuario_puede_gestionar_grupo(request.user, grupo):
        messages.error(request, "No tienes permiso para gestionar este grupo.")
        return redirect("mis_grupos")

    if request.method == "POST":
        tutor_id = request.POST.get("tutor_id")
        if tutor_id:
            tutor = get_object_or_404(Tutor, id=tutor_id)

            # Verificar permisos sobre el tutor
            if not _usuario_puede_gestionar_tutor(request.user, tutor):
                messages.error(request, "No tienes permiso para asignar este tutor.")
                return redirect("asignar_tutor_grupo", grupo_id=grupo.id)

            try:
                TutorService.asignar_tutor_a_grupo(tutor, grupo, request.user)
                messages.success(
                    request,
                    f'Tutor "{tutor.get_nombre_completo()}" asignado al grupo "{grupo.nombre}".',
                )
            except ValidationError as e:
                messages.error(request, str(e))

        return redirect("detalle_grupo", grupo_id=grupo.id)

    # GET: Mostrar formulario de asignación
    # Obtener tutores disponibles (activos en la institución y no asignados ya al grupo)
    tutores_asignados = grupo.tutores.values_list("id", flat=True)

    # Filtrar tutores según permisos del usuario
    if hasattr(request.user, "userprofile") and request.user.userprofile.institution:
        user_type = request.user.userprofile.user_type
        if user_type != "fed_central":
            # Usuarios institucionales solo ven tutores activos en su institución
            vinculaciones_activas = (
                TutorInstitucion.objects.filter(
                    institucion=request.user.userprofile.institution, status="activo"
                )
                .exclude(tutor_id__in=tutores_asignados)
                .select_related("tutor")
            )

            tutores_disponibles = [v.tutor for v in vinculaciones_activas]
        else:
            # Fed_central ve todos los tutores
            tutores_disponibles = Tutor.objects.exclude(
                id__in=tutores_asignados
            ).order_by("nombres", "apellidos")
    else:
        tutores_disponibles = []

    context = {
        "grupo": grupo,
        "tutores_disponibles": tutores_disponibles,
        "tutores_asignados": grupo.tutores.all(),
    }

    return render(request, "registry/asignar_tutor_grupo.html", context)


@login_required
def remover_tutor_grupo(request, grupo_id, tutor_id):
    """
    Vista para remover un tutor de un grupo.

    Permisos:
    - Ente Rector puede remover de cualquier grupo.
    - Usuarios institucionales solo pueden remover de grupos de su institución.
    """
    grupo = get_object_or_404(Grupo, id=grupo_id)
    tutor = get_object_or_404(Tutor, id=tutor_id)

    # Verificar permisos sobre el grupo
    if not _usuario_puede_gestionar_grupo(request.user, grupo):
        messages.error(request, "No tienes permiso para gestionar este grupo.")
        return redirect("mis_grupos")

    if request.method == "POST":
        try:
            TutorService.remover_tutor_de_grupo(tutor, grupo, request.user)
            messages.success(
                request,
                f'Tutor "{tutor.get_nombre_completo()}" removido del grupo "{grupo.nombre}".',
            )
        except ValidationError as e:
            messages.error(request, str(e))

    return redirect("asignar_tutor_grupo", grupo_id=grupo.id)


@login_required
@require_http_methods(["GET"])
def verificar_tutor_cedula(request):
    """
    Endpoint AJAX para verificar si un tutor existe por cédula.

    Retorna datos del tutor si existe para autocompletar el formulario.
    """
    cedula = request.GET.get("cedula", "").strip()

    if not cedula or len(cedula) < 5:
        return JsonResponse({"existe": False})

    tutor = TutorService.buscar_tutor_por_cedula(cedula)

    if not tutor:
        return JsonResponse({"existe": False})

    # Verificar vinculación con institución del usuario
    user_institution = (
        getattr(request.user.userprofile, "institution", None)
        if hasattr(request.user, "userprofile")
        else None
    )
    vinculacion_existente = None

    if user_institution:
        try:
            vinculacion_existente = TutorInstitucion.objects.get(
                tutor=tutor, institucion=user_institution
            )
        except TutorInstitucion.DoesNotExist:
            pass

    return JsonResponse(
        {
            "existe": True,
            "tutor": {
                "id": str(tutor.id),
                "nacionalidad": tutor.nacionalidad,
                "nombres": tutor.nombres,
                "apellidos": tutor.apellidos,
                "sexo": tutor.sexo,
                "cedula": tutor.cedula,
                "telefono_codigo": tutor.telefono_codigo,
                "telefono": tutor.telefono,
                "email": tutor.email,
                "profesion": tutor.profesion,
                "experiencia": tutor.experiencia,
            },
            "vinculado": vinculacion_existente is not None,
            "vinculacion": {
                "status": vinculacion_existente.status,
                "rol": vinculacion_existente.rol,
                "fecha": vinculacion_existente.fecha_vinculacion.isoformat(),
            }
            if vinculacion_existente
            else None,
        }
    )


@login_required
@require_http_methods(["GET"])
def buscar_tutores_ajax(request):
    """
    Endpoint AJAX para buscar tutores por nombre o cédula.

    Usado en selectores dinámicos.
    """
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    # Buscar tutores activos en cualquier institución
    vinculaciones = TutorInstitucion.objects.filter(
        Q(tutor__nombres__icontains=query)
        | Q(tutor__apellidos__icontains=query)
        | Q(tutor__cedula__icontains=query),
        status="activo",
    ).select_related("tutor", "institucion")[:10]

    results = [
        {
            "id": str(v.tutor.id),
            "text": f"{v.tutor.get_nombre_completo()} - {v.tutor.cedula}",
            "cedula": v.tutor.cedula,
            "institucion": v.institucion.nombre,
        }
        for v in vinculaciones
    ]

    return JsonResponse({"results": results})


@login_required
def cambiar_estado_tutor(request, tutor_id):
    """
    Vista para cambiar el estado de un tutor (activo/inactivo).
    """
    tutor = get_object_or_404(Tutor, id=tutor_id)
    vinc_id = request.POST.get("vinc_id")
    vinculacion = None

    if vinc_id:
        vinculacion = get_object_or_404(TutorInstitucion, id=vinc_id, tutor=tutor)

    # Verificar permisos
    user_profile = request.user.userprofile
    user_type = user_profile.user_type
    user_institution = user_profile.institution

    if not _usuario_puede_gestionar_tutor(request.user, tutor, user_institution):
        # Si es regional, verificar que la vinculación pertenezca a su estado
        if (
            user_type == "fed_regional"
            and vinculacion
            and vinculacion.estado == user_profile.estado
        ):
            pass
        elif (
            user_type == "fed_regional"
            and vinculacion
            and vinculacion.institucion
            and vinculacion.institucion.estado == user_profile.estado
        ):
            pass
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": "Sin permiso."}, status=403
                )
            messages.error(request, "No tienes permiso.")
            return redirect("lista_tutores")

    if request.method == "POST":
        nuevo_status = request.POST.get("status")
        try:
            TutorService.cambiar_estado_tutor(
                tutor=tutor,
                institucion=user_institution,
                nuevo_status=nuevo_status,
                usuario=request.user,
                vinculacion=vinculacion,
                estado=user_profile.estado if user_type == "fed_regional" else None,
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "nuevo_status": nuevo_status,
                        "message": f"Estado actualizado a {nuevo_status}.",
                    }
                )

            messages.success(request, f"Estado actualizado.")
        except ValidationError as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": str(e)}, status=400)
            messages.error(request, str(e))

    return redirect("detalle_tutor", tutor_id=tutor.id)
