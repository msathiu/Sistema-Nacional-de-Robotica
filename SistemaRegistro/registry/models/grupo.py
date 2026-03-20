import logging
import string
import uuid6
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

from .base import normalizar_texto_titulo, GRADO_CHOICES
from .institucion import Institucion
from .evento import Evento

logger = logging.getLogger(__name__)

class Grupo(models.Model):
    """Modelo para representar grupos de participantes."""

    ESTADO_CHOICES = [
        ("editable", "Editable"),
        ("inscrito", "Inscrito"),
        ("bloqueado", "Bloqueado"),
    ]

    CRITERIO_CHOICES = [
        ("edad", "Por Edad"),
        ("nivel", "Por Nivel Educativo"),
        ("proyecto", "Por Proyecto"),
    ]
    nombre = models.CharField(
        max_length=150, verbose_name="Nombre del Grupo", db_index=True
    )
    codigo = models.CharField(max_length=20, unique=True, editable=False)
    criterio = models.CharField(max_length=20, choices=CRITERIO_CHOICES)

    edad_desde = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Edad Desde",
        help_text="Edad mínima (solo para criterio 'Por Edad')",
    )
    edad_hasta = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Edad Hasta",
        help_text="Edad máxima (solo para criterio 'Por Edad')",
    )
    nivel_educativo = models.CharField(
        max_length=4,
        choices=GRADO_CHOICES,
        null=True,
        blank=True,
        verbose_name="Nivel Educativo",
        help_text="Grado escolar (solo para criterio 'Por Nivel Educativo')",
    )
    nombre_proyecto = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre del Proyecto",
        help_text="Nombre del proyecto (solo para criterio 'Por Proyecto')",
    )

    estado_grupo = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="editable", db_index=True
    )
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grupos_creados",
    )
    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.PROTECT,
        related_name="grupos_institucion",
        null=True,
        blank=True,
        verbose_name="Institución",
    )

    tutores = models.ManyToManyField(
        "Tutor", related_name="grupos", verbose_name="Tutores asignados"
    )

    participantes = models.ManyToManyField(
        "Participante", related_name="grupos", verbose_name="Integrantes del Grupo"
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grupos_inscritos",
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ["-fecha_registro"]
        indexes = [
            models.Index(fields=["criterio"], name="idx_grupo_criterio"),
            models.Index(fields=["institucion"], name="idx_grupo_institucion"),
        ]
        constraints = [
            UniqueConstraint(
                Lower("nombre"), "evento", name="unique_nombre_evento_case_insensitive"
            )
        ]

    def clean(self):
        super().clean()
        if self.criterio == "edad":
            if not self.edad_desde or not self.edad_hasta:
                raise ValidationError(
                    {
                        "edad_desde": 'Debe especificar edad desde y hasta para criterio "Por Edad"',
                        "edad_hasta": 'Debe especificar edad desde y hasta para criterio "Por Edad"',
                    }
                )
            if self.edad_desde > self.edad_hasta:
                raise ValidationError(
                    {"edad_desde": "La edad desde no puede ser mayor que edad hasta"}
                )
            if self.edad_desde < 4:
                raise ValidationError({"edad_desde": "La edad mínima debe ser 4 años"})
            self.nivel_educativo = None
            self.nombre_proyecto = ""
        elif self.criterio == "nivel":
            if not self.nivel_educativo:
                raise ValidationError(
                    {
                        "nivel_educativo": 'Debe seleccionar un nivel educativo para criterio "Por Nivel Educativo"'
                    }
                )
            self.edad_desde = None
            self.edad_hasta = None
            self.nombre_proyecto = ""
        elif self.criterio == "proyecto":
            if not self.nombre_proyecto or not self.nombre_proyecto.strip():
                raise ValidationError(
                    {
                        "nombre_proyecto": 'Debe ingresar el nombre del proyecto para criterio "Por Proyecto"'
                    }
                )
            self.edad_desde = None
            self.edad_hasta = None
            self.nivel_educativo = None

    def generar_codigo_grupo(self):
        now = timezone.now()
        year = str(now.year)[2:]
        month = str(now.month).zfill(2)
        day = str(now.day).zfill(2)
        prefijo = f"EQP-{day}{month}{year}-"
        chars = string.ascii_uppercase + string.digits
        max_intentos = 100
        for intento in range(max_intentos):
            secuencia = get_random_string(length=8, allowed_chars=chars)
            nuevo_codigo = f"{prefijo}{secuencia}"
            if not Grupo.objects.filter(codigo=nuevo_codigo).exists():
                return nuevo_codigo
        fallback = f"EQP-{day}{month}{year}-{str(uuid6.uuid7())[:8].upper()}"
        logger.warning(
            f"No se pudo generar código de grupo después de {max_intentos} intentos. "
            f"Usando fallback: {fallback}"
        )
        return fallback

    def save(self, *args, **kwargs):
        if self.nombre and isinstance(self.nombre, str):
            self.nombre = normalizar_texto_titulo(self.nombre.strip())
        if self.nombre_proyecto and isinstance(self.nombre_proyecto, str):
            self.nombre_proyecto = normalizar_texto_titulo(self.nombre_proyecto.strip())
        if not self.codigo:
            self.codigo = self.generar_codigo_grupo()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.usuario_creador.username}"
