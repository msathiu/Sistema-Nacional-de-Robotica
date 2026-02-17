from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.apps import apps 

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
    """Requiere que el usuario sea administrador"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'admin':
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


