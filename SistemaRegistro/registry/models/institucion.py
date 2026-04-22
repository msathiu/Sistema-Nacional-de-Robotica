import logging
import string
from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import User
from django.apps import apps
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import strip_tags

from .base import normalizar_texto_titulo, Estado, Municipio, Parroquia, Dependencia

logger = logging.getLogger(__name__)


class Institucion(models.Model):
    ESTATUS_CHOICES = [
        ("pendiente", "Pendiente"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    ]

    TIPO_INSTITUCION_CHOICES = [
        ("educativa", "Institución Educativa (Adscrita a MPPE)"),
        ("publica", "Pública"),
        ("privada", "Privada"),
        ("otra", "Otras Instituciones"),
        ("particular", "Particular (Persona Natural)"),
    ]

    NATURALEZA_CHOICES = [
        ("publica", "Pública"),
        ("privada", "Privada"),
    ]

    TIPO_FEDERADO_CHOICES = [
        ("institucion", "Institución Educativa"),
        ("organizacion", "Organización / Club"),
        ("particular", "Particular / Independiente"),
    ]
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="institucion",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=255)
    rif = models.CharField(max_length=20, null=True, blank=True)

    particular_nombres = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Nombres"
    )
    particular_apellidos = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Apellidos"
    )
    particular_nacionalidad = models.CharField(
        max_length=1,
        choices=[("V", "V"), ("E", "E")],
        null=True,
        blank=True,
        verbose_name="Nacionalidad",
    )
    particular_cedula = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Cédula (solo números)",
    )
    tipo_institucion = models.CharField(
        max_length=20, choices=TIPO_INSTITUCION_CHOICES, default="educativa"
    )
    naturaleza = models.CharField(
        max_length=20, choices=NATURALEZA_CHOICES, null=True, blank=True
    )
    subcategoria = models.CharField(max_length=120, null=True, blank=True)
    tipo_federado = models.CharField(
        max_length=20,
        choices=TIPO_FEDERADO_CHOICES,
        default="institucion",
    )
    federado = models.BooleanField(default=False, verbose_name="Federado")
    categoria = models.CharField(max_length=50, null=True, blank=True)
    institucion_procedencia = models.CharField(max_length=120, null=True, blank=True)
    codigo_mppe = models.CharField(max_length=30, null=True, blank=True)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT)
    parroquia = models.ForeignKey(Parroquia, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=35, unique=True, editable=False)
    direccion = models.TextField(blank=True)
    telefono_codigo = models.CharField(max_length=4, null=True, blank=True)
    telefono_numero = models.CharField(max_length=7, null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estatus = models.CharField(
        max_length=20, choices=ESTATUS_CHOICES, default="pendiente"
    )
    activa = models.BooleanField(default=False)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    dependencia = models.CharField(max_length=255, null=True, blank=True)
    dependencia_rel = models.ForeignKey(
        Dependencia, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Instituciones"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["codigo"], name="idx_inst_codigo"),
            models.Index(fields=["email"], name="idx_inst_email"),
            models.Index(fields=["estatus"], name="idx_inst_estatus"),
            models.Index(fields=["activa"], name="idx_inst_activa"),
            models.Index(fields=["estado", "municipio"], name="idx_inst_ubicacion"),
            models.Index(fields=["tipo_institucion"], name="idx_inst_tipo"),
            models.Index(fields=["federado"], name="idx_inst_federado"),
            models.Index(fields=["particular_cedula"], name="idx_inst_part_cedula"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["codigo_mppe"],
                condition=models.Q(eliminado=False)
                & models.Q(tipo_institucion="educativa"),
                name="unique_codigo_mppe_educativas",
            ),
            models.UniqueConstraint(
                fields=["rif", "estado", "municipio", "parroquia"],
                condition=models.Q(eliminado=False)
                & models.Q(tipo_institucion__in=["publica", "privada", "otra"]),
                name="unique_rif_ubicacion_regulares",
            ),
            models.UniqueConstraint(
                fields=["particular_cedula"],
                condition=models.Q(eliminado=False)
                & models.Q(tipo_institucion="particular"),
                name="unique_cedula_particulares",
            ),
        ]

    def generar_codigo_rnr(self):
        year = str(timezone.now().year)[2:]
        e = str(self.estado.id).zfill(3) if self.estado_id else "000"
        m = str(self.municipio.id).zfill(3) if self.municipio_id else "000"
        p = str(self.parroquia.id).zfill(3) if self.parroquia_id else "000"

        prefijo = f"RNR{year}-{e}{m}{p}-"
        chars = string.ascii_uppercase + string.digits

        max_intentos = 100
        for _ in range(max_intentos):
            secuencia = get_random_string(length=8, allowed_chars=chars)
            nuevo_codigo = f"{prefijo}{secuencia}"
            if not Institucion.objects.filter(codigo=nuevo_codigo).exists():
                return nuevo_codigo

        raise ValueError(
            f"No se pudo generar un código RNR único después de {max_intentos} intentos"
        )

    def enviar_correo_activacion(self):
        try:
            context = {
                "site_name": settings.SITE_NAME,
                "nombre_institucion": self.nombre,
                "codigo": self.codigo,
                "usuario": self.codigo,
                "login_url": f"{settings.BASE_URL}/login/",
            }
            html_message = render_to_string("emails/aprobacion.html", context)
            plain_message = strip_tags(html_message)
            send_mail(
                subject=f"Cuenta Activada - {settings.SITE_NAME}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(
                f"Correo de activación enviado a {self.email} para institución {self.codigo}"
            )
            return True
        except Exception as e:
            logger.error(f"Error al enviar correo de activación a {self.email}: {e}")
            return False

    def aprobar_y_generar_codigo(self):
        with transaction.atomic():
            if self.estatus == "pendiente":
                self.codigo = self.generar_codigo_rnr()
                self.estatus = "aprobado"
                self.activa = True
                self.save()
                self.enviar_correo_activacion()
                return True
        return False

    def save(self, *args, **kwargs):
        campos_a_normalizar = [
            "nombre",
            "direccion",
            "dependencia",
            "particular_nombres",
            "particular_apellidos",
        ]

        for nombre_campo in campos_a_normalizar:
            valor = getattr(self, nombre_campo, None)
            if isinstance(valor, str) and valor.strip():
                nuevo_valor = normalizar_texto_titulo(valor)
                if valor != nuevo_valor:
                    setattr(self, nombre_campo, nuevo_valor)

        if self.codigo_mppe and isinstance(self.codigo_mppe, str):
            self.codigo_mppe = self.codigo_mppe.strip().upper()

        # Generación de Código Temporal para nuevos registros
        if not self.codigo:
            import uuid

            self.codigo = f"TEMP-{uuid.uuid4().hex[:8].upper()}"

        if not self.usuario_id and self.pk:
            UserProfile = apps.get_model("users", "UserProfile")
            perfil = (
                UserProfile.objects.filter(institution=self)
                .select_related("user")
                .first()
            )
            if perfil and perfil.user:
                self.usuario = perfil.user

        super().save(*args, **kwargs)

        if self.activa and self.usuario and self.usuario.username != self.codigo:
            self.usuario.username = self.codigo
            self.usuario.save(update_fields=["username"])

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def nombre_publico(self):
        return self.nombre

    def mostrar_codigo_para(self, user):
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if hasattr(user, "userprofile") and user.userprofile.institution == self:
            return True
        return False
