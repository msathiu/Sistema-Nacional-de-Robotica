import logging

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def detectar_activacion_usuario(sender, instance, **kwargs):
    """
    Detecta cuando un usuario está siendo activado.
    Guarda el estado anterior en una variable temporal.
    """
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
    Sincroniza el estado de activación del usuario con la institución asociada.
    No envía correo; el envío de correo se maneja únicamente desde la activación de la institución.
    """
    # No sincronizar si es una creación nueva
    if created:
        return

    # Verificar si hay estado anterior guardado
    if not hasattr(instance, "_estado_anterior") or instance._estado_anterior is None:
        return

    estado_anterior = instance._estado_anterior

    # Detectar activación: cambio de inactivo a activo
    fue_activado = not estado_anterior.is_active and instance.is_active

    # Intentar obtener la institución
    institucion = getattr(instance, "institucion", None)
    if not institucion:
        from registry.models import Institucion

        institucion = Institucion.objects.filter(codigo=instance.username).first()

    # Sincronizar estado de la institución
    if institucion and institucion.activa != instance.is_active:
        institucion.activa = instance.is_active
        institucion.save(update_fields=["activa"])
        logger.info(
            f"Institución {institucion.nombre} sincronizada: activa={instance.is_active}"
        )

    # Limpiar estado anterior
    if hasattr(instance, "_estado_anterior"):
        delattr(instance, "_estado_anterior")
