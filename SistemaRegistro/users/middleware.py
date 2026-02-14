"""
Middleware de seguridad personalizado
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware para limitar peticiones por IP
    """

    def process_request(self, request):
        # Solo aplicar rate limiting a endpoints AJAX y búsquedas
        if not any(path in request.path for path in ["/ajax/", "/buscar-", "/api/"]):
            return None

        # Obtener IP del cliente
        ip = self.get_client_ip(request)

        # Clave de cache única por IP y path
        cache_key = f"rate_limit_{ip}_{request.path}"

        # Obtener contador de peticiones
        requests = cache.get(cache_key, 0)

        # Límite: 60 peticiones por minuto
        if requests >= 60:
            logger.warning(f"Rate limit excedido para IP {ip} en {request.path}")
            return JsonResponse(
                {"error": "Demasiadas peticiones. Intenta de nuevo en un minuto."},
                status=429,
            )

        # Incrementar contador
        cache.set(cache_key, requests + 1, 60)  # Expira en 60 segundos

        return None

    @staticmethod
    def get_client_ip(request):
        """Obtener IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para agregar headers de seguridad adicionales
    """

    def process_response(self, request, response):
        # Prevenir clickjacking
        response["X-Frame-Options"] = "DENY"

        # Prevenir MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # XSS Protection
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
