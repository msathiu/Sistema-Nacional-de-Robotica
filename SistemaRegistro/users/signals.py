import logging
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from users.models import UserProfile  # Asegúrate de que la ruta sea correcta

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea el perfil de usuario automáticamente al crear un User.
    Respeta la bandera _skip_profile_creation enviada desde el Admin.
    """
    if created:
        # Si fue manejado por un servicio explícito, no duplicar lógica
        if getattr(instance, "_identity_service_handled", False):
            return

        # Si el Admin nos dice que saltemos la creación (porque él lo manejará)
        if getattr(instance, "_skip_profile_creation", False):
            logger.info(
                f"Saltando creación de perfil para {instance.username} (manejado por Admin)"
            )
            return

        # Usamos get_or_create como red de seguridad absoluta
        UserProfile.objects.get_or_create(user=instance)
        logger.info(
            f"Perfil creado automáticamente para el usuario: {instance.username}"
        )


@receiver(pre_save, sender=User)
def detectar_activacion_usuario(sender, instance, **kwargs):
    # ... (Tu código actual de detectar_activacion se mantiene igual) ...
    if instance.pk:
        try:
            instance._estado_anterior = User.objects.get(pk=instance.pk)
        except User.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=User)
def sincronizar_activacion_usuario(sender, instance, created, **kwargs):
    """
    Sincroniza la activación del usuario con su institución.
    """
    if created:
        return

    # Si fue manejado por un servicio explícito, no duplicar lógica
    if getattr(instance, "_identity_service_handled", False):
        logger.info(
            f"Omitiendo señales para {instance.username} (Manejado por IdentityService)"
        )
        return

    if not hasattr(instance, "_estado_anterior") or instance._estado_anterior is None:
        return

    estado_anterior = instance._estado_anterior
    fue_activado = not estado_anterior.is_active and instance.is_active

    institucion = getattr(instance, "institucion", None)
    if not institucion:
        from registry.models import Institucion

        institucion = Institucion.objects.filter(codigo=instance.username).first()

    if institucion and institucion.activa != instance.is_active:
        institucion.activa = instance.is_active
        institucion.save(update_fields=["activa"])
        logger.info(
            f"Institución {institucion.nombre} sincronizada: activa={instance.is_active}"
        )

    if hasattr(instance, "_estado_anterior"):
        delattr(instance, "_estado_anterior")
