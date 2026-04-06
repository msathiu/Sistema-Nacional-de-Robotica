from datetime import date

import uuid6
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from .base import (
    CODIGO_AREA_CHOICES,
    GRADO_CHOICES,
    NACIONALIDAD_CHOICES,
    NUMERO_VALIDATOR,
    SEXO_CHOICES,
    Estado,
    Municipio,
    Parroquia,
    normalizar_texto_titulo,
)
from .institucion import Institucion


class Participante(models.Model):
    """
    Modelo para datos personales del participante (ÚNICOS).
    """

    id = models.UUIDField(default=uuid6.uuid7, primary_key=True, editable=False)
    nacionalidad = models.CharField(
        max_length=1,
        choices=NACIONALIDAD_CHOICES,
        default="V",
        verbose_name="Nacionalidad",
    )
    cedula = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]+$", message="Cédula debe contener solo números"
            )
        ],
        help_text="Solo números (ej: 19122516)",
    )
    cedula_escolar = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        verbose_name="Cédula Escolar",
        help_text="Cédula escolar del participante (solo números)",
        validators=[
            RegexValidator(
                regex="^[0-9]*$", message="La cédula escolar debe contener solo números"
            )
        ],
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    email = models.EmailField()

    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    parroquia = models.ForeignKey(
        Parroquia,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Parroquia",
    )
    direccion = models.TextField()

    codigo_area = models.CharField(
        max_length=4,
        choices=CODIGO_AREA_CHOICES,
        default="0424",
        verbose_name="Código de Área",
    )
    numero_telefono = models.CharField(
        max_length=7, validators=[NUMERO_VALIDATOR], verbose_name="Número (7 dígitos)"
    )

    grado_escolar = models.CharField(
        max_length=4,
        choices=GRADO_CHOICES,
        default="NO",
        verbose_name="Nivel Educativo/Grado",
    )
    titulo_universitario = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Título/Estudios Universitarios",
        help_text="Especificar título o estudios universitarios (solo si selecciona Estudios Universitarios)",
    )
    campo1 = models.TextField(
        blank=True,
        verbose_name="Campo Adicional",
        help_text="Campo adicional para guardar grado/nivel cuando se selecciona 'Otro/No especificado'",
    )

    nombre_representante = models.CharField(max_length=200, blank=True)
    nacionalidad_representante = models.CharField(
        max_length=1,
        choices=NACIONALIDAD_CHOICES,
        default="V",
        verbose_name="Nacionalidad Representante",
    )
    cedula_representante = models.CharField(
        max_length=10,
        blank=True,
        validators=[
            RegexValidator(
                r"^\d{7,10}$",
                "La cédula del representante debe tener entre 7 y 10 números.",
            )
        ],
        verbose_name="Cédula Representante",
    )
    codigo_area_representante = models.CharField(
        max_length=4,
        choices=CODIGO_AREA_CHOICES,
        blank=True,
        verbose_name="Cód. Área Rep.",
    )
    numero_telefono_representante = models.CharField(
        max_length=7,
        validators=[NUMERO_VALIDATOR],
        blank=True,
        verbose_name="Número Rep. (7 dígitos)",
    )
    email_representante = models.EmailField(blank=True)

    condicion_tea = models.BooleanField(
        default=False,
        verbose_name="Condición TEA",
        help_text="Indica si el participante posee condición en el espectro autista",
    )
    creado_por_federacion = models.BooleanField(
        default=False, verbose_name="Registrado por Federación"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        ordering = ["apellidos", "nombres"]
        indexes = [
            models.Index(fields=["cedula"], name="idx_part_cedula"),
            models.Index(fields=["cedula_escolar"], name="idx_part_cedula_esc"),
            models.Index(fields=["email"], name="idx_part_email"),
            models.Index(fields=["apellidos", "nombres"], name="idx_part_nombre"),
            models.Index(
                fields=["nombres", "apellidos", "fecha_nacimiento"],
                name="idx_part_nombre_fn",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["nombres", "apellidos", "fecha_nacimiento"],
                name="unique_participante_datos_personales",
                violation_error_message="Ya existe un participante con estos nombres, apellidos y fecha de nacimiento.",
            ),
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.cedula}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def edad(self):
        today = date.today()
        return (
            today.year
            - self.fecha_nacimiento.year
            - (
                (today.month, today.day)
                < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        )

    @property
    def telefono_completo(self):
        return f"{self.codigo_area}-{self.numero_telefono}"

    @property
    def telefono_representante_completo(self):
        if self.codigo_area_representante and self.numero_telefono_representante:
            return (
                f"{self.codigo_area_representante}-{self.numero_telefono_representante}"
            )
        return ""

    @property
    def cedula_completa(self):
        return f"{self.nacionalidad}-{self.cedula}"

    def get_instituciones_activas(self):
        return Institucion.objects.filter(
            participantes_vinculados__participante=self,
            participantes_vinculados__status="activo",
        ).distinct()

    def esta_vinculado_a(self, institucion):
        return ParticipanteInstitucion.objects.filter(
            participante=self, institucion=institucion, status="activo"
        ).exists()

    def clean(self):
        super().clean()
        if self.fecha_nacimiento:
            edad_calculada = self.edad
            if edad_calculada < 4:
                raise ValidationError(
                    {
                        "fecha_nacimiento": "El participante debe tener al menos 4 años para registrarse."
                    }
                )
            if edad_calculada < 18:
                errores = {}
                if not self.nombre_representante:
                    errores["nombre_representante"] = (
                        "El nombre del representante es obligatorio para menores de 18 años."
                    )
                if not self.cedula_representante:
                    errores["cedula_representante"] = (
                        "La cédula del representante es obligatoria para menores de 18 años."
                    )
                if not self.numero_telefono_representante:
                    errores["numero_telefono_representante"] = (
                        "El teléfono del representante es obligatorio para menores de 18 años."
                    )
                if errores:
                    raise ValidationError(errores)

    def save(self, *args, **kwargs):
        campos_titulo = [
            "nombres",
            "apellidos",
            "direccion",
            "titulo_universitario",
            "campo1",
            "nombre_representante",
        ]
        for campo in campos_titulo:
            valor = getattr(self, campo, None)
            if isinstance(valor, str) and valor.strip():
                nuevo_valor = normalizar_texto_titulo(valor)
                if valor != nuevo_valor:
                    setattr(self, campo, nuevo_valor)
        super().save(*args, **kwargs)


class ParticipanteInstitucion(models.Model):
    STATUS_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("suspendido", "Suspendido"),
        ("egresado", "Egresado"),
    ]

    TIPO_VINCULACION_CHOICES = [
        ("institucional", "Institucional (Sede Educativa/Club)"),
        ("regional", "Sede Regional (Federación Estado)"),
        ("central", "Sede Central (Federación Nacional)"),
    ]

    id = models.UUIDField(default=uuid6.uuid7, primary_key=True, editable=False)
    participante = models.ForeignKey(
        Participante,
        on_delete=models.CASCADE,
        related_name="vinculaciones",
        verbose_name="Participante",
    )
    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE,
        related_name="participantes_vinculados",
        verbose_name="Institución",
        null=True,
        blank=True,
    )
    estado = models.ForeignKey(
        Estado,
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
    grupo_actual = models.ForeignKey(
        "Grupo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participantes_actuales",
        verbose_name="Grupo Actual",
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
    registrado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participantes_registrados",
        verbose_name="Registrado Por",
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Vinculación Participante-Institución"
        verbose_name_plural = "Vinculaciones Participante-Institución"
        ordering = ["-fecha_vinculacion"]
        indexes = [
            models.Index(
                fields=["participante", "status"], name="idx_partinst_part_st"
            ),
            models.Index(fields=["institucion", "status"], name="idx_partinst_inst_st"),
            models.Index(
                fields=["status", "-fecha_vinculacion"], name="idx_partinst_st_fecha"
            ),
            models.Index(fields=["grupo_actual"], name="idx_partinst_grupo"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["participante", "institucion"],
                condition=models.Q(tipo_vinculacion="institucional"),
                name="unique_participante_institucion",
            ),
            models.UniqueConstraint(
                fields=["participante", "estado"],
                condition=models.Q(tipo_vinculacion="regional"),
                name="unique_participante_regional",
            ),
            models.UniqueConstraint(
                fields=["participante"],
                condition=models.Q(tipo_vinculacion="central"),
                name="unique_participante_central",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.grupo_actual
            and self.institucion
            and self.grupo_actual.institucion != self.institucion
        ):
            raise ValidationError(
                {
                    "grupo_actual": f"El grupo debe pertenecer a la institución {self.institucion.nombre}"
                }
            )


class ParticipanteGrupo(models.Model):
    id = models.UUIDField(default=uuid6.uuid7, primary_key=True, editable=False)
    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE, related_name="historial_grupos"
    )
    grupo = models.ForeignKey(
        "Grupo", on_delete=models.CASCADE, related_name="historial_participantes"
    )
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Participante-Grupo"
        verbose_name_plural = "Participantes-Grupos"
        constraints = [
            models.UniqueConstraint(
                fields=["participante", "grupo"],
                name="unique_participante_grupo",
            )
        ]
        ordering = ["-fecha_ingreso"]
        indexes = [
            models.Index(
                fields=["participante", "activo"], name="idx_partgrp_part_act"
            ),
            models.Index(fields=["grupo", "activo"], name="idx_partgrp_grp_act"),
        ]

    def __str__(self):
        return f"{self.participante.nombre_completo} → {self.grupo.nombre}"


class AsistenciaEvento(models.Model):
    ASISTENCIA_CHOICES = [
        ("asistio", "Asistió"),
        ("ausente", "Ausente"),
        ("pendiente", "Pendiente"),
        ("justificado", "Justificado"),
    ]

    evento = models.ForeignKey(
        "Evento", on_delete=models.CASCADE, related_name="asistencias"
    )
    participante = models.ForeignKey(
        "Participante", on_delete=models.CASCADE, related_name="asistencias"
    )
    grupo = models.ForeignKey(
        "Grupo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asistencias",
    )
    asistencia = models.CharField(
        max_length=12, choices=ASISTENCIA_CHOICES, default="pendiente", db_index=True
    )
    observacion = models.TextField(blank=True)
    fecha_asistencia = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que se marcó la asistencia."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asistencia a Evento"
        verbose_name_plural = "Asistencias a Eventos"
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "participante"],
                name="unique_asistenciaevento_evento_participante",
            )
        ]
        ordering = ["-evento__fecha", "participante__apellidos"]

    def __str__(self):
        return (
            f"Asistencia de {self.participante.nombre_completo} a {self.evento.nombre}"
        )
