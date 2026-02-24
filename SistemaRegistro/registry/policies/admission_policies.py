"""
Políticas de acceso para el proceso de admisión a clubes.

Este módulo implementa decoradores de permisos según permisos_clubes.md,
asegurando que cada actor solo pueda ejecutar su fase del proceso.

Reglas Implementadas:
- Sección 6, Paso 2: Solo Institución Fundadora puede dar visto bueno.
- Sección 6, Paso 3: Solo Ente Rector puede aprobar finalmente.
- Sección 6: El Ente Rector tiene visibilidad de todas las membresías.

Autor: Sistema de Registro
Fecha: 2026
"""

from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from ..models import MembresiaClu, Club


def es_fundadora_del_club(view_func):
    """
    Decorador que verifica si el usuario es de la Institución Fundadora del club.
    
    Regla: permisos_clubes.md - Sección 6, Paso 2
    "Solo usuarios con rol Institucional y FUNDADORA pueden ejecutar el paso 2"
    
    Este decorador extrae el club_id o membresia_id de los kwargs de la vista
    y verifica que el usuario pertenezca a la institución creadora del club.
    
    Args:
        view_func: Función de vista a decorar.
        
    Returns:
        function: Vista decorada con verificación de permisos.
        
    Raises:
        PermissionDenied: Si el usuario no es de la institución fundadora.
        
    Usage:
        @login_required
        @es_fundadora_del_club
        def dar_visto_bueno(request, membresia_id):
            # Solo llega aquí si es fundadora
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Intentar obtener el club de diferentes fuentes
        club_id = kwargs.get('club_id')
        membresia_id = kwargs.get('membresia_id')
        pk = kwargs.get('pk')
        
        club = None
        
        if membresia_id:
            # Si hay membresia_id, obtener el club desde la membresía
            membresia = get_object_or_404(
                MembresiaClu.objects.select_related('club'),
                id=membresia_id
            )
            club = membresia.club
        elif club_id:
            club = get_object_or_404(Club, id=club_id)
        elif pk:
            # Intentar usar pk como club_id
            try:
                club = Club.objects.get(id=pk)
            except Club.DoesNotExist:
                pass
        
        if not club:
            messages.error(request, "No se pudo identificar el club.")
            return redirect('clubes_lista')
        
        # Verificar que el usuario tiene perfil institucional
        if not hasattr(request.user, 'userprofile'):
            messages.error(
                request, 
                "No tienes un perfil institucional asociado a tu cuenta."
            )
            return redirect('clubes_lista')
        
        if not request.user.userprofile.institution:
            messages.error(
                request,
                "Tu perfil no está vinculado a ninguna institución."
            )
            return redirect('clubes_lista')
        
        # Verificar que es la institución fundadora
        if club.institucion_creadora != request.user.userprofile.institution:
            raise PermissionDenied(
                "Solo la Institución Fundadora del club puede realizar esta acción."
            )
        
        # Agregar el club al request para uso posterior
        request.club = club
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def es_ente_rector(view_func):
    """
    Decorador que verifica si el usuario tiene rol de Ente Rector.
    
    Regla: permisos_clubes.md - Sección 6, Paso 3
    "Solo usuarios con rol RECTORA ente rector pueden ejecutar el paso 3"
    
    Este decorador verifica que el usuario tenga user_type='fed_central'.
    
    Args:
        view_func: Función de vista a decorar.
        
    Returns:
        function: Vista decorada con verificación de permisos.
        
    Raises:
        PermissionDenied: Si el usuario no es del Ente Rector.
        
    Usage:
        @login_required
        @es_ente_rector
        def aprobar_membresia_rector(request, membresia_id):
            # Solo llega aquí si es Ente Rector
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar que el usuario tiene perfil
        if not hasattr(request.user, 'userprofile'):
            messages.error(
                request,
                "No tienes un perfil asociado a tu cuenta."
            )
            return redirect('dashboard')
        
        # Verificar que es Ente Rector (Federación Central)
        if request.user.userprofile.user_type != 'fed_central':
            raise PermissionDenied(
                "Solo el Ente Rector (Federación Central) puede realizar esta acción."
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def puede_ver_membresia(view_func):
    """
    Decorador que controla la visibilidad de membresías según el rol.
    
    Regla: permisos_clubes.md - Sección 6
    "El Ente Rector tiene visibilidad de todas las membresías en cualquier estado"
    
    Permisos de visualización:
    - Ente Rector: Ve todas las membresías.
    - Institución Fundadora: Ve membresías de sus clubes.
    - Institución Solicitante: Ve sus propias solicitudes.
    
    Args:
        view_func: Función de vista a decorar.
        
    Returns:
        function: Vista decorada con verificación de visibilidad.
        
    Raises:
        PermissionDenied: Si el usuario no tiene permiso para ver la membresía.
        
    Usage:
        @login_required
        @puede_ver_membresia
        def detalle_membresia(request, membresia_id):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        membresia_id = kwargs.get('membresia_id')
        
        if not membresia_id:
            messages.error(request, "Membresía no especificada.")
            return redirect('mis_membresias')
        
        membresia = get_object_or_404(
            MembresiaClu.objects.select_related('club', 'institucion', 'club__institucion_creadora'),
            id=membresia_id
        )
        
        # Verificar permisos
        tiene_permiso = False
        
        if hasattr(request.user, 'userprofile'):
            user_type = request.user.userprofile.user_type
            institution = request.user.userprofile.institution
            
            # Ente Rector: ve todo
            if user_type == 'fed_central':
                tiene_permiso = True
            # Federación Regional: ve membresías de su estado
            elif user_type == 'fed_regional':
                # Por implementar: filtrar por estado
                tiene_permiso = True
            # Institución: ve lo relacionado con ella
            elif institution:
                # Fundadora: ve membresías de sus clubes
                if membresia.club.institucion_creadora == institution:
                    tiene_permiso = True
                # Solicitante: ve sus propias solicitudes
                elif membresia.institucion == institution:
                    tiene_permiso = True
        
        if not tiene_permiso:
            raise PermissionDenied(
                "No tienes permiso para ver esta membresía."
            )
        
        # Agregar la membresía al request para uso posterior
        request.membresia = membresia
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def puede_gestionar_fundadora(view_func):
    """
    Decorador que verifica si el usuario puede gestionar membresías como fundadora.
    
    Regla: permisos_clubes.md - Sección 6, Paso 2
    "Solo usuarios con rol Institucional y FUNDADORA pueden ejecutar el paso 2"
    
    Verifica:
    1. El usuario tiene perfil institucional.
    2. El usuario pertenece a la institución fundadora del club.
    3. La membresía está en estado 'pendiente_filtro'.
    
    Args:
        view_func: Función de vista a decorar.
        
    Returns:
        function: Vista decorada con verificación de permisos.
        
    Usage:
        @login_required
        @puede_gestionar_fundadora
        def aprobar_membresia_fundadora(request, membresia_id):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        membresia_id = kwargs.get('membresia_id')
        
        if not membresia_id:
            messages.error(request, "Membresía no especificada.")
            return redirect('clubes_lista')
        
        membresia = get_object_or_404(
            MembresiaClu.objects.select_related('club', 'club__institucion_creadora'),
            id=membresia_id
        )
        
        # Verificar que tiene perfil institucional
        if not hasattr(request.user, 'userprofile') or not request.user.userprofile.institution:
            messages.error(request, "No tienes un perfil institucional asociado.")
            return redirect('clubes_lista')
        
        # Verificar que es la institución fundadora
        if membresia.club.institucion_creadora != request.user.userprofile.institution:
            raise PermissionDenied(
                "Solo la Institución Fundadora puede gestionar esta membresía."
            )
        
        # Verificar que está en estado pendiente
        if membresia.estado != 'pendiente_filtro':
            messages.warning(
                request,
                f"Esta membresía ya fue procesada. Estado actual: {membresia.get_estado_display()}"
            )
            return redirect('gestionar_membresias_club', club_id=membresia.club.id)
        
        request.membresia = membresia
        return view_func(request, *args, **kwargs)
    
    return wrapper


def puede_gestionar_rector(view_func):
    """
    Decorador que verifica si el Ente Rector puede gestionar una membresía.
    
    Regla: permisos_clubes.md - Sección 6, Paso 3
    "Solo usuarios con rol RECTORA ente rector pueden ejecutar el paso 3"
    
    Verifica:
    1. El usuario tiene rol 'fed_central'.
    2. La membresía está en estado 'visto_bueno_fundadora'.
    
    Args:
        view_func: Función de vista a decorar.
        
    Returns:
        function: Vista decorada con verificación de permisos.
        
    Usage:
        @login_required
        @puede_gestionar_rector
        def aprobar_membresia_rector(request, membresia_id):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        membresia_id = kwargs.get('membresia_id')
        
        if not membresia_id:
            messages.error(request, "Membresía no especificada.")
            return redirect('revisar_membresias')
        
        membresia = get_object_or_404(
            MembresiaClu.objects.select_related('club', 'institucion'),
            id=membresia_id
        )
        
        # Verificar que es Ente Rector
        if not hasattr(request.user, 'userprofile'):
            messages.error(request, "No tienes un perfil asociado.")
            return redirect('dashboard')
        
        if request.user.userprofile.user_type != 'fed_central':
            raise PermissionDenied(
                "Solo el Ente Rector puede realizar esta acción."
            )
        
        # Verificar que tiene visto bueno de la fundadora
        if membresia.estado != 'visto_bueno_fundadora':
            messages.warning(
                request,
                f"Esta membresía no tiene visto bueno de la Fundadora. "
                f"Estado actual: {membresia.get_estado_display()}"
            )
            return redirect('revisar_membresias')
        
        request.membresia = membresia
        return view_func(request, *args, **kwargs)
    
    return wrapper


# === Funciones auxiliares para templates ===

def usuario_puede_dar_visto_bueno(usuario, membresia) -> bool:
    """
    Verifica si un usuario puede dar visto bueno a una membresía.
    
    Regla: permisos_clubes.md - Sección 6, Paso 2
    
    Args:
        usuario: Usuario a verificar.
        membresia: Membresía en cuestión.
        
    Returns:
        bool: True si puede dar visto bueno.
    """
    if not hasattr(usuario, 'userprofile') or not usuario.userprofile.institution:
        return False
    
    if membresia.estado != 'pendiente_filtro':
        return False
    
    return membresia.club.institucion_creadora == usuario.userprofile.institution


def usuario_puede_aprobar_rector(usuario, membresia) -> bool:
    """
    Verifica si un usuario (Ente Rector) puede aprobar una membresía.
    
    Regla: permisos_clubes.md - Sección 6, Paso 3
    
    Args:
        usuario: Usuario a verificar.
        membresia: Membresía en cuestión.
        
    Returns:
        bool: True si puede aprobar como rector.
    """
    if not hasattr(usuario, 'userprofile'):
        return False
    
    if usuario.userprofile.user_type != 'fed_central':
        return False
    
    return membresia.estado == 'visto_bueno_fundadora'


def usuario_puede_ver_membresia(usuario, membresia) -> bool:
    """
    Verifica si un usuario puede ver una membresía específica.
    
    Regla: permisos_clubes.md - Sección 6
    "El Ente Rector tiene visibilidad de todas las membresías"
    
    Args:
        usuario: Usuario a verificar.
        membresia: Membresía en cuestión.
        
    Returns:
        bool: True si puede ver la membresía.
    """
    if not hasattr(usuario, 'userprofile'):
        return False
    
    user_type = usuario.userprofile.user_type
    institution = usuario.userprofile.institution
    
    # Ente Rector: ve todo
    if user_type == 'fed_central':
        return True
    
    # Federación Regional: ve lo de su estado (por implementar)
    if user_type == 'fed_regional':
        return True
    
    # Institución: ve lo relacionado
    if institution:
        if membresia.club.institucion_creadora == institution:
            return True
        if membresia.institucion == institution:
            return True
    
    return False
