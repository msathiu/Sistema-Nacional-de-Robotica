import uuid6
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .base import (
    CODIGO_AREA_CHOICES,
    NACIONALIDAD_CHOICES,
    SEXO_CHOICES,
    normalizar_texto_titulo,
)
from .institucion import Institucion


class Tutor(models.Model):
    """
    Modelo para representar tutores de grupos.
    """

    STATUS_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    id = models.UUIDField(
        default=uuid6.uuid7, editable=False, primary_key=True, verbose_name="ID"
    )
    nacionalidad = models.CharField(
        max_length=1,
        choices=NACIONALIDAD_CHOICES,
        default="V",
        verbose_name="Nacionalidad",
    )
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        default="M",
        verbose_name="Sexo",
    )
    cedula = models.CharField(
        max_length=12,
        db_index=True,
        validators=[
            RegexValidator(
                regex="^[0-9]+$",
                message="La cédula debe contener solo números (sin letras V/E)",
            )
        ],
        verbose_name="Cédula",
        help_text="Ingrese solo números, sin letras (V/E)",
    )
    telefono_codigo = models.CharField(
        max_length=4,
        choices=CODIGO_AREA_CHOICES,
        blank=True,
        verbose_name="Código de Área",
        help_text="Código de área del teléfono de contacto",
    )
    telefono = models.CharField(
        max_length=7,
        blank=True,
        verbose_name="Número de Teléfono",
        help_text="Número de teléfono de contacto (7 dígitos)",
    )
    email = models.EmailField(verbose_name="Correo Electrónico")
    profesion = models.CharField(max_length=100, blank=True, verbose_name="Profesión")
    experiencia = models.TextField(blank=True, verbose_name="Experiencia en Robótica")
    creado_por_federacion = models.BooleanField(
        default=False, verbose_name="Registrado por Federación"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )

    class Meta:
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cedula"], name="idx_tutor_cedula"),
        ]

    def save(self, *args, **kwargs):
        if self.nombres and isinstance(self.nombres, str):
            self.nombres = normalizar_texto_titulo(self.nombres.strip())
        if self.apellidos and isinstance(self.apellidos, str):
            self.apellidos = normalizar_texto_titulo(self.apellidos.strip())
        if self.profesion and isinstance(self.profesion, str):
            self.profesion = normalizar_texto_titulo(self.profesion.strip())
        if self.experiencia and isinstance(self.experiencia, str):
            self.experiencia = self.experiencia.strip()
        if self.email and isinstance(self.email, str):
            self.email = self.email.strip().lower()
        if self.telefono and isinstance(self.telefono, str):
            self.telefono = self.telefono.strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.get_nombre_completo()} ({self.cedula})"

    def get_nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    def get_telefono_completo(self) -> str:
        if self.telefono_codigo and self.telefono:
            return f"({self.telefono_codigo}) {self.telefono}"
        elif self.telefono:
            return self.telefono
        return ""

    def get_instituciones_activas(self):
        return Institucion.objects.filter(
            tutores_vinculados__tutor=self, tutores_vinculados__status="activo"
        ).distinct()

    def esta_vinculado_a(self, institucion):
        return TutorInstitucion.objects.filter(
            tutor=self, institucion=institucion, status="activo"
        ).exists()

    @property
    def nombre_formateado(self) -> str:
        return f"{self.apellidos}, {self.nombres}"


class TutorInstitucion(models.Model):
    ROL_CHOICES = [
        ("asistente", "Asistente"),
        ("entrenador", "Entrenador"),
        ("instructor", "Instructor/Monitor"),
        ("coordinador", "Coordinador"),
        ("delegado", "Delegado"),
        ("representante", "Representante"),
        ("colaborador", "Colaborador"),
    ]

    STATUS_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("suspendido", "Suspendido"),
    ]

    TIPO_VINCULACION_CHOICES = [
        ("institucional", "Institucional (Sede Educativa/Club)"),
        ("regional", "Sede Regional (Federación Estado)"),
        ("central", "Sede Central (Federación Nacional)"),
    ]

    id = models.UUIDField(default=uuid6.uuid7, primary_key=True, editable=False)
    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE,
        related_name="vinculaciones",
        verbose_name="Tutor",
    )
    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE,
        related_name="tutores_vinculados",
        verbose_name="Institución",
        null=True,
        blank=True,
    )
    estado = models.ForeignKey(
        "Estado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Estado/Sede Regional",
        help_text="Solo requerido para vinculaciones de sede regional.",
    )
    tipo_vinculacion = models.CharField(
        max_length=20,
        choices=TIPO_VINCULACION_CHOICES,
        default="institucional",
        verbose_name="Tipo de Vinculación",
    )
    rol = models.CharField(
        max_length=20, choices=ROL_CHOICES, default="colaborador", verbose_name="Rol"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="activo",
        db_index=True,
        verbose_name="Estado",
    )
    fecha_vinculacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Vinculación"
    )
    fecha_desvinculacion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Desvinculación"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Vinculación Tutor-Institución"
        verbose_name_plural = "Vinculaciones Tutor-Institución"
        ordering = ["-fecha_vinculacion"]
        indexes = [
            models.Index(fields=["tutor", "status"], name="idx_tutinst_tutor_st"),
            models.Index(fields=["institucion", "status"], name="idx_tutinst_inst_st"),
            models.Index(
                fields=["status", "-fecha_vinculacion"], name="idx_tutinst_st_fecha"
            ),
        ]
        constraints = [
            # 1. Unicidad para Instituciones (Tutor + Institución)
            models.UniqueConstraint(
                fields=["tutor", "institucion"],
                condition=models.Q(tipo_vinculacion="institucional"),
                name="unique_tutor_institucion",
            ),
            # 2. Unicidad para Sedes Regionales (Tutor + Estado)
            models.UniqueConstraint(
                fields=["tutor", "estado"],
                condition=models.Q(tipo_vinculacion="regional"),
                name="unique_tutor_regional",
            ),
            # 3. Unicidad para Sede Central (Un solo registro Central por Tutor)
            models.UniqueConstraint(
                fields=["tutor"],
                condition=models.Q(tipo_vinculacion="central"),
                name="unique_tutor_central",
            ),
        ]

    def __str__(self):
        return f"{self.tutor.get_nombre_completo()} @ {self.institucion.nombre} ({self.get_status_display()})"

    def desvincular(self):
        self.status = "inactivo"
        self.fecha_desvinculacion = timezone.now()
        self.save(update_fields=["status", "fecha_desvinculacion"])
