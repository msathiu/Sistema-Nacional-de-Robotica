import logging
from django.db import transaction
from django.contrib.auth.models import User
from ..models import UserProfile

logger = logging.getLogger(__name__)

class IdentityService:
    """
    Servicio centralizado para la gestión de Identidad (Usuarios y Perfiles).
    Mueve la lógica implícita de los signals a métodos explícitos.
    """

    @staticmethod
    def create_user_with_profile(username, email, password=None, user_type='participante', institution=None, **profile_data):
        """
        Crea un usuario y su perfil asociado en una sola transacción.
        """
        with transaction.atomic():
            # Marcar el usuario para que los signals no actúen redundantemente
            user_obj = User(
                username=username,
                email=email,
                is_active=False # Por defecto inactivo hasta aprobación
            )
            if password:
                user_obj.set_password(password)
            
            user_obj._identity_service_handled = True
            user_obj.save()
            
            profile = UserProfile.objects.create(
                user=user_obj,
                user_type=user_type,
                institution=institution,
                **profile_data
            )
            
            # Aplicar permisos iniciales según el tipo
            IdentityService._apply_permissions_by_role(user_obj, user_type)
            
            logger.info(f"Usuario {username} creado con perfil {user_type}")
            return user_obj, profile

    @staticmethod
    def update_user_role(user, new_user_type):
        """
        Actualiza el rol de un usuario y sus flags de Django (is_staff, is_superuser).
        Reemplaza la lógica de sync_user_permissions (signal).
        """
        with transaction.atomic():
            profile = user.userprofile
            profile.user_type = new_user_type
            profile.save(update_fields=['user_type'])
            
            # Marcamos al usuario para evitar re-procesamiento en signals si hubiera
            user._identity_service_handled = True
            IdentityService._apply_permissions_by_role(user, new_user_type)
            logger.info(f"Rol de usuario {user.username} actualizado a {new_user_type}")

    @staticmethod
    def toggle_user_status(user, is_active):
        """
        Activa o desactiva un usuario y sincroniza su institución si aplica.
        Reemplaza la lógica circular de activación en signals.
        """
        with transaction.atomic():
            user.is_active = is_active
            # Usar flag para silenciar signals redundantes
            user._identity_service_handled = True
            user.save(update_fields=['is_active'])
            
            # Sincronizar con institución si es un usuario institucional
            if hasattr(user, 'userprofile') and user.userprofile.institution:
                inst = user.userprofile.institution
                if inst.activa != is_active:
                    inst.activa = is_active
                    # También marcamos la institución para silenciar sus signals circulares
                    inst._identity_service_handled = True
                    inst.save(update_fields=['activa'])
            
            logger.info(f"Estado de usuario {user.username} cambiado a: {is_active}")

    @staticmethod
    def _apply_permissions_by_role(user, user_type):
        """
        Lógica interna para mapear roles a flags de Django.
        """
        updated = False
        is_staff, is_superuser = False, False

        if user_type in ['superuser', 'tecnologico']:
            is_staff, is_superuser = True, True
        elif user_type == 'fed_central':
            is_staff, is_superuser = True, False
        
        if user.is_staff != is_staff or user.is_superuser != is_superuser:
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            updated = True
        
        if updated:
            user.save(update_fields=['is_staff', 'is_superuser'])
