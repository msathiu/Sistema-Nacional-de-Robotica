from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg
from django.utils import timezone

from .base import normalizar_texto_titulo
from .institucion import Institucion
from .investigacion import LineaInvestigacion
from .tutor import Tutor


class Club(models.Model):
    ESTADO_VINCULACION_CHOICES = [
        ("abierto", "Abierto"),
        ("cerrado", "Cerrado"),
        ("invitacion", "Bajo Invitación"),
    ]

    STATUS_CHOICES = [
        ("borrador", "Borrador"),
        ("pendiente", "Pendiente de Revisión"),
        ("en_revision", "En Revisión"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    ]

    TIPO_CREADOR_CHOICES = [
        ("institucion", "Institución"),
        ("fed_central", "Federación Central"),
        ("fed_regional", "Sede Regional"),
    ]

    nombre = models.CharField(
        max_length=200, verbose_name="Nombre del Club", db_index=True
    )
    logo = models.ImageField(upload_to="clubes/logos/", blank=True, null=True)
    siglas = models.CharField(max_length=10, blank=True)
    descripcion = models.TextField(verbose_name="Descripción")
    ubicacion = models.CharField(max_length=255, verbose_name="Ubicación")
    fecha_fundacion = models.DateField(null=True, blank=True)

    institucion_creadora = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE,
        related_name="clubes_creados",
        null=True,
        blank=True,
    )

    tipo_creador = models.CharField(
        max_length=20,
        choices=TIPO_CREADOR_CHOICES,
        default="institucion",
        verbose_name="Tipo de Creador",
        help_text="Indica si el club fue creado por una institución, federación central o sede regional",
    )

    coordinador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="clubes_coordinados",
        null=True,
        blank=True,
        verbose_name="Coordinador del Club",
    )

    documento_legal = models.CharField(
        max_length=255, blank=True, verbose_name="Documento Legal / Aval Institucional"
    )

    estado_vinculacion = models.CharField(
        max_length=20, choices=ESTADO_VINCULACION_CHOICES, default="abierto"
    )
    cupo_maximo = models.IntegerField(
        default=10, verbose_name="Cupo máximo de instituciones"
    )
    requisitos = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="borrador",
        verbose_name="Estado del Club",
        db_index=True,
    )

    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True, db_index=True)

    eliminado = models.BooleanField(default=False, db_index=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    motivo_eliminacion = models.TextField(blank=True)
    eliminado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clubes_eliminados",
    )

    class Meta:
        verbose_name = "Club"
        verbose_name_plural = "Clubes"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["activo", "status"], name="idx_club_activo_status"),
            models.Index(fields=["status", "nombre"], name="idx_club_status_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        campos_titulo = ["nombre", "ubicacion", "documento_legal"]
        update_fields = kwargs.get("update_fields")

        if update_fields is None or any(f in update_fields for f in campos_titulo):
            for campo in campos_titulo:
                valor = getattr(self, campo, None)
                if isinstance(valor, str) and valor.strip():
                    nuevo_valor = normalizar_texto_titulo(valor.strip())
                    if valor != nuevo_valor:
                        setattr(self, campo, nuevo_valor)

        if self.cupo_maximo and self.pk:
            miembros_actuales = self.membresias.filter(estado="miembro_activo").count()
            cupos = max(0, self.cupo_maximo - miembros_actuales)
            if cupos == 0 and self.estado_vinculacion == "abierto":
                self.estado_vinculacion = "cerrado"

        super().save(*args, **kwargs)

    @property
    def lineas_investigacion(self):
        if self.pk:
            lineas_nm = (
                self.club_lineas.select_related("linea")
                .filter(linea__activa=True)
                .order_by("orden")
                .values_list("linea__nombre", flat=True)
            )
            lineas = list(lineas_nm)
            if lineas:
                return lineas
        return ["Sin líneas asignadas"]

    @property
    def cupos_disponibles(self):
        if not self.pk:
            return self.cupo_maximo
        miembros_actuales = self.membresias.filter(estado="miembro_activo").count()
        return max(0, self.cupo_maximo - miembros_actuales)

    @property
    def puede_postularse(self):
        return (
            self.activo
            and self.status == "aprobado"
            and self.estado_vinculacion == "abierto"
            and self.cupos_disponibles > 0
        )

    def enviar_a_revision(self):
        if self.status == "borrador":
            self.status = "pendiente"
            self.save(update_fields=["status"])
            return True
        return False

    def aprobar(self):
        self.status = "aprobado"
        self.fecha_aprobacion = timezone.now()
        self.save(update_fields=["status", "fecha_aprobacion"])
        return True

    def rechazar(self, observaciones=""):
        self.status = "rechazado"
        self.save(update_fields=["status"])
        return True

    def puede_editar(self, user):
        if not hasattr(user, "userprofile"):
            return False
        user_type = user.userprofile.user_type
        if user_type in ["fed_central", "superuser"]:
            return True
        if self.coordinador == user:
            return True
        if self.institucion_creadora and user_type == "institucional":
            if user.userprofile.institution == self.institucion_creadora:
                return True
        return False

    def responsables(self):
        return self.tutores.filter(rol="responsable", status="activo")

    def contar_reenvios(self):
        return self.historial.filter(
            estado_anterior="rechazado", estado_nuevo="pendiente"
        ).count()

    def obtener_ultimo_rechazo(self):
        return (
            self.historial.filter(estado_nuevo="rechazado").order_by("-fecha").first()
        )

    @property
    def promedio_calificacion(self):
        resultado = self.calificaciones.aggregate(promedio=Avg("puntuacion"))
        return resultado["promedio"] or 0

    @property
    def total_calificaciones(self):
        return self.calificaciones.count()

    @property
    def tiene_calificaciones(self):
        return self.calificaciones.exists()

    @property
    def calificaciones_recientes(self):
        return self.calificaciones.select_related("institucion").order_by("-fecha")[:5]

    def mi_calificacion(self, institucion):
        return self.calificaciones.filter(institucion=institucion).first()

    @property
    def solicitudes_pendientes_rector(self):
        """Cantidad de solicitudes de membresía pendientes de aprobación por el ente rector (fed_central)."""
        if not self.pk:
            return 0
        from django.db.models import Q
        return self.membresias.filter(
            Q(estado="visto_bueno_fundadora") |
            Q(estado="pendiente_filtro", club__institucion_creadora__isnull=True)
        ).count()


class MembresiaClu(models.Model):
    ESTADO_CHOICES = [
        ("pendiente_filtro", "Pendiente de Filtro (Fundadora)"),
        ("visto_bueno_fundadora", "Visto Bueno Fundadora"),
        ("miembro_activo", "Miembro Activo"),
        ("rechazada", "Rechazada"),
    ]

    TIPO_LINEA_CHOICES = [
        ("soporte", "Soporte"),
        ("afines", "Afines"),
        ("vinculantes", "Vinculantes"),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="membresias")
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    carta_intencion = models.TextField()
    propuesta_tecnica = models.TextField()
    representante_legal = models.CharField(max_length=200)
    representante_tutor = models.ForeignKey(
        "registry.Tutor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membresias_representadas",
        verbose_name="Representante Legal (Tutor)",
    )

    tipo_linea = models.CharField(
        max_length=20,
        choices=TIPO_LINEA_CHOICES,
        default="soporte",
        verbose_name="Tipo de Línea de Investigación",
    )

    estado = models.CharField(
        max_length=25, choices=ESTADO_CHOICES, default="pendiente_filtro", db_index=True
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    visto_bueno_fundadora = models.BooleanField(
        default=False, verbose_name="Visto Bueno Fundadora"
    )
    visto_bueno_fundadora_por = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="membresias_visto_bueno",
        verbose_name="Visto bueno dado por",
    )
    visto_bueno_fundadora_fecha = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha visto bueno"
    )
    observaciones_fundadora = models.TextField(
        blank=True, verbose_name="Observaciones de la Fundadora"
    )

    aprobacion_ente_rector = models.BooleanField(
        default=False, verbose_name="Aprobación Ente Rector"
    )
    aprobacion_ente_rector_por = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="membresias_aprobadas_rector",
        verbose_name="Aprobado por (Ente Rector)",
    )
    aprobacion_ente_rector_fecha = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha aprobación Ente Rector"
    )
    observaciones_rector = models.TextField(
        blank=True, verbose_name="Observaciones del Ente Rector"
    )

    class Meta:
        verbose_name = "Membresía de Club"
        verbose_name_plural = "Membresías de Clubes"
        ordering = ["-fecha_solicitud"]
        indexes = [
            models.Index(
                fields=["club", "institucion"],
                name="idx_memb_club_inst_active",
                condition=models.Q(
                    estado__in=["pendiente_filtro", "visto_bueno_fundadora"]
                ),
            ),
        ]

    def __str__(self):
        return f"{self.institucion.nombre} -> {self.club.nombre} ({self.estado})"


class SolicitudEliminacionClub(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
    ]

    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="solicitudes_eliminacion"
    )
    institucion_solicitante = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    motivo = models.TextField(verbose_name="Motivo de la solicitud")
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="pendiente", db_index=True
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    observaciones_federacion = models.TextField(blank=True)
    revisado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_eliminacion_revisadas",
    )

    class Meta:
        verbose_name = "Solicitud de Eliminación de Club"
        verbose_name_plural = "Solicitudes de Eliminación de Clubes"
        ordering = ["-fecha_solicitud"]
        indexes = [
            models.Index(
                fields=["estado", "fecha_solicitud"], name="idx_sol_elim_estado"
            ),
        ]

    def __str__(self):
        return f"Solicitud eliminación: {self.club.nombre} ({self.estado})"


class HistorialClub(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="historial")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    observaciones = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Historial de Club"
        verbose_name_plural = "Historiales de Clubes"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["club", "-fecha"], name="idx_hist_club_fecha"),
        ]

    def __str__(self):
        return f"{self.club.nombre}: {self.estado_anterior} → {self.estado_nuevo}"


class ComentarioClub(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="comentarios")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField()
    es_federacion = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Comentario de Club"
        verbose_name_plural = "Comentarios de Clubes"
        ordering = ["fecha"]
        indexes = [
            models.Index(fields=["club", "fecha"], name="idx_com_club_fecha"),
        ]

    def __str__(self):
        return f"Comentario en {self.club.nombre} por {self.usuario.username}"


class CalificacionClub(models.Model):
    PUNTUACION_CHOICES = [
        (1, "1 - Muy Malo"),
        (2, "2 - Malo"),
        (3, "3 - Regular"),
        (4, "4 - Bueno"),
        (5, "5 - Excelente"),
    ]

    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="calificaciones"
    )
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    puntuacion = models.IntegerField(
        choices=PUNTUACION_CHOICES, verbose_name="Puntuación"
    )
    resena = models.TextField(blank=True, verbose_name="Reseña")
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Calificación de Club"
        verbose_name_plural = "Calificaciones de Clubes"
        constraints = [
            models.UniqueConstraint(
                fields=["club", "institucion"],
                name="unique_calificacion_club_institucion",
            )
        ]
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["club", "-fecha"], name="idx_calif_club_fecha"),
        ]

    def __str__(self):
        return f"{self.club.nombre} - {self.puntuacion}★ por {self.institucion.nombre}"


class ClubLineaInvestigacion(models.Model):
    TIPO_LINEA_CHOICES = [
        ("principal", "Principal"),
        ("soporte", "Soporte"),
        ("afines", "Afines"),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="club_lineas")
    linea = models.ForeignKey(
        LineaInvestigacion, on_delete=models.PROTECT, related_name="clubes"
    )
    tipo_linea = models.CharField(
        max_length=20,
        choices=TIPO_LINEA_CHOICES,
        default="principal",
        verbose_name="Tipo de Línea",
    )
    orden = models.IntegerField(default=0, verbose_name="Orden")
    fecha_vinculacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Club-Línea de Investigación"
        verbose_name_plural = "Clubes-Líneas de Investigación"
        constraints = [
            models.UniqueConstraint(
                fields=["club", "linea"],
                name="unique_clublinea_club_linea",
            )
        ]
        ordering = ["orden"]
        indexes = [
            models.Index(fields=["club", "orden"], name="idx_clublinea_club_orden"),
        ]

    def __str__(self):
        return f"{self.club.nombre} - {self.linea.nombre} ({self.tipo_linea})"


class ClubTutor(models.Model):
    ROL_CHOICES = [
        ("responsable", "Responsable del Club"),
        ("coordinador", "Coordinador"),
        ("entrenador", "Entrenador"),
        ("instructor", "Instructor"),
        ("colaborador", "Colaborador"),
        ("representante", "Representante"),
        ("director", "Director Ejecutivo"),
        ("delegado", "Delegado"),
        ("asistente", "Asistente"),
        ("logistico", "Logística"),
    ]
    STATUS_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="tutores")
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="clubes")
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="activo")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["club", "tutor"],
                name="unique_club_tutor",
            )
        ]
