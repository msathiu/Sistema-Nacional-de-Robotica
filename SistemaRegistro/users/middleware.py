"""
Middlewares personalizados para la aplicación users.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
import time


class RateLimitMiddleware:
    """
    Middleware para limitar la tasa de solicitudes y prevenir abuso.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        self.blocked_ips = {}
    
    def __call__(self, request):
        # Obtener IP del cliente
        ip = self._get_client_ip(request)
        
        # Verificar si la IP está bloqueada
        if ip in self.blocked_ips:
            if time.time() - self.blocked_ips[ip] < 300:  # 5 minutos de bloqueo
                return HttpResponseForbidden("Demasiadas solicitudes. Intente más tarde.")
            else:
                del self.blocked_ips[ip]
        
        # Contar solicitudes por IP
        current_time = time.time()
        if ip not in self.request_counts:
            self.request_counts[ip] = []
        
        # Limpiar solicitudes antiguas (más de 1 minuto)
        self.request_counts[ip] = [
            t for t in self.request_counts[ip] 
            if current_time - t < 60
        ]
        
        # Verificar límite (100 solicitudes por minuto)
        if len(self.request_counts[ip]) > 100:
            self.blocked_ips[ip] = current_time
            return HttpResponseForbidden("Demasiadas solicitudes. Intente más tarde.")
        
        self.request_counts[ip].append(current_time)
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware:
    """
    Middleware para agregar headers de seguridad a las respuestas.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response


class SuperuserAdminOnlyMiddleware:
    """
    Middleware que restringe a los superusuarios para que solo puedan acceder
    al panel de administración de Django (/admin/).
    
    Esto evita que superusuarios accedan accidentalmente a vistas de usuarios normales
    como /dashboard/, /instituciones/, etc.
    """
    
    # Rutas permitidas para superusuarios
    ALLOWED_PATHS = [
        '/admin/',           # Panel de administración
        '/admin/login/',     # Login del admin
        '/admin/logout/',    # Logout del admin
        '/logout/',          # Logout general
        '/login/',           # Login (para redirección)
    ]
    
    # Prefijos de rutas permitidas
    ALLOWED_PREFIXES = [
        '/admin/',           # Todo lo que empiece con /admin/
    ]
    
    # Rutas de archivos estáticos y media (siempre permitidas)
    STATIC_PREFIXES = [
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Procesar la solicitud antes de la vista
        if self._should_restrict(request):
            # Verificar si la ruta está permitida
            if not self._is_allowed_path(request.path):
                messages.warning(
                    request,
                    'Como superusuario, solo puedes acceder al panel de administración.'
                )
                return redirect('/admin/')
        
        response = self.get_response(request)
        return response
    
    def _should_restrict(self, request):
        """
        Determina si se debe aplicar la restricción.
        Solo se aplica a usuarios autenticados que sean superusuarios.
        """
        # No aplicar si el usuario no está autenticado
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Solo aplicar a superusuarios
        return request.user.is_superuser
    
    def _is_allowed_path(self, path):
        """
        Verifica si la ruta está permitida para superusuarios.
        """
        # Rutas de archivos estáticos siempre permitidas
        for prefix in self.STATIC_PREFIXES:
            if path.startswith(prefix):
                return True
        
        # Verificar rutas exactas
        if path in self.ALLOWED_PATHS:
            return True
        
        # Verificar prefijos permitidos
        for prefix in self.ALLOWED_PREFIXES:
            if path.startswith(prefix):
                return True
        
        # Verificar si es una ruta AJAX o API del admin
        if '/admin/' in path:
            return True
        
        return False


class RoleBasedAccessMiddleware:
    """
    Middleware que controla el acceso a rutas basándose en el rol del usuario.
    
    PROTECCIÓN DEL ADMIN:
    - SOLO superuser puede acceder a /admin/ (panel de administración de Django)
    - Todos los demás roles (tecnologico, fed_central, institucional, participante, fed_regional)
      son redirigidos a su dashboard correspondiente
    
    PROTECCIÓN DE RUTAS POR ROL:
    - institucional: Solo puede acceder a rutas de institución
    - participante: Solo puede acceder a rutas de participante
    - fed_regional: Solo puede acceder a rutas de federación regional
    - tecnologico: Puede acceder a rutas de federación e instituciones (NO al admin)
    - fed_central: Puede acceder a rutas de federación e instituciones (NO al admin)
    - superuser: Solo puede acceder a /admin/ (restringido por SuperuserAdminOnlyMiddleware)
    """
    
    # Roles que pueden acceder al admin de Django - SOLO SUPERUSER
    ADMIN_ALLOWED_ROLES = ['superuser']
    
    # Rutas del admin de Django
    ADMIN_PATHS = ['/admin/', '/admin/dashboard/', '/admin/logs/']
    
    # Rutas públicas (accesibles sin autenticación)
    PUBLIC_PATHS = ['/', '/login/', '/register/', '/logout/']
    
    # Rutas de archivos estáticos y media
    STATIC_PREFIXES = ['/static/', '/media/']
    
    # Mapeo de rutas permitidas por rol
    ROLE_ROUTE_PERMISSIONS = {
        'institucional': {
            'allowed_prefixes': ['/institucion/', '/participantes/', '/eventos/', '/grupos/', '/mis-grupos/', '/perfil/', '/ajax/', '/api/'],
            'allowed_exact': ['/dashboard/', '/dashboard/institucional/'],
            'denied_prefixes': ['/admin/', '/sedes/', '/federacion/'],
        },
        'participante': {
            'allowed_prefixes': ['/participante/', '/eventos/', '/grupos/', '/mis-grupos/', '/perfil/', '/ajax/'],
            'allowed_exact': ['/dashboard/', '/dashboard/participante/'],
            'denied_prefixes': ['/admin/', '/instituciones/', '/sedes/', '/federacion/', '/institucion/'],
        },
        'fed_regional': {
            'allowed_prefixes': ['/federacion/', '/instituciones/', '/participantes/', '/eventos/', '/perfil/', '/ajax/', '/api/'],
            'allowed_exact': ['/dashboard/'],
            'denied_prefixes': ['/admin/', '/sedes/registrar/'],
        },
        'fed_central': {
            'allowed_prefixes': ['/federacion/', '/instituciones/', '/sedes/', '/participantes/', '/eventos/', '/perfil/', '/ajax/', '/api/'],
            'allowed_exact': ['/dashboard/'],
            'denied_prefixes': ['/admin/'],
        },
        'tecnologico': {
            'allowed_prefixes': ['/federacion/', '/instituciones/', '/sedes/', '/participantes/', '/eventos/', '/perfil/', '/ajax/', '/api/'],
            'allowed_exact': ['/dashboard/'],
            'denied_prefixes': ['/admin/'],
        },
        'superuser': {
            # El superusuario SOLO puede acceder al admin de Django
            # SuperuserAdminOnlyMiddleware se encarga de esta restricción
            'allowed_prefixes': ['/admin/'],
            'allowed_exact': ['/admin/', '/login/', '/logout/'],
            'denied_prefixes': ['/dashboard/', '/institucion/', '/federacion/', '/participante/', '/instituciones/', '/sedes/', '/participantes/', '/eventos/', '/grupos/', '/mis-grupos/', '/perfil/'],
        },
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Procesar la solicitud antes de la vista
        if self._should_check_access(request):
            # Verificar acceso al admin
            if self._is_admin_path(request.path):
                if not self._can_access_admin(request):
                    messages.error(
                        request,
                        'No tienes permiso para acceder al panel de administración.'
                    )
                    return redirect(self._get_user_dashboard(request))
            
            # Verificar acceso a rutas según rol
            if not self._can_access_route(request):
                messages.warning(
                    request,
                    'No tienes permiso para acceder a esta sección.'
                )
                return redirect(self._get_user_dashboard(request))
        
        response = self.get_response(request)
        return response
    
    def _should_check_access(self, request):
        """
        Determina si se debe verificar el acceso.
        No aplica para rutas públicas, estáticas o usuarios no autenticados.
        """
        # No verificar si el usuario no está autenticado
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # No verificar rutas públicas
        if request.path in self.PUBLIC_PATHS:
            return False
        
        # No verificar archivos estáticos
        for prefix in self.STATIC_PREFIXES:
            if request.path.startswith(prefix):
                return False
        
        return True
    
    def _is_admin_path(self, path):
        """Verifica si la ruta es del admin de Django"""
        for admin_path in self.ADMIN_PATHS:
            if path.startswith(admin_path):
                return True
        return path.startswith('/admin/')
    
    def _can_access_admin(self, request):
        """
        Verifica si el usuario puede acceder al admin de Django.
        SOLO superuser tiene acceso.
        """
        try:
            user_profile = request.user.userprofile
            return user_profile.user_type in self.ADMIN_ALLOWED_ROLES
        except:
            # Si no tiene perfil, verificar si es superuser de Django
            return request.user.is_superuser and request.user.is_staff
    
    def _can_access_route(self, request):
        """
        Verifica si el usuario puede acceder a la ruta actual según su rol.
        """
        try:
            user_profile = request.user.userprofile
            user_type = user_profile.user_type
        except:
            # Si no tiene perfil, permitir acceso (se manejará en otro punto)
            return True
        
        # Obtener permisos para el rol del usuario
        permissions = self.ROLE_ROUTE_PERMISSIONS.get(user_type)
        if not permissions:
            # Rol no reconocido, denegar acceso a rutas protegidas
            return not self._is_admin_path(request.path)
        
        path = request.path
        
        # Verificar rutas denegadas explícitamente
        for denied_prefix in permissions.get('denied_prefixes', []):
            if path.startswith(denied_prefix):
                return False
        
        # Verificar rutas permitidas exactas
        if path in permissions.get('allowed_exact', []):
            return True
        
        # Verificar prefijos permitidos
        for allowed_prefix in permissions.get('allowed_prefixes', []):
            if path.startswith(allowed_prefix):
                return True
        
        # Ruta específica para dashboard principal
        if path == '/dashboard/':
            return True
        
        # Rutas AJAX y API son accesibles para usuarios autenticados
        if path.startswith('/ajax/') or path.startswith('/api/'):
            return True
        
        # Por defecto, permitir acceso a rutas no explícitamente denegadas
        # Esto evita bloquear rutas legítimas que no están en la lista
        return True
    
    def _get_user_dashboard(self, request):
        """Obtiene la URL del dashboard correspondiente según el rol del usuario"""
        try:
            user_profile = request.user.userprofile
            user_type = user_profile.user_type
            
            dashboards = {
                'participante': 'dashboard_participante',
                'institucional': 'dashboard_institucional',
                'fed_regional': 'dashboard',
                'fed_central': 'dashboard',  # fed_central va al dashboard general, NO al admin
                'tecnologico': 'dashboard',   # tecnologico va al dashboard general, NO al admin
                'superuser': '/admin/',        # Solo superuser va al admin
            }
            
            dashboard = dashboards.get(user_type, 'dashboard')
            return dashboard
        except:
            return 'dashboard'
