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
    Decorador que verifica que el usuario tenga uno de los roles permitidos.
    
    Uso:
        @role_required(['institucional', 'fed_central'])
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                user_profile = request.user.userprofile
                user_type = user_profile.user_type
                
                if user_type in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(
                        request,
                        f'No tienes permiso para acceder a esta página. Tu rol: {user_profile.get_user_type_display()}'
                    )
                    return redirect('dashboard')
            except:
                messages.error(request, 'No tienes un perfil de usuario configurado.')
                return redirect('dashboard')
        return wrapper
    return decorator


def admin_access_required(view_func):
    """
    Decorador que restringe el acceso solo a superusuarios.
    SOLO el superuser puede acceder al panel de administración de Django.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Solo permitir si es superuser de Django
        if request.user.is_superuser and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'No tienes permiso para acceder al panel de administración. Solo superusuarios pueden acceder.')
        return redirect('dashboard')
    return wrapper


def admin_or_owner_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, institucion_id, *args, **kwargs):
        from django.apps import apps
        print(f"\n--- [LOG DECORADOR] ---")
        
        user_profile = request.user.userprofile
        user_type = user_profile.user_type
        print(f"Usuario: {request.user.username} | Rol: {user_type}")
        
        # 1. Acceso Administrativo y REGIONAL
        # He añadido 'fed_regional' a la lista de permisos
        if user_type in ['admin', 'fed_central', 'superuser', 'tecnologico', 'fed_regional']:
            print(f"ACCESO: Concedido por rol {user_type}")
            return view_func(request, institucion_id, *args, **kwargs)
        
        # 2. Acceso Sede (institucional) - Validación por ID
        if user_type == 'institucional':
            if user_profile.institution:
                perfil_inst_id = str(user_profile.institution.id)
                url_inst_id = str(institucion_id)
                print(f"COMPARANDO: Perfil({perfil_inst_id}) vs URL({url_inst_id})")
                
                if perfil_inst_id == url_inst_id:
                    print("ACCESO: Sede autorizada")
                    return view_func(request, institucion_id, *args, **kwargs)
            
            print("ERROR: El usuario institucional no tiene permiso para este ID")

        # Denegar si no cumple nada de lo anterior
        print(f"RESULTADO: Acceso Denegado para el rol {user_type}")
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('lista_instituciones')
    return wrapper

def owns_institution(view_func):
    """Verifica que el usuario tenga permiso sobre la institución especificada"""
    @wraps(view_func)
    @login_required
    def wrapper(request, institucion_id, *args, **kwargs):
        # CARGA DINÁMICA AQUÍ TAMBIÉN
        Institucion = apps.get_model('users', 'Institucion')
        
        user_profile = request.user.userprofile
        
        # Admin puede acceder a todo
        if user_profile.user_type in ['admin', 'fed_central']:
            return view_func(request, institucion_id, *args, **kwargs)
        
        # Usuario institucional solo puede acceder a su propia institución
        if user_profile.user_type == 'institucional':
            inst = get_object_or_404(Institucion, id=institucion_id)
            if inst.usuarios.filter(id=request.user.id).exists():
                return view_func(request, institucion_id, *args, **kwargs)
        
        messages.error(request, 'No tienes permiso para modificar esta institución.')
        return redirect('dashboard')
    
    return wrapper

def admin_required(view_func):
    """Requiere que el usuario sea administrador, federación central o superusuario"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type not in ['admin', 'fed_central', 'superuser']:
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def institucional_required(view_func):
    """Requiere que el usuario sea de tipo institucional"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'institucional':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def participante_required(view_func):
    """Requiere que el usuario sea participante"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'participante':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


