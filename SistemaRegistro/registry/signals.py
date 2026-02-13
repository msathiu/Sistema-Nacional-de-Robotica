"""
Señales para el modelo Institucion.
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Institucion

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Institucion)
def detectar_activacion_institucion(sender, instance, **kwargs):
    """
    Detecta cuando una institución está siendo activada.
    Guarda el estado anterior en una variable temporal.
    """
    if instance.pk:
        try:
            instance._estado_anterior = Institucion.objects.get(pk=instance.pk)
        except Institucion.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Institucion)
def enviar_correo_activacion_institucion(sender, instance, created, **kwargs):
    """
    Envía correo de activación cuando una institución es activada.

    Condiciones para enviar correo:
    - La institución pasa de inactiva (activa=False) a activa (activa=True)
    - El código es permanente (RNR), NO temporal (TEMP-)
    - Tiene un usuario asociado

    También sincroniza el estado del usuario (is_active) con la institución.
    """
    # No enviar correo si es una creación nueva
    if created:
        logger.info(f"Institución {instance.nombre} creada. No se envía correo aún.")
        return

    # Verificar si hay estado anterior guardado
    if not hasattr(instance, "_estado_anterior") or instance._estado_anterior is None:
        return

    estado_anterior = instance._estado_anterior

    # Detectar activación: cambio de inactiva a activa
    fue_activada = not estado_anterior.activa and instance.activa

    # Verificar que el código sea permanente (RNR), no temporal (TEMP-)
    tiene_codigo_permanente = (
        instance.codigo
        and instance.codigo.startswith("RNR")
        and not instance.codigo.startswith("TEMP-")
    )

    # Sincronizar estado del usuario con la institución
    if instance.usuario:
        if instance.usuario.is_active != instance.activa:
            instance.usuario.is_active = instance.activa
            instance.usuario.save(update_fields=["is_active"])
            logger.info(
                f"Usuario {instance.usuario.username} sincronizado: "
                f"is_active={instance.activa}"
            )

    # Enviar correo SOLO si:
    # 1. Fue activada
    # 2. Tiene código permanente (RNR)
    # 3. Tiene usuario asociado
    if fue_activada and tiene_codigo_permanente and instance.usuario:
        logger.info(
            f"Activación detectada para {instance.nombre}. "
            f"Activa: {estado_anterior.activa} -> {instance.activa}, "
            f"Código: {estado_anterior.codigo} -> {instance.codigo}"
        )

        # Enviar correo
        resultado = instance.enviar_correo_activacion()

        if resultado:
            logger.info(f"Correo de activación enviado exitosamente a {instance.email}")
        else:
            logger.error(f"Error al enviar correo de activación a {instance.email}")
    elif fue_activada and not tiene_codigo_permanente:
        logger.warning(
            f"Institución {instance.nombre} activada pero tiene código temporal. "
            f"No se envía correo. Código: {instance.codigo}"
        )

    # Limpiar estado anterior
    if hasattr(instance, "_estado_anterior"):
        delattr(instance, "_estado_anterior")
