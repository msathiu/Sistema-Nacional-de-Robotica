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


def _sincronizar_usuario_institucion(instance):
    """Sincroniza el estado del usuario con la institución."""
    if instance.usuario and instance.usuario.is_active != instance.activa:
        instance.usuario.is_active = instance.activa
        instance.usuario.save(update_fields=["is_active"])
        logger.info(
            f"Usuario {instance.usuario.username} sincronizado: "
            f"is_active={instance.activa}"
        )


def _enviar_correo_si_corresponde(instance, estado_anterior, fue_activada, tiene_codigo_permanente):
    """Envía correo de activación si se cumplen las condiciones."""
    if fue_activada and tiene_codigo_permanente and instance.usuario:
        logger.info(
            f"Activación detectada para {instance.nombre}. "
            f"Activa: {estado_anterior.activa} -> {instance.activa}, "
            f"Código: {estado_anterior.codigo} -> {instance.codigo}"
        )
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
    if created:
        logger.info(f"Institución {instance.nombre} creada. No se envía correo aún.")
        return

    if not hasattr(instance, "_estado_anterior") or instance._estado_anterior is None:
        return

    estado_anterior = instance._estado_anterior
    fue_activada = not estado_anterior.activa and instance.activa
    tiene_codigo_permanente = (
        instance.codigo
        and instance.codigo.startswith("RNR")
        and not instance.codigo.startswith("TEMP-")
    )

    _sincronizar_usuario_institucion(instance)
    _enviar_correo_si_corresponde(instance, estado_anterior, fue_activada, tiene_codigo_permanente)

    if hasattr(instance, "_estado_anterior"):
        delattr(instance, "_estado_anterior")
