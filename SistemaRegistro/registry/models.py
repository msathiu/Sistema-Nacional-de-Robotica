import logging
import random
import string
import uuid
from datetime import date

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class Estado(models.Model):
    """Modelo para representar los estados de Venezuela."""

    nombre = models.CharField(max_length=100, unique=True, db_index=True)
    codigo = models.CharField(max_length=10, unique=True, db_index=True)

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"], name="idx_estado_nombre"),
            models.Index(fields=["codigo"], name="idx_estado_codigo"),
        ]

    def __str__(self):
        return self.nombre


class LineaInvestigacion(models.Model):
    """Catálogo dinámico de líneas de investigación gestionado por el Ente Rector."""
    
    codigo = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, db_index=True, verbose_name="Activa")
    orden = models.IntegerField(default=0, verbose_name="Orden de visualización")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Línea de Investigación"
        verbose_name_plural = "Líneas de Investigación"
        ordering = ['orden', 'nombre']
        indexes = [
            models.Index(fields=['activa', 'orden'], name='idx_linea_activa_orden'),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Municipio(models.Model):
    """Modelo para representar los municipios de Venezuela."""

    estado = models.ForeignKey(
        Estado,
        on_delete=models.PROTECT,
        related_name="municipios",
    )
    nombre = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        unique_together = ["estado", "nombre"]
        ordering = ["estado", "nombre"]
        indexes = [
            models.Index(fields=["estado", "nombre"], name="idx_mun_estado_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.estado.nombre})"


class Parroquia(models.Model):
    """Modelo para representar las parroquias de Venezuela."""

    municipio = models.ForeignKey(
        Municipio, on_delete=models.PROTECT, related_name="parroquias"
    )
    nombre = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "Parroquia"
        verbose_name_plural = "Parroquias"
        unique_together = ["municipio", "nombre"]
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["municipio", "nombre"], name="idx_parr_mun_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} (Mun. {self.municipio.nombre})"


class Dependencia(models.Model):
    """Modelo para representar las dependencias gubernamentales."""

    nombre = models.CharField(max_length=255, unique=True, db_index=True)
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Dependencia"
        verbose_name_plural = "Dependencias"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["activa", "nombre"], name="idx_dep_activa_nombre"),
        ]

    def __str__(self):
        return self.nombre


def generar_codigo_unico():
    """
    Genera un código aleatorio de 8 caracteres alfanuméricos.

    Returns:
        str: Código único de 8 caracteres en mayúsculas.
    """
    caracteres = string.ascii_uppercase + string.digits
    max_intentos = 100
    for _ in range(max_intentos):
        codigo = "".join(random.choices(caracteres, k=8))
        if not Institucion.objects.filter(codigo=codigo).exists():
            return codigo
    raise ValueError("No se pudo generar un código único después de múltiples intentos")


class Institucion(models.Model):
    ESTATUS_CHOICES = [
        ("pendiente", "Pendiente"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    ]

    TIPO_INSTITUCION_CHOICES = [
        ("educativa", "Institucion educativa (Adscrita a MPPE)"),
        ("publica", "Publica"),
        ("privada", "Privada"),
        ("otra", "Otras Instituciones"),
        ("particular", "Particular (Persona Natural)"),
    ]

    NATURALEZA_CHOICES = [
        ("publica", "Publica"),
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
    rif = models.CharField(
        max_length=20, null=True, blank=True
    )  # Agregamos null=True y blank=True
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
        default="institucion",  # Al darle un default, evitamos el error de NotNull
    )
    federado = models.BooleanField(default=False, verbose_name="Federado")
    categoria = models.CharField(max_length=50, null=True, blank=True)
    institucion_procedencia = models.CharField(max_length=120, null=True, blank=True)
    codigo_mppe = models.CharField(max_length=30, null=True, blank=True)
    estado = models.ForeignKey("Estado", on_delete=models.PROTECT)
    municipio = models.ForeignKey("Municipio", on_delete=models.PROTECT)
    parroquia = models.ForeignKey("Parroquia", on_delete=models.PROTECT)
    codigo = models.CharField(max_length=35, unique=True, editable=False)
    direccion = models.TextField(blank=True)
    telefono_codigo = models.CharField(max_length=4, null=True, blank=True)
    telefono_numero = models.CharField(max_length=7, null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estatus = models.CharField(
        max_length=20, choices=ESTATUS_CHOICES, default="pendiente"
    )
    activa = models.BooleanField(default=False)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    dependencia = models.CharField(max_length=255, null=True, blank=True)
    dependencia_rel = models.ForeignKey(
        "Dependencia", on_delete=models.SET_NULL, null=True, blank=True
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
        ]

    def generar_codigo_rnr(self):
        """
        Genera el código único con formato RNR[YY]-[EEEMMMPPP]-[8CHARS].

        Formato:
            - RNR: Prefijo del Registro Nacional de Robótica
            - YY: Últimos 2 dígitos del año actual
            - EEE: ID del estado (3 dígitos)
            - MMM: ID del municipio (3 dígitos)
            - PPP: ID de la parroquia (3 dígitos)
            - 8CHARS: Secuencia aleatoria alfanumérica

        Returns:
            str: Código único generado.

        Raises:
            ValueError: Si no se puede generar un código único después de múltiples intentos.
        """
        year = str(timezone.now().year)[2:]

        # Formateo de IDs de ubicación con ceros a la izquierda
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
        """
        Envía un correo electrónico al usuario cuando su cuenta es activada.

        El correo incluye:
            - Código RNR generado
            - Instrucciones de acceso
            - URL de login

        Returns:
            bool: True si el correo se envió exitosamente, False en caso contrario.
        """
        try:
            # Preparar contexto para el template
            context = {
                "site_name": settings.SITE_NAME,
                "nombre_institucion": self.nombre,
                "codigo": self.codigo,
                "usuario": self.codigo,  # El usuario es el código RNR
                "login_url": f"{settings.BASE_URL}/login/",
            }

            # Renderizar template HTML
            html_message = render_to_string("emails/aprobacion.html", context)
            plain_message = strip_tags(html_message)

            # Enviar correo
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
        """
        Método profesional para activar la cuenta.
        Se debe llamar desde el Admin o una vista de revisión.
        """
        if self.estatus == "pendiente":
            self.codigo = self.generar_codigo_rnr()
            self.estatus = "aprobado"
            self.activa = True
            self.save()
            # Enviar correo de activación
            self.enviar_correo_activacion()
            return True
        return False

    def save(self, *args, **kwargs):
        """
        Guarda la institución y gestiona el ciclo de vida del código.

        Flujo de códigos:
            1. Registro inicial: Se asigna código temporal TEMP-XXXXXXXX
            2. Activación: Se genera código permanente RNR[YY]-[EEEMMMPPP]-[8CHARS]
            3. Login: El usuario usa el código RNR como username

        Proceso:
            1. Si se activa la institución, genera código RNR permanente
            2. Vincula el usuario con la institución si existe
            3. Guarda la institución
            4. Sincroniza el username del usuario con el código RNR

        Nota: El envío de correo se maneja automáticamente mediante señales
        (ver registry/signals.py)
        """
        # 1. Si se activa la institucion y tiene un codigo temporal o vacio
        if self.activa and (not self.codigo or self.codigo.startswith("TEMP-")):
            self.codigo = self.generar_codigo_rnr()
            self.estatus = "aprobado"

        # 2. Si no hay enlace directo, intentar obtener usuario desde UserProfile
        if not self.usuario_id and self.pk:
            UserProfile = apps.get_model("users", "UserProfile")
            perfil = (
                UserProfile.objects.filter(institution=self)
                .select_related("user")
                .first()
            )
            if perfil and perfil.user:
                self.usuario = perfil.user

        # 3. Guardar institucion
        super().save(*args, **kwargs)

        # 4. Sincronizar username con codigo oficial cuando esta activa
        # Esto permite que el usuario inicie sesión con el código RNR
        if self.activa and self.usuario and self.usuario.username != self.codigo:
            self.usuario.username = self.codigo
            self.usuario.save(update_fields=["username"])

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def nombre_publico(self):
        """Retorna el nombre de la institución sin exponer el código.
        
        Uso: Para mostrar en vistas públicas donde no se debe revelar el código RNR.
        """
        return self.nombre
    
    def mostrar_codigo_para(self, user):
        """Verifica si el usuario tiene permiso para ver el código de la institución.
        
        Args:
            user: Usuario que solicita ver el código
            
        Returns:
            bool: True si puede ver el código, False si no
        """
        if not user or not user.is_authenticated:
            return False
        
        # Federación y superusuarios pueden ver todos los códigos
        if user.is_staff or user.is_superuser:
            return True
        
        # La propia institución puede ver su código
        if hasattr(user, 'userprofile') and user.userprofile.institution == self:
            return True
        
        return False


class Participante(models.Model):
    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Femenino"),
        ("O", "Otro"),
    ]

    CODIGO_AREA_CHOICES = [
        ("0424", "0424"),
        ("0414", "0414"),
        ("0422", "0422"),
        ("0412", "0412"),
        ("0426", "0426"),
        ("0416", "0416"),
    ]

    GRADO_CHOICES = [
        ("NO", "No estudia"),
        ("P1", "Preescolar Nivel 1"),
        ("P2", "Preescolar Nivel 2"),
        ("PR1", "1er Grado Primaria"),
        ("PR2", "2do Grado Primaria"),
        ("PR3", "3er Grado Primaria"),
        ("PR4", "4to Grado Primaria"),
        ("PR5", "5to Grado Primaria"),
        ("PR6", "6to Grado Primaria"),
        ("L1", "1er Año Liceo"),
        ("L2", "2do Año Liceo"),
        ("L3", "3er Año Liceo"),
        ("L4", "4to Año Liceo"),
        ("L5", "5to Año Liceo"),
        ("L6", "6to Año Liceo"),
        ("U", "Estudios Universitarios"),
        ("OTRO", "Otro/No especificado"),
    ]

    STATUS_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    NUMERO_VALIDATOR = RegexValidator(
        regex="^[0-9]{7}$", message="El número debe ser de 7 dígitos numéricos."
    )

    # Datos personales
    # Nota: cedula se mantiene por compatibilidad pero es la cédula personal
    cedula = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(regex="^[VE0-9]+$", message="Cédula válida requerida")
        ],
    )
    cedula_escolar = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Cédula Escolar",
        help_text="Cédula escolar del participante (si posee)",
    )
    condicion_tea = models.BooleanField(
        default=False,
        verbose_name="Condición TEA",
        help_text="Indica si el participante posee condición en el espectro autista",
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    email = models.EmailField()
    direccion = models.TextField()
    codigo_area = models.CharField(
        max_length=4,
        choices=CODIGO_AREA_CHOICES,
        default="0424",  # Puedes establecer un valor predeterminado
        verbose_name="Código de Área",
    )
    numero_telefono = models.CharField(
        max_length=7, validators=[NUMERO_VALIDATOR], verbose_name="Número (7 dígitos)"
    )

    # Ubicación
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    parroquia = models.ForeignKey(
        Parroquia,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Parroquia",
    )

    # Institución
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    grupo = models.ForeignKey(
        "Grupo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Grupo",
        help_text="Grupo al que pertenece el participante por defecto",
    )
    nombre_escuela = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre de la Escuela/Universidad",
        help_text="Nombre del centro de estudio actual.",
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

    # Representante (para menores)
    nombre_representante = models.CharField(max_length=200, blank=True)
    cedula_representante = models.CharField(max_length=20, blank=True)

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

    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="activo",
        verbose_name="Status",
    )

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
            models.Index(fields=["institucion"], name="idx_part_inst"),
            models.Index(fields=["estado", "municipio"], name="idx_part_ubicacion"),
            models.Index(fields=["status"], name="idx_part_status"),
            models.Index(fields=["grupo"], name="idx_part_grupo"),
            models.Index(fields=["apellidos", "nombres"], name="idx_part_nombre"),
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.cedula}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del participante."""
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

    # 5. PROPIEDAD PARA OBTENER EL NÚMERO COMPLETO DEL REPRESENTANTE
    @property
    def telefono_representante_completo(self):
        if self.codigo_area_representante and self.numero_telefono_representante:
            return (
                f"{self.codigo_area_representante}-{self.numero_telefono_representante}"
            )
        return ""

    def clean(self):
        """
        Valida los datos del participante antes de guardar.

        Validaciones:
            - Edad mínima de 4 años
            - Datos del representante obligatorios para menores de 18 años

        Raises:
            ValidationError: Si alguna validación falla.
        """
        super().clean()

        if self.fecha_nacimiento:
            edad_calculada = self.edad

            # Validar edad mínima
            if edad_calculada < 4:
                raise ValidationError(
                    {
                        "fecha_nacimiento": "El participante debe tener al menos 4 años para registrarse."
                    }
                )

            # Validar datos del representante para menores de edad
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

class AsistenciaEvento(models.Model):
    """
    Registra la asistencia de un participante a un evento específico,
    posiblemente como parte de un grupo.
    """
    ASISTENCIA_CHOICES = [
        ('asistio', 'Asistió'),
        ('ausente', 'Ausente'),
        ('pendiente', 'Pendiente'),
        ('justificado', 'Justificado'),
    ]

    evento = models.ForeignKey('Evento', on_delete=models.CASCADE, related_name='asistencias')
    participante = models.ForeignKey('Participante', on_delete=models.CASCADE, related_name='asistencias')
    grupo = models.ForeignKey('Grupo', on_delete=models.SET_NULL, null=True, blank=True, related_name='asistencias')
    asistencia = models.CharField(max_length=12, choices=ASISTENCIA_CHOICES, default='pendiente', db_index=True)
    observacion = models.TextField(blank=True)
    fecha_asistencia = models.DateTimeField(null=True, blank=True, help_text="Fecha y hora en que se marcó la asistencia.")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asistencia a Evento"
        verbose_name_plural = "Asistencias a Eventos"
        unique_together = ['evento', 'participante'] # Un participante solo puede tener un registro de asistencia por evento
        ordering = ['-evento__fecha', 'participante__apellidos']

    def __str__(self):
        return f"Asistencia de {self.participante.nombre_completo} a {self.evento.nombre}"

class EventoManager(models.Manager):
    """Manager con queries optimizadas para eventos."""
    
    def institucionales(self):
        """Eventos institucionales."""
        return self.filter(tipo_evento='institucional')
    
    def de_club(self):
        """Eventos de club."""
        return self.filter(tipo_evento='club')
    
    def pendientes_aprobacion(self):
        """Eventos de club pendientes de aprobación."""
        return self.de_club().filter(estado_evento='pendiente')
    
    def disponibles_para_inscripcion(self):
        """Eventos disponibles para inscripción."""
        return self.filter(
            models.Q(tipo_evento='institucional', estado_evento='abierto') |
            models.Q(tipo_evento='club', estado_evento='aprobado')
        )


class Evento(models.Model):
    """Modelo para representar eventos de robótica (institucionales y de club)."""

    TIPO_CHOICES = [
        ("competencia", "Competencia"),
        ("taller", "Taller"),
        ("seminario", "Seminario"),
        ("exhibicion", "Exhibición"),
    ]

    MODALIDAD_CHOICES = [
        ("presencial", "Presencial"),
        ("virtual", "Virtual"),
        ("hibrido", "Híbrido"),
    ]

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente Aprobación'),
        ('en_revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('publicado', 'Publicado'),
        ('en_proceso', 'En Proceso'),
        ('finalizado', 'Finalizado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
        # Mantener compatibilidad con estados antiguos
        ("abierto", "Abierto"),
        ("pausado", "Pausado"),
        ("cerrado", "Cerrado"),
    ]
    
    TIPO_EVENTO_CHOICES = [
        ('institucional', 'Evento Institucional'),
        ('club', 'Evento de Club'),
    ]

    nombre = models.CharField(max_length=255, db_index=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="competencia")
    categoria = models.CharField(max_length=100, blank=True)
    fecha = models.DateField(db_index=True)
    descripcion = models.TextField(blank=True)
    modalidad = models.CharField(
        max_length=20, choices=MODALIDAD_CHOICES, default="presencial"
    )
    ubicacion = models.CharField(max_length=255, blank=True)
    estado_evento = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="abierto", db_index=True
    )
    estado = models.ForeignKey(
        "Estado", on_delete=models.SET_NULL, null=True, blank=True
    )
    municipio = models.ForeignKey(
        "Municipio", on_delete=models.SET_NULL, null=True, blank=True
    )
    parroquia = models.ForeignKey(
        "Parroquia", on_delete=models.SET_NULL, null=True, blank=True
    )
    direccion = models.CharField(max_length=300, blank=True)
    capacidad_maxima = models.PositiveIntegerField(null=True, blank=True)
    requisitos = models.TextField(blank=True)
    
    # Discriminador de tipo
    tipo_evento = models.CharField(
        max_length=20,
        choices=TIPO_EVENTO_CHOICES,
        default='institucional',
        verbose_name='Tipo de Evento'
    )
    
    # Relaciones polimórficas
    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Para eventos institucionales"
    )
    club_organizador = models.ForeignKey(
        'Club',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='eventos',
        help_text="Para eventos de club"
    )
    
    # Campos de aprobación (solo para eventos de club)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    aprobado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_club_aprobados'
    )
    observaciones_aprobacion = models.TextField(blank=True)
    
    # Metadata
    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='eventos_creados'
    )
    activo = models.BooleanField(default=True, db_index=True)
    cancelado = models.BooleanField(default=False)
    motivo_cancelacion = models.TextField(blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    objects = EventoManager()

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha", "activo"], name="idx_evt_fecha_activo"),
            models.Index(fields=["institucion"], name="idx_evt_institucion"),
            models.Index(fields=['tipo_evento', 'estado_evento'], name='idx_evt_tipo_estado'),
            models.Index(fields=['club_organizador', 'estado_evento'], name='idx_evt_club_estado'),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(tipo_evento='institucional', institucion__isnull=False, club_organizador__isnull=True) |
                    models.Q(tipo_evento='club', club_organizador__isnull=False, institucion__isnull=True)
                ),
                name='evento_organizador_valido'
            )
        ]

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"
    
    @property
    def es_evento_club(self):
        """Indica si es un evento de club."""
        return self.tipo_evento == 'club'
    
    @property
    def organizador(self):
        """Retorna el organizador según el tipo."""
        return self.club_organizador if self.es_evento_club else self.institucion
    
    @property
    def requiere_aprobacion(self):
        """Indica si el evento requiere aprobación."""
        return self.es_evento_club
    
    @property
    def puede_inscribirse(self):
        """Indica si se pueden inscribir grupos."""
        if self.es_evento_club:
            return self.estado_evento == 'aprobado' and self.activo and not self.cancelado
        return self.estado_evento == 'abierto' and self.activo and not self.cancelado

    @property
    def esta_vigente(self):
        """Verifica si el evento aún está vigente."""
        return self.activo and not self.cancelado and self.fecha >= date.today()

    @property
    def inscripciones_abiertas(self):
        """Verifica si las inscripciones están abiertas."""
        return self.puede_inscribirse and self.fecha >= date.today()

    @property
    def cupos_disponibles(self):
        """Calcula cupos disponibles."""
        if not self.capacidad_maxima:
            return float("inf")
        inscritos = self.inscripciones_grupo.filter(activo=True).count()
        return max(0, self.capacidad_maxima - inscritos)
    
    def clean(self):
        """Validaciones del modelo."""
        if self.tipo_evento == 'institucional' and not self.institucion:
            raise ValidationError("Evento institucional debe tener institución organizadora")
        if self.tipo_evento == 'club' and not self.club_organizador:
            raise ValidationError("Evento de club debe tener club organizador")
        if self.institucion and self.club_organizador:
            raise ValidationError("Evento no puede tener ambos organizadores")


class Inscripcion(models.Model):
    MODALIDAD_CHOICES = (
        ("individual", "Individual"),
        ("equipo", "Equipo"),
    )

    evento = models.ForeignKey("Evento", on_delete=models.CASCADE)
    lider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    nombre_proyecto = models.CharField(max_length=150)
    descripcion_proyecto = models.TextField()
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evento.nombre} - {self.lider.username}"


class IntegranteEquipo(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion, related_name="integrantes", on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.usuario.username


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
        ("mixto", "Mixto"),
    ]

    nombre = models.CharField(
        max_length=150, verbose_name="Nombre del Grupo", db_index=True
    )
    codigo = models.CharField(max_length=20, unique=True, editable=False)
    criterio = models.CharField(
        max_length=20, choices=CRITERIO_CHOICES, default="mixto"
    )
    estado_grupo = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="editable", db_index=True
    )
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grupos_creados",
    )

    # Campos legacy de tutor (mantenidos para compatibilidad)
    # TODO: Migrar a relación M2M con modelo Tutor
    tutor_nombre = models.CharField(max_length=200, blank=True, null=True)
    tutor_apellidos = models.CharField(
        max_length=200, default="", blank=True, null=True
    )
    tutor_cedula = models.CharField(max_length=20, db_index=True, blank=True, null=True)
    tutor_telefono = models.CharField(max_length=20, blank=True, null=True)

    # Relación M2M con Tutores (nueva implementación)
    tutores = models.ManyToManyField(
        "Tutor",
        related_name="grupos",
        blank=True,
        verbose_name="Tutores asignados"
    )

    participantes = models.ManyToManyField(
        "Participante", related_name="grupos", verbose_name="Integrantes del Grupo"
    )
    evento = models.ForeignKey(
        "Evento",
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

    def save(self, *args, **kwargs):
        if not self.codigo:
            chars = string.ascii_uppercase + string.digits
            while True:
                codigo = "GRP-" + get_random_string(length=8, allowed_chars=chars)
                if not Grupo.objects.filter(codigo=codigo).exists():
                    self.codigo = codigo
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.usuario_creador.username}"


class Club(models.Model):
    """Modelo para representar clubes de robótica."""

    # NOTA: LINEAS_INVESTIGACION_CHOICES eliminado - usar modelo LineaInvestigacion dinámico

    ESTADO_VINCULACION_CHOICES = [
        ("abierto", "Abierto"),
        ("cerrado", "Cerrado"),
        ("invitacion", "Bajo Invitación"),
    ]

    # Estados del club para flujo de aprobación
    STATUS_CHOICES = [
        ("borrador", "Borrador"),
        ("pendiente", "Pendiente de Revisión"),
        ("en_revision", "En Revisión"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    ]

    nombre = models.CharField(
        max_length=200, verbose_name="Nombre del Club", db_index=True
    )
    logo = models.ImageField(upload_to="clubes/logos/", blank=True, null=True)
    siglas = models.CharField(max_length=10, blank=True)
    descripcion = models.TextField(verbose_name="Descripción")
    ubicacion = models.CharField(max_length=255, verbose_name="Ubicación")
    fecha_fundacion = models.DateField(null=True, blank=True)

    # Relación con institución
    institucion_creadora = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE,
        related_name="clubes_creados",
        null=True,
        blank=True,
    )

    # Coordinador del club (usuario responsable)
    coordinador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="clubes_coordinados",
        null=True,
        blank=True,
        verbose_name="Coordinador del Club",
    )

    # Documento legal (RUT/NIT o aval institucional)
    documento_legal = models.CharField(
        max_length=255, blank=True, verbose_name="Documento Legal / Aval Institucional"
    )

    # NOTA: Campos linea_1, linea_2, linea_3 eliminados - usar ClubLineaInvestigacion

    # Estado de vinculación y cupos
    estado_vinculacion = models.CharField(
        max_length=20, choices=ESTADO_VINCULACION_CHOICES, default="abierto"
    )
    cupo_maximo = models.IntegerField(
        default=10, verbose_name="Cupo máximo de instituciones"
    )
    requisitos = models.TextField(blank=True)

    # Nuevo: Status para flujo de aprobación
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="borrador",
        verbose_name="Estado del Club",
        db_index=True,
    )

    # Fechas
    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True, db_index=True)
    
    # Campos para eliminación
    eliminado = models.BooleanField(default=False, db_index=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    motivo_eliminacion = models.TextField(blank=True)
    eliminado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clubes_eliminados'
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
        """Override save para cerrar automáticamente cuando no hay cupos."""
        # Calcular cupos disponibles antes de guardar
        if self.cupo_maximo and self.pk:
            miembros_actuales = self.membresias.filter(estado="miembro_activo").count()
            cupos = max(0, self.cupo_maximo - miembros_actuales)

            # Si no hay cupos disponibles y está abierto, cerrar automáticamente
            if cupos == 0 and self.estado_vinculacion == "abierto":
                self.estado_vinculacion = "cerrado"

        super().save(*args, **kwargs)

    @property
    def lineas_investigacion(self):
        """Retorna lista de líneas de investigación del club usando ClubLineaInvestigacion."""
        if self.pk:
            lineas_nm = self.club_lineas.select_related('linea').filter(
                linea__activa=True
            ).order_by('orden').values_list('linea__nombre', flat=True)
            lineas = list(lineas_nm)
            if lineas:
                return lineas
        return ['Sin líneas asignadas']

    @property
    def cupos_disponibles(self):
        """Retorna cuántos cupos quedan disponibles."""
        if not self.pk:
            return self.cupo_maximo
        miembros_actuales = self.membresias.filter(estado="miembro_activo").count()
        return max(0, self.cupo_maximo - miembros_actuales)

    @property
    def puede_postularse(self):
        """Verifica si el club acepta nuevas postulaciones."""
        return (
            self.activo
            and self.status == "aprobado"
            and self.estado_vinculacion == "abierto"
            and self.cupos_disponibles > 0
        )

    def enviar_a_revision(self):
        """Envía el club a revisión (de borrador a pendiente)."""
        if self.status == "borrador":
            self.status = "pendiente"
            self.save(update_fields=["status"])
            return True
        return False

    def aprobar(self):
        """Aprueba el club."""
        from django.utils import timezone

        self.status = "aprobado"
        self.fecha_aprobacion = timezone.now()
        self.save(update_fields=["status", "fecha_aprobacion"])
        return True

    def rechazar(self, observaciones=""):
        """Rechaza el club."""
        self.status = "rechazado"
        self.save(update_fields=["status"])
        # Aquí se podría guardar las observaciones en un campo separado
        return True

    def puede_editar(self, user):
        """Verifica si el usuario puede editar el club."""
        # El coordinador o el creador pueden editar
        if self.coordinador == user:
            return True
        if self.institucion_creadora and hasattr(user, "userprofile"):
            if user.userprofile.institution == self.institucion_creadora:
                return True
        return False
    
    def contar_reenvios(self):
        """Cuenta cuántas veces se ha reenviado el club después de rechazos."""
        return self.historial.filter(
            estado_anterior="rechazado",
            estado_nuevo="pendiente"
        ).count()
    
    def obtener_ultimo_rechazo(self):
        """Obtiene el último historial de rechazo con observaciones."""
        return self.historial.filter(
            estado_nuevo="rechazado"
        ).order_by('-fecha').first()


class MembresiaClu(models.Model):
    """
    Modelo para gestionar solicitudes de membresía a clubes.
    
    Flujo de Doble Aprobación (permisos_clubes.md - Sección 6):
    1. Solicitante crea registro con estado PENDIENTE_FILTRO
    2. Institución Fundadora da visto bueno -> VISTO_BUENO_FUNDADORA
    3. Ente Rector aprueba finalmente -> MIEMBRO_ACTIVO
    
    Ninguna institución puede ser MIEMBRO_ACTIVO sin ambos checks.
    """

    # Estados federados para el flujo de doble aprobación
    ESTADO_CHOICES = [
        ('pendiente_filtro', 'Pendiente de Filtro (Fundadora)'),
        ('visto_bueno_fundadora', 'Visto Bueno Fundadora'),
        ('miembro_activo', 'Miembro Activo'),
        ('rechazada', 'Rechazada'),
    ]

    # Tipos de línea de investigación en la membresía
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

    # Tipo de línea de investigación que aporta la institución
    tipo_linea = models.CharField(
        max_length=20,
        choices=TIPO_LINEA_CHOICES,
        default="soporte",
        verbose_name="Tipo de Línea de Investigación",
    )

    estado = models.CharField(
        max_length=25,
        choices=ESTADO_CHOICES,
        default='pendiente_filtro',
        db_index=True
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    # === Campos de Auditoría para Flujo Federado ===
    # Fase 1: Visto bueno de la Institución Fundadora
    visto_bueno_fundadora = models.BooleanField(
        default=False,
        verbose_name='Visto Bueno Fundadora'
    )
    visto_bueno_fundadora_por = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='membresias_visto_bueno',
        verbose_name='Visto bueno dado por'
    )
    visto_bueno_fundadora_fecha = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha visto bueno'
    )
    observaciones_fundadora = models.TextField(
        blank=True,
        verbose_name='Observaciones de la Fundadora'
    )

    # Fase 2: Aprobación del Ente Rector (Federación Central)
    aprobacion_ente_rector = models.BooleanField(
        default=False,
        verbose_name='Aprobación Ente Rector'
    )
    aprobacion_ente_rector_por = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='membresias_aprobadas_rector',
        verbose_name='Aprobado por (Ente Rector)'
    )
    aprobacion_ente_rector_fecha = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha aprobación Ente Rector'
    )
    observaciones_rector = models.TextField(
        blank=True,
        verbose_name='Observaciones del Ente Rector'
    )

    class Meta:
        verbose_name = "Membresía de Club"
        verbose_name_plural = "Membresías de Clubes"
        ordering = ["-fecha_solicitud"]
        indexes = [
            # Índice único parcial: solo para solicitudes activas
            models.Index(
                fields=['club', 'institucion'],
                name='idx_memb_club_inst_active',
                condition=models.Q(estado__in=['pendiente_filtro', 'visto_bueno_fundadora'])
            ),
        ]

    def __str__(self):
        return f"{self.institucion.nombre} -> {self.club.nombre} ({self.estado})"


class InscripcionGrupoEvento(models.Model):
    """Modelo para inscripción de grupos a eventos (institucionales o de club)."""

    ROL_CHOICES = [
        ("participante", "Participante"),
        ("expositor", "Expositor"),
        ("competidor", "Competidor"),
    ]

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="inscripciones_grupo"
    )
    grupo = models.ForeignKey(
        Grupo, on_delete=models.CASCADE, related_name="inscripciones"
    )
    rol_participacion = models.CharField(
        max_length=20, choices=ROL_CHOICES, default="participante"
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Inscripción Grupo-Evento"
        verbose_name_plural = "Inscripciones Grupo-Evento"
        unique_together = ["evento", "grupo"]
        ordering = ["-fecha_inscripcion"]

    def __str__(self):
        return f"{self.grupo.nombre} -> {self.evento.nombre}"
    
    def clean(self):
        """Validar que el grupo puede inscribirse al evento."""
        super().clean()
        
        if self.evento.es_evento_club:
            # Validar que la institución del grupo es miembro del club
            institucion_grupo = self.grupo.usuario_creador.userprofile.institution
            es_miembro = self.evento.club_organizador.membresias.filter(
                institucion=institucion_grupo,
                estado='miembro_activo'
            ).exists()
            
            if not es_miembro:
                raise ValidationError(
                    f"Solo instituciones miembros del club '{self.evento.club_organizador.nombre}' "
                    "pueden inscribir grupos a este evento."
                )


class SolicitudEliminacionClub(models.Model):
    """Modelo para gestionar solicitudes de eliminación de clubes aprobados."""

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
    ]

    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="solicitudes_eliminacion"
    )
    institucion_solicitante = models.ForeignKey(
        Institucion, on_delete=models.CASCADE
    )
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
            models.Index(fields=["estado", "fecha_solicitud"], name="idx_sol_elim_estado"),
        ]

    def __str__(self):
        return f"Solicitud eliminación: {self.club.nombre} ({self.estado})"


class Notificacion(models.Model):
    """Modelo para sistema de notificaciones internas (buzón de mensajes)."""

    TIPO_CHOICES = [
        ("club_aprobado", "Club Aprobado"),
        ("club_rechazado", "Club Rechazado"),
        ("solicitud_eliminacion", "Solicitud de Eliminación"),
        ("eliminacion_aprobada", "Eliminación Aprobada"),
        ("eliminacion_rechazada", "Eliminación Rechazada"),
        ("membresia_aprobada", "Membresía Aprobada"),
        ("membresia_rechazada", "Membresía Rechazada"),
        ("salida_club", "Salida de Club"),
        ("sistema", "Notificación del Sistema"),
    ]

    destinatario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, db_index=True)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    club = models.ForeignKey(
        Club, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["destinatario", "leida"], name="idx_notif_dest_leida"),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.destinatario.username}"

    def marcar_leida(self):
        """Marca la notificación como leída."""
        if not self.leida:
            self.leida = True
            self.save(update_fields=["leida"])


class HistorialClub(models.Model):
    """Registra todos los cambios de estado de un club para auditoría."""

    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="historial"
    )
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
    """Sistema de comentarios para revisión de clubes."""

    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="comentarios"
    )
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
    """Sistema de calificación y reseñas de clubes."""

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
    puntuacion = models.IntegerField(choices=PUNTUACION_CHOICES, verbose_name="Puntuación")
    resena = models.TextField(blank=True, verbose_name="Reseña")
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Calificación de Club"
        verbose_name_plural = "Calificaciones de Clubes"
        unique_together = ["club", "institucion"]
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["club", "-fecha"], name="idx_calif_club_fecha"),
        ]

    def __str__(self):
        return f"{self.club.nombre} - {self.puntuacion}★ por {self.institucion.nombre}"


class ClubEvento(models.Model):
    """Vinculación entre clubes y eventos."""

    ROL_CHOICES = [
        ("organizador", "Organizador"),
        ("colaborador", "Colaborador"),
        ("participante", "Participante"),
    ]

    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="eventos_vinculados"
    )
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="clubes_vinculados"
    )
    rol = models.CharField(
        max_length=20, choices=ROL_CHOICES, default="participante", verbose_name="Rol del Club"
    )
    fecha_vinculacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Club-Evento"
        verbose_name_plural = "Clubes-Eventos"
        unique_together = ["club", "evento"]
        ordering = ["-fecha_vinculacion"]
        indexes = [
            models.Index(fields=["evento", "activo"], name="idx_clubevt_evt_act"),
        ]

    def __str__(self):
        return f"{self.club.nombre} → {self.evento.nombre} ({self.rol})"


class ClubLineaInvestigacion(models.Model):
    """Relación N:M entre clubes y líneas de investigación."""
    
    TIPO_LINEA_CHOICES = [
        ('principal', 'Principal'),
        ('soporte', 'Soporte'),
        ('afines', 'Afines'),
    ]
    
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='club_lineas'
    )
    linea = models.ForeignKey(
        LineaInvestigacion,
        on_delete=models.PROTECT,
        related_name='clubes'
    )
    tipo_linea = models.CharField(
        max_length=20,
        choices=TIPO_LINEA_CHOICES,
        default='principal',
        verbose_name="Tipo de Línea"
    )
    orden = models.IntegerField(default=0, verbose_name="Orden")
    fecha_vinculacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Club-Línea de Investigación"
        verbose_name_plural = "Clubes-Líneas de Investigación"
        unique_together = ['club', 'linea']
        ordering = ['orden']
        indexes = [
            models.Index(fields=['club', 'orden'], name='idx_clublinea_club_orden'),
        ]
    
    def __str__(self):
        return f"{self.club.nombre} - {self.linea.nombre} ({self.tipo_linea})"


class Tutor(models.Model):
    """
    Modelo para representar tutores de grupos.
    
    Un tutor es una persona responsable que guía y acompaña
    a un grupo de participantes en eventos de robótica.
    
    Attributes:
        id: UUID único para identificación.
        institucion: Institución a la que pertenece el tutor.
        nombres: Nombres del tutor.
        apellidos: Apellidos del tutor.
        cedula: Cédula de identidad (única).
        telefono: Teléfono de contacto.
        email: Correo electrónico.
        profesion: Profesión o especialidad.
        experiencia: Experiencia en robótica.
        status: Estado del tutor (activo/inactivo).
        created_at: Fecha de creación del registro.
    """
    
    STATUS_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        verbose_name='ID'
    )
    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.PROTECT,
        related_name='tutores',
        verbose_name='Institución'
    )
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    cedula = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex='^[0-9]+$',
                message='La cédula debe contener solo números (sin letras V/E)'
            )
        ],
        verbose_name='Cédula',
        help_text='Ingrese solo números, sin letras (V/E)'
    )
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
    email = models.EmailField(verbose_name='Correo Electrónico')
    profesion = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Profesión'
    )
    experiencia = models.TextField(
        blank=True,
        verbose_name='Experiencia en Robótica'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='activo',
        db_index=True,
        verbose_name='Estado'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutores'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cedula'], name='idx_tutor_cedula'),
            models.Index(fields=['status', 'institucion'], name='idx_tutor_status_inst'),
        ]
    
    def __str__(self) -> str:
        """Representación en string del tutor."""
        return f"{self.get_nombre_completo()} ({self.cedula})"
    
    def get_nombre_completo(self) -> str:
        """Retorna el nombre completo del tutor."""
        return f"{self.nombres} {self.apellidos}"
