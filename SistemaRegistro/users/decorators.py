from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.apps import apps 


def not_superuser_required(view_func):
    """
    Decorador que bloquea el acceso de superusuarios a vistas de usuarios normales.
    Los superusuarios solo deben acceder al admin de Django.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            messages.warning(
                request, 
                'Los superusuarios solo pueden acceder al panel de administración.'
            )
            return redirect('/admin/')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(allowed_roles):
    """
    Decorador genérico que verifica que el usuario tenga uno de los roles permitidos.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, 'No tienes un perfil de usuario configurado.')
                return redirect('dashboard')
            
            user_profile = request.user.userprofile
            if user_profile.user_type in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(
                request,
                f'No tienes permiso para acceder a esta página. Tu rol: {user_profile.get_user_type_display()}'
            )
            return redirect('dashboard')
        return wrapper
    return decorator


def admin_access_required(view_func):
    """
    Solo el superuser de Django (is_staff) puede acceder.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Solo superusuarios pueden acceder al panel de administración.')
        return redirect('dashboard')
    return wrapper


def fed_central_required(view_func):
    """Requiere ser Federación Central o Tecnológico."""
    return role_required(['fed_central', 'tecnologico'])(view_func)


def fed_regional_required(view_func):
    """Requiere ser Federación Regional"""
    return role_required(['fed_regional'])(view_func)


def fed_any_required(view_func):
    """Cualquier usuario de Federación (Central o Regional)"""
    return role_required(['fed_central', 'fed_regional', 'tecnologico'])(view_func)


def institucional_required(view_func):
    """Requiere ser Usuario Institucional"""
    return role_required(['institucional'])(view_func)


def participante_required(view_func):
    """Requiere ser Participante"""
    return role_required(['participante'])(view_func)


def admin_required(view_func):
    """Cualquier rol administrativo (Fed Central, Fed Regional, Admin)"""
    return role_required(['admin', 'fed_central', 'fed_regional', 'tecnologico'])(view_func)


def fed_central_cannot_create(redirect_to='dashboard'):
    """
    Bloquea a usuarios fed_central de crear recursos (pero permite ver/gestionar).
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, 'No tienes un perfil configurado.')
                return redirect('dashboard')
            
            user_type = request.user.userprofile.user_type
            if user_type == 'fed_central':
                messages.warning(
                    request, 
                    'Como Federación Central no puedes crear nuevos registros, solo supervisarlos.'
                )
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_or_owner_required(view_func):
    """
    Permite acceso si es admin/federación O si es el dueño institucional del recurso.
    Requiere que la vista reciba 'institucion_id'.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, institucion_id, *args, **kwargs):
        user_profile = request.user.userprofile
        user_type = user_profile.user_type
        
        # 1. Acceso Administrativo/Federación
        if user_type in ['admin', 'fed_central', 'tecnologico', 'fed_regional']:
            # Si es regional, validar que sea de su estado
            if user_type == 'fed_regional':
                Institucion = apps.get_model('registry', 'Institucion')
                inst = get_object_or_404(Institucion, id=institucion_id)
                if inst.estado != user_profile.estado:
                    messages.error(request, 'No tienes permiso sobre instituciones de otros estados.')
                    return redirect('lista_instituciones')
            return view_func(request, institucion_id, *args, **kwargs)
        
        # 2. Acceso Propietario (Institucional)
        if user_type == 'institucional' and user_profile.institution:
            if str(user_profile.institution.id) == str(institucion_id):
                return view_func(request, institucion_id, *args, **kwargs)

        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('dashboard')
    return wrapper


def can_export_participantes_required(view_func):
    """
    Decorador específico para exportación de participantes.
    Requiere: institucional, fed_regional, fed_central, superuser o tecnologico.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile'):
            messages.error(request, 'No tienes un perfil de usuario configurado.')
            return redirect('dashboard')
        
        if request.user.userprofile.can_export_participantes:
            return view_func(request, *args, **kwargs)
        
        messages.error(
            request,
            f'No tienes permiso para exportar participantes. Tu rol: {request.user.userprofile.get_user_type_display()}'
        )
        return redirect('lista_participantes')
    return wrapper


def can_delete_participantes_required(view_func):
    """
    Decorador específico para eliminar participantes del padrón.
    Solo fed_central, superuser y tecnologico pueden eliminar.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile'):
            messages.error(request, 'No tienes un perfil de usuario configurado.')
            return redirect('dashboard')
        
        if request.user.userprofile.can_delete_participantes:
            return view_func(request, *args, **kwargs)
        
        messages.error(
            request,
            'Solo la Federación Central puede eliminar participantes del padrón nacional.'
        )
        return redirect('lista_participantes')
    return wrapper


def can_create_participante_required(view_func):
    """
    Decorador específico para creación de participantes.
    Todos excepto fed_central pueden crear.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile'):
            messages.error(request, 'No tienes un perfil de usuario configurado.')
            return redirect('dashboard')
        
        if request.user.userprofile.can_create_participante:
            return view_func(request, *args, **kwargs)
        
        messages.warning(
            request,
            'Como Federación Central no puedes crear nuevos participantes, solo supervisarlos.'
        )
        return redirect('lista_participantes')
    return wrapper
