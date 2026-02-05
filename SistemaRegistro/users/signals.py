import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def notificar_aprobacion_usuario(sender, instance, **kwargs):
    # 1. Solo actuar si el usuario ya existe (tiene PK)
    if not instance.pk:
        return

    try:
        # 2. Obtener el estado anterior directamente de la DB
        user_previo = User.objects.filter(pk=instance.pk).only("is_active").first()
        if not user_previo:
            return

        # 3. Detectar el cambio: Inactivo -> Activo
        if not user_previo.is_active and instance.is_active:
            # IMPORTACIÓN LOCAL para evitar errores de "no reconoce" o circulares
            from registry.models import Institucion

            # 4. Intentar obtener la institución
            # Buscamos por la relación o por el código (username)
            institucion = getattr(instance, "institucion", None)
            if not institucion:
                institucion = Institucion.objects.filter(
                    codigo=instance.username
                ).first()

            # 5. Definir variables para el correo
            nombre_inst = institucion.nombre if institucion else instance.username
            codigo_inst = institucion.codigo if institucion else "N/A"

            contexto = {
                "nombre_institucion": nombre_inst,
                "codigo": codigo_inst,
                "usuario": instance.username,
                "login_url": f"{settings.BASE_URL}/login"
                if hasattr(settings, "BASE_URL")
                else "/login",
                "site_name": getattr(
                    settings, "SITE_NAME", "Sistema Nacional de Robótica"
                ),
            }

            # 6. Preparar y enviar correo
            asunto = "🚀 ¡Tu cuenta de Institución ha sido activada!"
            html_content = render_to_string("emails/aprobacion.html", contexto)
            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                subject=asunto,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.email],
            )
            msg.attach_alternative(html_content, "text/html")

            # fail_silently=False para ver errores en consola/logs
            msg.send(fail_silently=False)

            logger.info(f"📧 Correo enviado a: {instance.email}")

    except Exception as e:
        logger.error(f"❌ Error en señal para {instance.email}: {str(e)}")
