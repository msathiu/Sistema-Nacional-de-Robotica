import logging
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import Institucion

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=User)
def notificar_aprobacion_usuario(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        user_previo = User.objects.filter(pk=instance.pk).only('is_active').first()
        if not user_previo:
            return

        # Detectar el cambio: Inactivo -> Activo
        if not user_previo.is_active and instance.is_active:
            
            # 1. Intentar obtener la institución de dos formas:
            # Forma A: Por la relación directa (si existe)
            institucion = getattr(instance, 'institucion', None)
            
            # Forma B: Si no hay relación, buscarla por el código (username)
            if not institucion:
                # Buscamos la institución cuyo campo 'codigo' coincida con el 'username' del usuario
                institucion = Institucion.objects.filter(codigo=instance.username).first()

            # 2. Asignar variables finales
            if institucion:
                # Si encontramos la institución, usamos sus datos reales
                nombre_inst = institucion.nombre
                codigo_inst = institucion.codigo
            else:
                # Si no existe la institución en la tabla, usamos datos del usuario
                nombre_inst = instance.username
                codigo_inst = "N/A"

            contexto = {
                'nombre_institucion': nombre_inst,
                'codigo': codigo_inst,
                'usuario': instance.username,
                'login_url': f"{settings.BASE_URL}/login",
                'site_name': getattr(settings, 'SITE_NAME', 'Sistema Nacional de Robótica'),
            }

            # 6. Preparar y enviar correo
            asunto = '🚀 ¡Tu cuenta de Institución ha sido activada!'
            html_content = render_to_string('emails/aprobacion.html', contexto)
            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                subject=asunto,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.email]
            )
            msg.attach_alternative(html_content, "text/html")
            
            # fail_silently=False para ver errores de SMTP en los logs de Docker
            msg.send(fail_silently=False)
            
            logger.info(f"📧 Correo de activación enviado con éxito a: {instance.email}")

    except Exception as e:
        # Usar str(e) para no romper la transacción si algo falla aquí
        logger.error(f"❌ Error en señal para {instance.email}: {str(e)}")