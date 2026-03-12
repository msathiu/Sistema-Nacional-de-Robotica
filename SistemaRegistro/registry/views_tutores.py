"""Vistas para gestión de tutores."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
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
    - Ente Rector (fed_central) y superuser pueden gestionar cualquier tutor.
    - Usuarios institucionales solo pueden gestionar tutores vinculados a su institución.
    """
    if not hasattr(user, 'userprofile'):
        return False
    
    user_type = user.userprofile.user_type
    
    # Ente Rector y superuser pueden gestionar todos
    if user_type in ['fed_central', 'superuser'] or user.is_superuser:
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
        tutor=tutor,
        institucion=user_institution
    ).exists()


def _usuario_puede_gestionar_grupo(user, grupo) -> bool:
    """
    Verifica si un usuario puede gestionar un grupo.
    
    Reglas:
    - Ente Rector (fed_central) y superuser pueden gestionar cualquier grupo.
    - Usuarios institucionales solo pueden gestionar grupos que crearon o de su institución.
    
    Args:
        user: Usuario a verificar.
        grupo: Grupo a gestionar.
        
    Returns:
        bool: True si tiene permiso, False en caso contrario.
    """
    if not hasattr(user, 'userprofile'):
        return False
    
    user_type = user.userprofile.user_type
    
    # Ente Rector y superuser pueden gestionar todos
    if user_type in ['fed_central', 'superuser'] or user.is_superuser:
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
    if hasattr(creador, 'userprofile') and creador.userprofile.institution == institution:
        return True
    
    return False


def _usuario_puede_crear_tutor_para_institucion(user, institucion) -> bool:
    """
    Verifica si un usuario puede crear tutores para una institución específica.
    
    Reglas:
    - Ente Rector (fed_central) y superuser pueden crear tutores para cualquier institución.
    - Usuarios institucionales solo pueden crear tutores para su propia institución.
    
    Args:
        user: Usuario a verificar.
        institucion: Institución donde se crearía el tutor.
        
    Returns:
        bool: True si tiene permiso, False en caso contrario.
    """
    if not hasattr(user, 'userprofile'):
        return False
    
    user_type = user.userprofile.user_type
    
    # Ente Rector y superuser pueden crear para cualquier institución
    if user_type in ['fed_central', 'superuser'] or user.is_superuser:
        return True
    
    # Usuarios institucionales solo pueden crear para su propia institución
    institution = user.userprofile.institution
    if not institution:
        return False
    
    return institution == institucion


@login_required
def lista_tutores(request):
    """
    Vista para listar todos los tutores.
    
    Permite filtrar por institución, estado y búsqueda por nombre/cédula.
    
    Permisos:
    - Ente Rector puede ver todos los tutores.
    - Usuarios institucionales solo pueden ver tutores de su institución.
    """
    # Filtrar según permisos del usuario
    user_institution = None
    puede_ver_todos = False
    
    if hasattr(request.user, 'userprofile'):
        user_type = request.user.userprofile.user_type
        if user_type in ['fed_central', 'superuser'] or request.user.is_superuser:
            puede_ver_todos = True
            tutores = TutorInstitucion.objects.select_related('tutor', 'institucion').all()
        else:
            user_institution = request.user.userprofile.institution
            if user_institution:
                tutores = TutorInstitucion.objects.select_related('tutor', 'institucion').filter(
                    institucion=user_institution
                )
            else:
                tutores = TutorInstitucion.objects.none()
    else:
        tutores = TutorInstitucion.objects.none()
    
    # Filtros
    institucion_id = request.GET.get('institucion')
    status = request.GET.get('status')
    busqueda = request.GET.get('q', '').strip()
    
    if institucion_id and puede_ver_todos:
        tutores = tutores.filter(institucion_id=institucion_id)
    
    if status:
        tutores = tutores.filter(status=status)
    
    if busqueda:
        tutores = tutores.filter(
            Q(tutor__nombres__icontains=busqueda) |
            Q(tutor__apellidos__icontains=busqueda) |
            Q(tutor__cedula__icontains=busqueda)
        )
    
    # Ordenamiento
    tutores = tutores.order_by('-fecha_vinculacion')
    
    # Instituciones para el filtro (solo si puede ver todos)
    if puede_ver_todos:
        instituciones = Institucion.objects.filter(
            estatus='aprobado'
        ).order_by('nombre')
    else:
        instituciones = Institucion.objects.filter(
            id=user_institution.id if user_institution else None
        )
    
    context = {
        'tutores': tutores,
        'instituciones': instituciones,
        'filtros': {
            'institucion': institucion_id,
            'status': status,
            'q': busqueda,
        },
        'puede_ver_todos': puede_ver_todos,
    }
    
    return render(request, 'registry/lista_tutores.html', context)


@login_required
@fed_central_cannot_create('lista_tutores')
def crear_tutor(request):
    """
    Vista para crear un nuevo tutor.
    
    Usa TutorService para validar la cédula única.
    
    Permisos:
    - Ente Rector (superuser) puede crear tutores para cualquier institución.
    - Usuarios institucionales solo pueden crear tutores para su propia institución.
    - fed_central NO puede crear tutores (bloqueado por decorador).
    """
    # Determinar instituciones disponibles según permisos
    puede_crear_cualquiera = False
    user_institution = None
    
    if hasattr(request.user, 'userprofile'):
        user_type = request.user.userprofile.user_type
        
        if user_type in ['superuser'] or request.user.is_superuser:
            puede_crear_cualquiera = True
        else:
            user_institution = request.user.userprofile.institution
    
    if request.method == 'POST':
        form = TutorForm(request.POST)
        if form.is_valid():
            institucion_seleccionada = form.cleaned_data['institucion']
            
            # Validar permisos sobre la institución seleccionada
            if not _usuario_puede_crear_tutor_para_institucion(request.user, institucion_seleccionada):
                messages.error(
                    request, 
                    "No tienes permiso para crear tutores en esta institución."
                )
                return redirect('lista_tutores')
            
            try:
                # Usar el nuevo servicio
                tutor, vinculacion, tutor_creado = TutorService.registrar_tutor_con_institucion(
                    institucion=institucion_seleccionada,
                    datos_tutor={
                        'cedula': form.cleaned_data['cedula'],
                        'nacionalidad': form.cleaned_data.get('nacionalidad', 'V'),
                        'nombres': form.cleaned_data['nombres'],
                        'apellidos': form.cleaned_data['apellidos'],
                        'sexo': form.cleaned_data.get('sexo', 'M'),
                        'telefono_codigo': form.cleaned_data.get('telefono_codigo', ''),
                        'telefono': form.cleaned_data.get('telefono', ''),
                        'email': form.cleaned_data['email'],
                        'profesion': form.cleaned_data.get('profesion', ''),
                        'experiencia': form.cleaned_data.get('experiencia', ''),
                    },
                    rol='colaborador',
                    usuario=request.user
                )
                
                if tutor_creado:
                    messages.success(
                        request,
                        f'Tutor "{tutor.get_nombre_completo()}" registrado exitosamente.'
                    )
                else:
                    messages.success(
                        request,
                        f'Tutor "{tutor.get_nombre_completo()}" vinculado a {institucion_seleccionada.nombre}.'
                    )
                return redirect('lista_tutores')
                
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        # Pre-seleccionar institución del usuario si tiene perfil
        initial = {}
        if user_institution and not puede_crear_cualquiera:
            initial['institucion'] = user_institution
        
        form = TutorForm(initial=initial)
        
        # Si no puede crear para cualquier institución, limitar el queryset
        if not puede_crear_cualquiera and user_institution:
            form.fields['institucion'].queryset = Institucion.objects.filter(
                id=user_institution.id
            )
    
    context = {
        'form': form,
        'titulo': 'Registrar Tutor',
        'boton_texto': 'Registrar',
        'puede_seleccionar_institucion': puede_crear_cualquiera,
    }
    
    return render(request, 'registry/form_tutor.html', context)


@login_required
def editar_tutor(request, tutor_id):
    """
    Vista para editar un tutor existente.
    
    Permisos:
    - Ente Rector puede editar cualquier tutor.
    - Usuarios institucionales solo pueden editar tutores de su institución.
    """
    tutor = get_object_or_404(Tutor, id=tutor_id)
    
    # Verificar permisos
    if not _usuario_puede_gestionar_tutor(request.user, tutor):
        messages.error(request, "No tienes permiso para editar este tutor.")
        return redirect('lista_tutores')
    
    # Determinar institución del usuario
    user_institution = None
    puede_cambiar_institucion = False
    if hasattr(request.user, 'userprofile'):
        user_type = request.user.userprofile.user_type
        user_institution = request.user.userprofile.institution
        if user_type in ['fed_central', 'superuser'] or request.user.is_superuser:
            puede_cambiar_institucion = True
    
    if request.method == 'POST':
        form = TutorForm(request.POST, instance=tutor)
        if form.is_valid():
            try:
                # Validar cédula única si cambió
                cedula = form.cleaned_data['cedula'].strip()
                if Tutor.objects.filter(cedula=cedula).exclude(pk=tutor.pk).exists():
                    raise ValidationError(f'Ya existe un tutor con la cédula {cedula}.')
                
                # Guardar solo los datos del tutor (sin institución)
                tutor.nacionalidad = form.cleaned_data.get('nacionalidad', 'V')
                tutor.nombres = form.cleaned_data['nombres']
                tutor.apellidos = form.cleaned_data['apellidos']
                tutor.sexo = form.cleaned_data.get('sexo', 'M')
                tutor.cedula = cedula
                tutor.telefono_codigo = form.cleaned_data.get('telefono_codigo', '')
                tutor.telefono = form.cleaned_data.get('telefono', '')
                tutor.email = form.cleaned_data['email']
                tutor.profesion = form.cleaned_data.get('profesion', '')
                tutor.experiencia = form.cleaned_data.get('experiencia', '')
                tutor.save()
                
                messages.success(
                    request,
                    f'Tutor "{tutor.get_nombre_completo()}" actualizado exitosamente.'
                )
                return redirect('lista_tutores')
                
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        # Pre-cargar institución del usuario para el formulario
        initial = {}
        if user_institution and not puede_cambiar_institucion:
            initial['institucion'] = user_institution
        
        form = TutorForm(instance=tutor, initial=initial)
        
        # Limitar queryset de instituciones según permisos
        if not puede_cambiar_institucion and user_institution:
            form.fields['institucion'].queryset = Institucion.objects.filter(
                id=user_institution.id
            )
    
    context = {
        'form': form,
        'tutor': tutor,
        'titulo': 'Editar Tutor',
        'boton_texto': 'Guardar Cambios',
        'puede_seleccionar_institucion': puede_cambiar_institucion,
    }
    
    return render(request, 'registry/form_tutor.html', context)


@login_required
def detalle_tutor(request, tutor_id):
    """
    Vista para ver los detalles de un tutor.
    """
    tutor = get_object_or_404(
        Tutor.objects.prefetch_related('grupos'),
        id=tutor_id
    )
    
    # Obtener vinculaciones del tutor con instituciones
    vinculaciones = TutorInstitucion.objects.filter(
        tutor=tutor
    ).select_related('institucion').order_by('-fecha_vinculacion')
    
    # Grupos asignados
    grupos = tutor.grupos.all().select_related('evento')
    
    context = {
        'tutor': tutor,
        'vinculaciones': vinculaciones,
        'grupos': grupos,
    }
    
    return render(request, 'registry/detalle_tutor.html', context)


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
        return redirect('mis_grupos')
    
    if request.method == 'POST':
        tutor_id = request.POST.get('tutor_id')
        if tutor_id:
            tutor = get_object_or_404(Tutor, id=tutor_id)
            
            # Verificar permisos sobre el tutor
            if not _usuario_puede_gestionar_tutor(request.user, tutor):
                messages.error(request, "No tienes permiso para asignar este tutor.")
                return redirect('asignar_tutor_grupo', grupo_id=grupo.id)
            
            try:
                TutorService.asignar_tutor_a_grupo(tutor, grupo, request.user)
                messages.success(
                    request,
                    f'Tutor "{tutor.get_nombre_completo()}" asignado al grupo "{grupo.nombre}".'
                )
            except ValidationError as e:
                messages.error(request, str(e))
        
        return redirect('detalle_grupo', grupo_id=grupo.id)
    
    # GET: Mostrar formulario de asignación
    # Obtener tutores disponibles (activos en la institución y no asignados ya al grupo)
    tutores_asignados = grupo.tutores.values_list('id', flat=True)
    
    # Filtrar tutores según permisos del usuario
    if hasattr(request.user, 'userprofile') and request.user.userprofile.institution:
        user_type = request.user.userprofile.user_type
        if user_type not in ['fed_central', 'superuser'] and not request.user.is_superuser:
            # Usuarios institucionales solo ven tutores activos en su institución
            vinculaciones_activas = TutorInstitucion.objects.filter(
                institucion=request.user.userprofile.institution,
                status='activo'
            ).exclude(
                tutor_id__in=tutores_asignados
            ).select_related('tutor')
            
            tutores_disponibles = [v.tutor for v in vinculaciones_activas]
        else:
            # Fed_central ve todos los tutores
            tutores_disponibles = Tutor.objects.exclude(
                id__in=tutores_asignados
            ).order_by('nombres', 'apellidos')
    else:
        tutores_disponibles = []
    
    context = {
        'grupo': grupo,
        'tutores_disponibles': tutores_disponibles,
        'tutores_asignados': grupo.tutores.all(),
    }
    
    return render(request, 'registry/asignar_tutor_grupo.html', context)


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
        return redirect('mis_grupos')
    
    if request.method == 'POST':
        try:
            TutorService.remover_tutor_de_grupo(tutor, grupo, request.user)
            messages.success(
                request,
                f'Tutor "{tutor.get_nombre_completo()}" removido del grupo "{grupo.nombre}".'
            )
        except ValidationError as e:
            messages.error(request, str(e))
    
    return redirect('asignar_tutor_grupo', grupo_id=grupo.id)


@login_required
@require_http_methods(["GET"])
def verificar_tutor_cedula(request):
    """
    Endpoint AJAX para verificar si un tutor existe por cédula.
    
    Retorna datos del tutor si existe para autocompletar el formulario.
    """
    cedula = request.GET.get('cedula', '').strip()
    
    if not cedula or len(cedula) < 5:
        return JsonResponse({'existe': False})
    
    tutor = TutorService.buscar_tutor_por_cedula(cedula)
    
    if not tutor:
        return JsonResponse({'existe': False})
    
    # Verificar vinculación con institución del usuario
    user_institution = getattr(request.user.userprofile, 'institution', None) if hasattr(request.user, 'userprofile') else None
    vinculacion_existente = None
    
    if user_institution:
        try:
            vinculacion_existente = TutorInstitucion.objects.get(
                tutor=tutor,
                institucion=user_institution
            )
        except TutorInstitucion.DoesNotExist:
            pass
    
    return JsonResponse({
        'existe': True,
        'tutor': {
            'id': str(tutor.id),
            'nacionalidad': tutor.nacionalidad,
            'nombres': tutor.nombres,
            'apellidos': tutor.apellidos,
            'sexo': tutor.sexo,
            'cedula': tutor.cedula,
            'telefono_codigo': tutor.telefono_codigo,
            'telefono': tutor.telefono,
            'email': tutor.email,
            'profesion': tutor.profesion,
            'experiencia': tutor.experiencia,
        },
        'vinculado': vinculacion_existente is not None,
        'vinculacion': {
            'status': vinculacion_existente.status,
            'rol': vinculacion_existente.rol,
            'fecha': vinculacion_existente.fecha_vinculacion.isoformat(),
        } if vinculacion_existente else None
    })


@login_required
@require_http_methods(["GET"])
def buscar_tutores_ajax(request):
    """
    Endpoint AJAX para buscar tutores por nombre o cédula.
    
    Usado en selectores dinámicos.
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Buscar tutores activos en cualquier institución
    vinculaciones = TutorInstitucion.objects.filter(
        Q(tutor__nombres__icontains=query) |
        Q(tutor__apellidos__icontains=query) |
        Q(tutor__cedula__icontains=query),
        status='activo'
    ).select_related('tutor', 'institucion')[:10]
    
    results = [
        {
            'id': str(v.tutor.id),
            'text': f'{v.tutor.get_nombre_completo()} - {v.tutor.cedula}',
            'cedula': v.tutor.cedula,
            'institucion': v.institucion.nombre,
        }
        for v in vinculaciones
    ]
    
    return JsonResponse({'results': results})


@login_required
def cambiar_estado_tutor(request, tutor_id):
    """
    Vista para cambiar el estado de un tutor (activo/inactivo).
    
    Soporta tanto solicitudes tradicionales como AJAX.
    Para AJAX retorna JSON, para tradicional redirige.
    
    Permisos:
    - Ente Rector puede cambiar estado de cualquier tutor.
    - Usuarios institucionales solo pueden cambiar estado de tutores de su institución.
    """
    tutor = get_object_or_404(Tutor, id=tutor_id)
    
    # Verificar permisos
    user_institution = request.user.userprofile.institution if hasattr(request.user, 'userprofile') else None
    if not _usuario_puede_gestionar_tutor(request.user, tutor, user_institution):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para cambiar el estado de este tutor.'
            }, status=403)
        messages.error(request, "No tienes permiso para cambiar el estado de este tutor.")
        return redirect('detalle_tutor', tutor_id=tutor.id)
    
    if request.method == 'POST':
        nuevo_status = request.POST.get('status')
        
        # Validar estado
        if nuevo_status not in ['activo', 'inactivo', 'suspendido']:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Estado inválido.'
                }, status=400)
            messages.error(request, "Estado inválido.")
            return redirect('detalle_tutor', tutor_id=tutor.id)
        
        try:
            vinculacion = TutorService.cambiar_estado_tutor(
                tutor, 
                user_institution, 
                nuevo_status, 
                request.user
            )
            
            # Responder según tipo de solicitud
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                accion = 'habilitado' if nuevo_status == 'activo' else 'deshabilitado'
                return JsonResponse({
                    'success': True,
                    'nuevo_status': nuevo_status,
                    'tutor_nombre': tutor.get_nombre_completo(),
                    'message': f'El tutor "{tutor.get_nombre_completo()}" fue {accion}.'
                })
            
            accion = 'habilitado' if nuevo_status == 'activo' else 'deshabilitado'
            messages.success(
                request,
                f'El tutor "{tutor.get_nombre_completo()}" fue {accion}.'
            )
        except ValidationError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, str(e))
    
    # Redirección por defecto para GET o fallos
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido.'
        }, status=405)
    
    return redirect('detalle_tutor', tutor_id=tutor.id)
