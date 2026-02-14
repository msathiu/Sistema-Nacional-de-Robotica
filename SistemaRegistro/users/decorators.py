"""
Decoradores de seguridad personalizados para control de acceso
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """Requiere que el usuario sea administrador"""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if (
            not hasattr(request.user, "userprofile")
            or request.user.userprofile.user_type != "admin"
        ):
            messages.error(request, "No tienes permiso para acceder a esta página.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


def institucional_required(view_func):
    """Requiere que el usuario sea de tipo institucional"""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if (
            not hasattr(request.user, "userprofile")
            or request.user.userprofile.user_type != "institucional"
        ):
            messages.error(request, "No tienes permiso para acceder a esta página.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


def participante_required(view_func):
    """Requiere que el usuario sea participante"""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if (
            not hasattr(request.user, "userprofile")
            or request.user.userprofile.user_type != "participante"
        ):
            messages.error(request, "No tienes permiso para acceder a esta página.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


def owns_institution(view_func):
    """Verifica que el usuario tenga permiso sobre la institución especificada"""

    @wraps(view_func)
    @login_required
    def wrapper(request, institucion_id, *args, **kwargs):
        user_profile = request.user.userprofile

        # Admin puede acceder a todo
        if user_profile.user_type == "admin":
            return view_func(request, institucion_id, *args, **kwargs)

        # Usuario institucional solo puede acceder a su propia institución
        if user_profile.user_type == "institucional":
            if (
                user_profile.institution
                and user_profile.institution.id == institucion_id
            ):
                return view_func(request, institucion_id, *args, **kwargs)

        messages.error(request, "No tienes permiso para modificar esta institución.")
        return redirect("dashboard")

    return wrapper
