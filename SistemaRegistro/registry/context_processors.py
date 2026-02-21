"""Context processors para agregar variables globales a todos los templates."""

from django.core.cache import cache
from registry.models import Club


def notificaciones_no_leidas(request):
    """Agrega el contador de notificaciones no leídas al contexto."""
    if request.user.is_authenticated:
        count = request.user.notificaciones.filter(leida=False).count()
        return {'notificaciones_no_leidas': count}
    return {'notificaciones_no_leidas': 0}


def clubes_pendientes_federacion(request):
    """Contador de clubes pendientes para usuarios de federación."""
    if not request.user.is_authenticated:
        return {}
    
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type not in ['fed_central', 'fed_regional']:
        return {}
    
    cache_key = 'clubes_pendientes_count'
    count = cache.get(cache_key)
    
    if count is None:
        count = Club.objects.filter(status='pendiente', eliminado=False).count()
        cache.set(cache_key, count, 300)
    
    return {
        'clubes_pendientes_count': count,
        'tiene_clubes_pendientes': count > 0
    }


def user_roles(request):
    """Agrega variables de roles de usuario al contexto global."""
    if request.user.is_authenticated:
        try:
            perfil = request.user.userprofile
            return {
                'perfil': perfil,
                'es_central': perfil.user_type == 'fed_central',
                'es_regional': perfil.user_type == 'fed_regional',
                'es_institucional': perfil.user_type == 'institucional',
                'es_participante': perfil.user_type == 'participante',
            }
        except:
            pass
    return {
        'perfil': None,
        'es_central': False,
        'es_regional': False,
        'es_institucional': False,
        'es_participante': False,
    }
