from datetime import date

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .base import (
    CODIGO_AREA_CHOICES,
    Estado,
    Municipio,
    Parroquia,
    normalizar_texto_titulo,
)
from .institucion import Institucion

# =============================================================================
# MAQUINA DE ESTADOS - PRODUCTION GRADE
# =============================================================================


class EstadoEvento(models.TextChoices):
    """
    Estados definitivos para el flujo de vida de un evento.
    """

    BORRADOR = "borrador", "Borrador"
    REVISION = "revision", "En Revisión"
    ABIERTO = "abierto", "Abierto para Inscripción"
    RECHAZADO = "rechazado", "Rechazado"
    CANCELADO = "cancelado", "Cancelado"
    PAUSADO = "pausado", "Pausado"
    EN_PROCESO = "en_proceso", "En Proceso"
    FINALIZADO = "finalizado", "Finalizado"


# Definición estricta de flujo de estados
TRANSICIONES_VALIDAS = {
    EstadoEvento.BORRADOR: {EstadoEvento.REVISION, EstadoEvento.CANCELADO},
    EstadoEvento.REVISION: {
        EstadoEvento.ABIERTO,
        EstadoEvento.RECHAZADO,
        EstadoEvento.CANCELADO,
    },
    EstadoEvento.ABIERTO: {
        EstadoEvento.PAUSADO,
        EstadoEvento.CANCELADO,
        EstadoEvento.EN_PROCESO,
    },
    EstadoEvento.PAUSADO: {
        EstadoEvento.ABIERTO,
        EstadoEvento.CANCELADO,
    },
    EstadoEvento.RECHAZADO: {
        EstadoEvento.REVISION,
        EstadoEvento.CANCELADO,
    },
    EstadoEvento.EN_PROCESO: {
        EstadoEvento.FINALIZADO,
        EstadoEvento.CANCELADO,
        EstadoEvento.PAUSADO,
    },
    EstadoEvento.CANCELADO: set(),  # Estado terminal
    EstadoEvento.FINALIZADO: set(),  # Estado terminal
}

# Grupos de estados para lógica de negocio
ESTADOS_FINALES = {EstadoEvento.FINALIZADO, EstadoEvento.CANCELADO}
ESTADOS_VIVOS = {EstadoEvento.ABIERTO, EstadoEvento.EN_PROCESO, EstadoEvento.PAUSADO}
ESTADOS_EDITABLES = {EstadoEvento.BORRADOR, EstadoEvento.RECHAZADO}
ESTADOS_INSCRIBIBLES = {EstadoEvento.ABIERTO}


class EventoManager(models.Manager):
    def institucionales(self):
        return self.filter(tipo_evento="institucional")

    def de_club(self):
        return self.filter(tipo_evento="club")

    def pendientes_aprobacion(self):
        return self.filter(estado_evento=EstadoEvento.REVISION)

    def pendientes_aprobacion_todos(self):
        return self.filter(estado_evento=EstadoEvento.REVISION)

    def publicos(self):
        return self.filter(audiencia="publica", estado_evento=EstadoEvento.ABIERTO)

    def exclusivos_club(self):
        return self.filter(
            audiencia="club_exclusivo",
            estado_evento=EstadoEvento.ABIERTO,
        )

    def privados(self):
        return self.filter(
            audiencia="institucional_privado",
            estado_evento=EstadoEvento.ABIERTO,
        )

    def disponibles_para_inscripcion(self):
        return self.filter(
            estado_evento=EstadoEvento.ABIERTO,
            activo=True,
            cancelado=False,
        )

    def de_federacion(self):
        return self.filter(es_publico=True)

    def por_estado(self, estado_evento):
        return self.filter(estado_evento=estado_evento)

    def activos(self):
        return self.filter(activo=True, cancelado=False)

    def vigentes(self):
        return self.filter(activo=True, cancelado=False, fecha__gte=date.today())

    # Nuevos metodos para estados production-grade
    def en_borrador(self):
        return self.filter(estado_evento=EstadoEvento.BORRADOR)

    def en_revision(self):
        return self.filter(estado_evento=EstadoEvento.REVISION)

    def abiertos(self):
        return self.filter(estado_evento=EstadoEvento.ABIERTO)

    def pausados(self):
        return self.filter(estado_evento=EstadoEvento.PAUSADO)

    def en_proceso(self):
        return self.filter(estado_evento=EstadoEvento.EN_PROCESO)

    def finalizados(self):
        return self.filter(estado_evento=EstadoEvento.FINALIZADO)

    def cancelados(self):
        return self.filter(estado_evento=EstadoEvento.CANCELADO)

    def rechazados(self):
        return self.filter(estado_evento=EstadoEvento.RECHAZADO)


class Evento(models.Model):
    TIPO_CHOICES = [
        ("Competencia", "Competencia"),
        ("Taller", "Taller"),
        ("Seminario", "Seminario"),
        ("Conferencia", "Conferencia"),
        ("Exhibición", "Exhibición"),
        ("Hackathon", "Hackathon"),
        ("Feria", "Feria"),
        ("Encuentro", "Encuentro"),
        ("Capacitación", "Capacitación"),
        ("Otro", "Otro"),
    ]

    MODALIDAD_CHOICES = [
        ("presencial", "Presencial"),
        ("virtual", "Virtual"),
        ("hibrido", "Híbrido"),
    ]

    # ESTADO_CHOICES eliminado - ahora usa EstadoEvento.TextChoices

    TIPO_EVENTO_CHOICES = [
        ("institucional", "Evento Institucional"),
        ("club", "Evento de Club"),
    ]

    AUDIENCIA_CHOICES = [
        ("publica", "Pública - Todas las instituciones"),
        ("club_exclusivo", "Exclusivo para miembros del club"),
        ("institucional_privado", "Privado - Solo mi institución"),
    ]

    nombre = models.CharField(max_length=255, db_index=True)
    tipo = models.CharField(
        max_length=100, choices=TIPO_CHOICES, default="Competencia", db_index=True
    )
    categoria = models.CharField(max_length=100, blank=True)
    fecha = models.DateField(db_index=True)
    fecha_hasta = models.DateField(null=True, blank=True, db_index=True)
    descripcion = models.TextField(blank=True)
    modalidad = models.CharField(
        max_length=20, choices=MODALIDAD_CHOICES, default="presencial"
    )
    ubicacion = models.CharField(max_length=255, blank=True)

    # --- Campos de Estado ---
    estado_evento = models.CharField(
        max_length=20,
        choices=EstadoEvento.choices,
        default=EstadoEvento.BORRADOR,
        db_index=True,
    )
    observacion_estado = models.TextField(
        blank=True, default="", help_text="Motivo de pausa, rechazo o cancelación"
    )
    # -----------------------
    estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, blank=True)
    municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    parroquia = models.ForeignKey(
        Parroquia, on_delete=models.SET_NULL, null=True, blank=True
    )
    direccion = models.CharField(max_length=300, blank=True)
    capacidad_maxima = models.PositiveIntegerField(null=True, blank=True)
    requisitos = models.TextField(blank=True)

    telefono_codigo = models.CharField(
        max_length=4,
        choices=CODIGO_AREA_CHOICES,
        blank=True,
        verbose_name="Código de Área",
        help_text="Código de área del teléfono de contacto",
    )
    telefono_numero = models.CharField(
        max_length=7,
        blank=True,
        verbose_name="Número de Teléfono",
        help_text="Número de teléfono de contacto (7 dígitos)",
    )
    email_contacto = models.EmailField(
        blank=True,
        verbose_name="Correo de Contacto",
        help_text="Correo electrónico de contacto del evento",
    )

    tipo_evento = models.CharField(
        max_length=20,
        choices=TIPO_EVENTO_CHOICES,
        default="institucional",
        verbose_name="Tipo de Evento",
    )

    es_publico = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si es True, el evento es público para todas las instituciones. Si es False, requiere aprobación.",
    )

    audiencia = models.CharField(
        max_length=25,
        choices=AUDIENCIA_CHOICES,
        default="publica",
        db_index=True,
        verbose_name="Audiencia del Evento",
        help_text="Define quién puede ver e inscribirse al evento",
    )

    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Para eventos institucionales",
    )
    club_organizador = models.ForeignKey(
        "Club",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="eventos",
        help_text="Para eventos de club",
    )

    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    aprobado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_club_aprobados",
    )
    observaciones_aprobacion = models.TextField(blank=True)

    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="eventos_creados"
    )
    activo = models.BooleanField(default=True, db_index=True)
    cancelado = models.BooleanField(default=False)
    motivo_cancelacion = models.TextField(blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    objects = EventoManager()

    def save(self, *args, **kwargs):
        campos_titulo = ["nombre", "categoria", "ubicacion", "direccion"]
        update_fields = kwargs.get("update_fields")

        if self.fecha and not self.fecha_hasta:
            self.fecha_hasta = self.fecha

        if update_fields is None or any(f in update_fields for f in campos_titulo):
            for campo in campos_titulo:
                valor = getattr(self, campo, None)
                if isinstance(valor, str) and valor.strip():
                    nuevo_valor = normalizar_texto_titulo(valor)
                    if valor != nuevo_valor:
                        setattr(self, campo, nuevo_valor)

            if (
                update_fields is None or "email_contacto" in update_fields
            ) and self.email_contacto:
                self.email_contacto = self.email_contacto.strip().lower()

        if update_fields is not None and "fecha_actualizacion" not in update_fields:
            kwargs["update_fields"] = list(update_fields) + ["fecha_actualizacion"]

        super().save(*args, **kwargs)

    def actualizar_estado_por_fecha(self):
        """
        Actualiza el estado del evento basandose en la fecha.
        Cuando el evento pasa a FINALIZADO, bloquea todos los grupos inscritos.
        """
        hoy = date.today()
        nuevo_estado = None
        fecha_fin = self.fecha_hasta or self.fecha

        if self.estado_evento in ESTADOS_FINALES:
            return

        if (
            self.estado_evento == EstadoEvento.ABIERTO
            and self.fecha <= hoy <= fecha_fin
        ):
            nuevo_estado = EstadoEvento.EN_PROCESO
        elif fecha_fin < hoy and self.estado_evento in [
            EstadoEvento.ABIERTO,
            EstadoEvento.EN_PROCESO,
        ]:
            nuevo_estado = EstadoEvento.FINALIZADO

        if nuevo_estado and self.estado_evento != nuevo_estado:
            self.estado_evento = nuevo_estado
            self.save(update_fields=["estado_evento"])
            # Bloquear grupos inscritos cuando el evento finaliza
            if nuevo_estado == EstadoEvento.FINALIZADO:
                self.grupos_inscritos.filter(
                    estado_grupo__in=["editable", "inscrito"]
                ).update(estado_grupo="bloqueado")

    # =============================================================================
    # METODOS DE DOMINIO - PRODUCTION GRADE
    # =============================================================================

    def puede_transicionar(self, nuevo_estado: str) -> bool:
        """Verifica si se puede transicionar al nuevo estado según la máquina de estados."""
        return nuevo_estado in TRANSICIONES_VALIDAS.get(self.estado_evento, set())

    def obtener_transiciones_permitidas(self):
        """Retorna los estados a los que se puede transicionar desde el estado actual."""
        return TRANSICIONES_VALIDAS.get(self.estado_evento, set())

    def puede_ser_editado(self):
        """Un evento solo es editable en borrador o si fue rechazado."""
        return self.estado_evento in ESTADOS_EDITABLES

    def puede_cancelar(self, usuario):
        """
        Regla:
        - La institución solo puede cancelar eventos creados por ella misma.
        - El ente rector puede cancelar los eventos de cualquier institución.
        """
        if self.estado_evento in ESTADOS_FINALES:
            return False

        perfil = getattr(usuario, "userprofile", None)
        if not perfil:
            return False

        # Ente rector (fed_central, superuser, tecnologico)
        if perfil.user_type in ["fed_central", "superuser", "tecnologico"]:
            return True

        # Institución (solo el suyo)
        if perfil.user_type == "institucional":
            return self.institucion == perfil.institution

        return False

    def puede_pausar(self, usuario):
        """
        Regla: Solo el ente rector puede pausar un evento.
        """
        if self.estado_evento not in [EstadoEvento.ABIERTO, EstadoEvento.EN_PROCESO]:
            return False

        perfil = getattr(usuario, "userprofile", None)
        if not perfil:
            return False

        return perfil.user_type in ["fed_central", "superuser", "tecnologico"]

    def solicitar_revision(self):
        """Envía el evento a revisión por parte del ente rector."""
        if self.puede_transicionar(EstadoEvento.REVISION):
            self.estado_evento = EstadoEvento.REVISION
            self.save(update_fields=["estado_evento"])
            return True
        return False

    def aprobar(self, usuario, observaciones=""):
        """Aprueba el evento y lo abre para inscripciones."""
        if self.puede_transicionar(EstadoEvento.ABIERTO):
            self.estado_evento = EstadoEvento.ABIERTO
            self.aprobado_por = usuario
            self.fecha_aprobacion = timezone.now()
            self.observaciones_aprobacion = observaciones
            # Al aprobar, si es institucional, se hace público para inscripciones
            if self.tipo_evento == "institucional":
                self.es_publico = True
                self.audiencia = "publica"
            self.save()
            return True
        return False

    def rechazar(self, observaciones):
        """Rechaza el evento (vuelve a borrador editable)."""
        if self.puede_transicionar(EstadoEvento.RECHAZADO):
            self.estado_evento = EstadoEvento.RECHAZADO
            self.observacion_estado = observaciones
            self.es_publico = False
            self.save()
            return True
        return False

    def pausar(self, observaciones):
        """Pausa el evento (requiere observación visible)."""
        if self.puede_transicionar(EstadoEvento.PAUSADO):
            self.estado_evento = EstadoEvento.PAUSADO
            self.observacion_estado = observaciones
            self.save()
            return True
        return False

    def cancelar(self, observaciones):
        """Cancela definitivamente el evento."""
        if self.puede_transicionar(EstadoEvento.CANCELADO):
            self.estado_evento = EstadoEvento.CANCELADO
            self.cancelado = True
            self.motivo_cancelacion = observaciones
            self.observacion_estado = observaciones
            self.activo = False
            self.save()
            return True
        return False

    def iniciar(self):
        """Inicia el evento (ABIERTO → EN_PROCESO). Llamado por el comando actualizar_estados_eventos."""
        if self.puede_transicionar(EstadoEvento.EN_PROCESO):
            self.estado_evento = EstadoEvento.EN_PROCESO
            self.save(update_fields=["estado_evento"])
            return True
        return False

    def es_visible_para_todos(self):
        """Evento visible para todos: abierto, en proceso o si es publicacion especial."""
        return (
            self.estado_evento
            in [EstadoEvento.ABIERTO, EstadoEvento.EN_PROCESO, EstadoEvento.PAUSADO]
            and self.es_publico
        )

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha", "activo"], name="idx_evt_fecha_activo"),
            models.Index(fields=["institucion"], name="idx_evt_institucion"),
            models.Index(
                fields=["tipo_evento", "estado_evento"], name="idx_evt_tipo_estado"
            ),
            models.Index(
                fields=["club_organizador", "estado_evento"], name="idx_evt_club_estado"
            ),
            models.Index(
                fields=["audiencia", "estado_evento"], name="idx_evt_audiencia_estado"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(
                        tipo_evento="institucional",
                        es_publico=True,
                        club_organizador__isnull=True,
                    )
                    | models.Q(
                        tipo_evento="institucional",
                        es_publico=False,
                        institucion__isnull=False,
                        club_organizador__isnull=True,
                    )
                    | models.Q(
                        tipo_evento="club",
                        club_organizador__isnull=False,
                        institucion__isnull=True,
                    )
                ),
                name="evento_organizador_valido",
            )
        ]

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"

    @property
    def fecha_fin_efectiva(self):
        return self.fecha_hasta or self.fecha

    @property
    def es_evento_un_dia(self):
        return self.fecha_fin_efectiva == self.fecha

    @property
    def rango_fechas_display(self):
        if not self.fecha:
            return ""
        if self.es_evento_un_dia:
            return self.fecha.strftime("%d/%m/%Y")
        return f"{self.fecha.strftime('%d/%m/%Y')} al {self.fecha_fin_efectiva.strftime('%d/%m/%Y')}"

    def usuario_puede_gestionar(self, perfil):
        if perfil.user_type in ["fed_central", "superuser", "tecnologico"]:
            return True
        if perfil.user_type == "institucional":
            return self.institucion == perfil.institution
        return False

    @property
    def es_editable_por_institucion(self):
        return self.estado_evento in ESTADOS_EDITABLES

    @property
    def es_editable_o_activo(self):
        estados_finales = ["finalizado", "cancelado", "rechazado"]
        return self.estado_evento not in estados_finales

    @property
    def es_evento_club(self):
        return self.tipo_evento == "club"

    @property
    def organizador(self):
        return self.club_organizador if self.es_evento_club else self.institucion

    @property
    def organizador_display(self):
        """
        Nombre visible del organizador para UI.
        Conserva institución o club cuando existan y resuelve el caso histórico
        de eventos institucionales creados por Federación sin institución ligada.
        """
        if self.es_evento_club and self.club_organizador:
            club = self.club_organizador
            tipo_creador = getattr(club, "tipo_creador", None)
            if tipo_creador == "fed_central":
                return "Federación Venezolana de Robótica Creativa"
            if tipo_creador == "fed_regional":
                return "Sede Regional"

            institucion_creadora = getattr(club, "institucion_creadora", None)
            if institucion_creadora:
                return (
                    getattr(institucion_creadora, "nombre_publico", None)
                    or institucion_creadora.nombre
                )
            return club.nombre

        if self.institucion:
            return (
                getattr(self.institucion, "nombre_publico", None)
                or self.institucion.nombre
            )

        if self.creado_por_fed_central:
            return "Federación Venezolana de Robótica Creativa"

        return ""

    @property
    def requiere_aprobacion(self):
        if self.es_publico:
            return False
        return True

    @property
    def creado_por_fed_central(self):
        if self.es_publico:
            return True
        if self.creado_por and hasattr(self.creado_por, "userprofile"):
            return self.creado_por.userprofile.user_type == "fed_central"
        return False

    @property
    def puede_inscribirse(self):
        """Verifica si se puede inscribir al evento."""
        return (
            self.estado_evento == EstadoEvento.ABIERTO
            and self.activo
            and not self.cancelado
        )

    @property
    def es_exclusivo_club(self):
        return self.audiencia == "club_exclusivo"

    @property
    def es_privado(self):
        return self.audiencia == "institucional_privado"

    @property
    def es_publico_audiencia(self):
        return self.audiencia == "publica"

    @property
    def esta_vigente(self):
        return (
            self.activo
            and not self.cancelado
            and self.fecha_fin_efectiva >= date.today()
        )

    @property
    def telefono_completo(self):
        if self.telefono_codigo and self.telefono_numero:
            return f"{self.telefono_codigo}-{self.telefono_numero}"
        return ""

    @property
    def inscripciones_abiertas(self):
        return self.puede_inscribirse and self.fecha >= date.today()

    @property
    def cupos_disponibles(self):
        if not self.capacidad_maxima:
            return float("inf")
        inscritos = self.inscripciones_grupo.filter(activo=True).count()
        return max(0, self.capacidad_maxima - inscritos)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.fecha and not self.fecha_hasta:
            self.fecha_hasta = self.fecha

        if self.fecha and self.fecha_hasta and self.fecha_hasta < self.fecha:
            raise ValidationError(
                {
                    "fecha_hasta": "La fecha hasta no puede ser anterior a la fecha desde."
                }
            )

        # Validar solo si el tipo_evento es explícitamente "institucional" Y hay una institución
        # Los eventos del ente rector (fed_central) pueden tener tipo_evento institucional sin institución
        # si así fueron creados originalmente
        if self.tipo_evento == "institucional" and not self.institucion:
            # Permitir si el evento ya existe y fue creado sin institución (caso de fed_central)
            if (
                self.pk
                and Evento.objects.filter(pk=self.pk, institucion__isnull=True).exists()
            ):
                pass  # Permitir edición sin institución si ya existía así
            else:
                raise ValidationError(
                    "Evento institucional debe tener institución organizadora"
                )
        if self.tipo_evento == "club" and not self.club_organizador:
            raise ValidationError("Evento de club debe tener club organizador")
        if self.institucion and self.club_organizador:
            raise ValidationError("Evento no puede tener ambos organizadores")

    # --- Configuración centralizada de estados para UI ---
    ESTADO_UI_CONFIG = {
        "borrador": {"label": "Borrador", "badge_class": "bg-secondary opacity-75"},
        "revision": {"label": "En revisión", "badge_class": "bg-warning text-dark"},
        "abierto": {"label": "Abierto", "badge_class": "bg-success"},
        "rechazado": {"label": "Rechazado", "badge_class": "bg-danger"},
        "pausado": {"label": "Pausado", "badge_class": "bg-warning"},
        "cancelado": {"label": "Cancelado", "badge_class": "bg-danger"},
        "en_proceso": {"label": "En Proceso", "badge_class": "bg-primary"},
        "finalizado": {"label": "Finalizado", "badge_class": "bg-dark"},
    }

    @property
    def estado_ui(self):
        """Retorna dict con label y badge_class para el estado actual."""
        config = self.ESTADO_UI_CONFIG.get(self.estado_evento, {})
        if self.cancelado:
            return {"label": "Cancelado", "badge_class": "bg-danger"}
        return {
            "label": config.get("label", self.get_estado_evento_display()),
            "badge_class": config.get("badge_class", "bg-secondary"),
        }

    @property
    def estado_badge_html(self):
        """Retorna el HTML completo del badge de estado."""
        ui = self.estado_ui
        return f'<span class="badge {ui["badge_class"]}">{ui["label"]}</span>'

    @property
    def tipo_evento_ui(self):
        """Retorna dict con label, icono y clase CSS para tipo de evento."""
        if self.tipo_evento == "club":
            return {
                "label": "Club",
                "icon": "bi-people",
                "class": "badge-tipo bg-purple",
            }
        # Si es institucional pero creado por federación central
        if self.creado_por and hasattr(self.creado_por, 'userprofile'):
            if self.creado_por.userprofile.user_type in ['fed_central', 'superuser', 'tecnologico']:
                return {
                    "label": "Federativo",
                    "icon": "bi-shield-check",
                    "class": "badge-tipo bg-cyan",
                }
        return {
            "label": "Institucional",
            "icon": "bi-building",
            "class": "badge-tipo bg-blue",
        }

    @property
    def modalidad_ui(self):
        """Retorna dict con label, icono y clase CSS para modalidad."""
        if self.modalidad == "presencial":
            return {
                "label": "Presencial",
                "icon": "bi-geo-alt",
                "class": "badge-tipo-generic bg-success text-white",
            }
        if self.modalidad == "virtual":
            return {
                "label": "Virtual",
                "icon": "bi bi-display",
                "class": "badge-tipo-generic bg-info text-white",
            }
        return {
            "label": "Híbrido",
            "icon": "bi-diagram-3",
            "class": "badge-tipo-generic bg-warning text-dark",
        }


class Inscripcion(models.Model):
    MODALIDAD_CHOICES = (
        ("individual", "Individual"),
        ("equipo", "Equipo"),
    )
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    lider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    nombre_proyecto = models.CharField(max_length=150)
    descripcion_proyecto = models.TextField()
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evento.nombre} - {self.lider.username}"

    def save(self, *args, **kwargs):
        if self.nombre_proyecto and isinstance(self.nombre_proyecto, str):
            original = self.nombre_proyecto
            normalizado = normalizar_texto_titulo(original.strip())
            if original != normalizado:
                self.nombre_proyecto = normalizado
        if self.descripcion_proyecto and isinstance(self.descripcion_proyecto, str):
            self.descripcion_proyecto = self.descripcion_proyecto.strip()
        super().save(*args, **kwargs)


class IntegranteEquipo(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion, related_name="integrantes", on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.usuario.username


class InscripcionGrupoEvento(models.Model):
    ROL_CHOICES = [
        ("participante", "Participante"),
        ("expositor", "Expositor"),
        ("competidor", "Competidor"),
    ]
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="inscripciones_grupo"
    )
    grupo = models.ForeignKey(
        "Grupo", on_delete=models.CASCADE, related_name="inscripciones"
    )
    rol_participacion = models.CharField(
        max_length=20, choices=ROL_CHOICES, default="participante"
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Inscripción Grupo-Evento"
        verbose_name_plural = "Inscripciones Grupo-Evento"
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "grupo"],
                name="unique_inscripcion_evento_grupo",
            )
        ]
        ordering = ["-fecha_inscripcion"]

    def __str__(self):
        return f"{self.grupo.nombre} -> {self.evento.nombre}"

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        if self.evento.es_evento_club:
            institucion_grupo = self.grupo.usuario_creador.userprofile.institution
            es_miembro = self.evento.club_organizador.membresias.filter(
                institucion=institucion_grupo, estado="miembro_activo"
            ).exists()
            if not es_miembro:
                raise ValidationError(
                    f"Solo instituciones miembros del club '{self.evento.club_organizador.nombre}' "
                    "pueden inscribir grupos a este evento."
                )


class ClubEvento(models.Model):
    ROL_CHOICES = [
        ("organizador", "Organizador"),
        ("colaborador", "Colaborador"),
        ("participante", "Participante"),
    ]
    club = models.ForeignKey(
        "Club", on_delete=models.CASCADE, related_name="eventos_vinculados"
    )
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="clubes_vinculados"
    )
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default="participante",
        verbose_name="Rol del Club",
    )
    fecha_vinculacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Club-Evento"
        verbose_name_plural = "Clubes-Eventos"
        constraints = [
            models.UniqueConstraint(
                fields=["club", "evento"],
                name="unique_clubevento_club_evento",
            )
        ]
        ordering = ["-fecha_vinculacion"]
        indexes = [
            models.Index(fields=["evento", "activo"], name="idx_clubevt_evt_act"),
        ]

    def __str__(self):
        return f"{self.club.nombre} → {self.evento.nombre} ({self.rol})"
