import logging
import random
import string
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

    NUMERO_VALIDATOR = RegexValidator(
        regex="^[0-9]{7}$", message="El número debe ser de 7 dígitos numéricos."
    )

    # Datos personales
    cedula = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(regex="^[VE0-9]+$", message="Cédula válida requerida")
        ],
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

    # Institución
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
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
    activo = models.BooleanField(default=True)

    user = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        ordering = ["apellidos", "nombres"]
        indexes = [
            models.Index(fields=["cedula"], name="idx_part_cedula"),
            models.Index(fields=["email"], name="idx_part_email"),
            models.Index(fields=["institucion"], name="idx_part_inst"),
            models.Index(fields=["estado", "municipio"], name="idx_part_ubicacion"),
            models.Index(fields=["activo"], name="idx_part_activo"),
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


class Evento(models.Model):
    """Modelo para representar eventos de robótica."""

    TIPO_CHOICES = [
        ('competencia', 'Competencia'),
        ('taller', 'Taller'),
        ('seminario', 'Seminario'),
        ('exhibicion', 'Exhibición'),
    ]

    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('hibrido', 'Híbrido'),
    ]

    ESTADO_CHOICES = [
        ('abierto', 'Abierto'),
        ('pausado', 'Pausado'),
        ('cerrado', 'Cerrado'),
        ('finalizado', 'Finalizado'),
    ]

    nombre = models.CharField(max_length=255, db_index=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='competencia')
    fecha = models.DateField(db_index=True)
    descripcion = models.TextField(blank=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default='presencial')
    ubicacion = models.CharField(max_length=255, blank=True)
    estado_evento = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierto', db_index=True)
    estado = models.ForeignKey(
        "Estado", on_delete=models.SET_NULL, null=True, blank=True
    )
    municipio = models.ForeignKey("Municipio", on_delete=models.SET_NULL, null=True, blank=True)
    parroquia = models.ForeignKey("Parroquia", on_delete=models.SET_NULL, null=True, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    capacidad_maxima = models.PositiveIntegerField(null=True, blank=True)
    requisitos = models.TextField(blank=True)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
    activo = models.BooleanField(default=True, db_index=True)
    cancelado = models.BooleanField(default=False)
    motivo_cancelacion = models.TextField(blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha", "activo"], name="idx_evt_fecha_activo"),
            models.Index(fields=["institucion"], name="idx_evt_institucion"),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"

    @property
    def esta_vigente(self):
        """Verifica si el evento aún está vigente."""
        return self.activo and not self.cancelado and self.fecha >= date.today()

    @property
    def inscripciones_abiertas(self):
        """Verifica si las inscripciones están abiertas."""
        return (self.activo and 
                not self.cancelado and 
                self.estado_evento == 'abierto' and 
                self.fecha >= date.today())

    @property
    def cupos_disponibles(self):
        """Calcula cupos disponibles."""
        if not self.capacidad_maxima:
            return float('inf')
        # Asumiendo que tienes un modelo Proyecto relacionado
        inscritos = self.proyectos.count() if hasattr(self, 'proyectos') else 0
        return max(0, self.capacidad_maxima - inscritos)

    @property
    def puede_inscribirse(self):
        """Verifica si se pueden hacer inscripciones."""
        return self.inscripciones_abiertas and self.cupos_disponibles > 0

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
        ('editable', 'Editable'),
        ('inscrito', 'Inscrito'),
        ('bloqueado', 'Bloqueado'),
    ]

    CRITERIO_CHOICES = [
        ('edad', 'Por Edad'),
        ('nivel', 'Por Nivel Educativo'),
        ('proyecto', 'Por Proyecto'),
        ('mixto', 'Mixto'),
    ]

    nombre = models.CharField(
        max_length=150, verbose_name="Nombre del Grupo", db_index=True
    )
    codigo = models.CharField(max_length=20, unique=True, editable=False)
    criterio = models.CharField(max_length=20, choices=CRITERIO_CHOICES, default='mixto')
    estado_grupo = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='editable', db_index=True)
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grupos_creados",
    )
    
    # Cambiados a null=True para evitar el error de base de datos si fallara la lógica
    tutor_nombre = models.CharField(max_length=200, blank=True, null=True)
    tutor_apellidos = models.CharField(max_length=200, default='', blank=True, null=True)
    tutor_cedula = models.CharField(max_length=20, db_index=True, blank=True, null=True)
    tutor_telefono = models.CharField(max_length=20, blank=True, null=True)
    
    participantes = models.ManyToManyField(
        'Participante', related_name="grupos", verbose_name="Integrantes del Grupo"
    )
    evento = models.ForeignKey(
        'Evento',
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
                codigo = 'GRP-' + get_random_string(length=8, allowed_chars=chars)
                if not Grupo.objects.filter(codigo=codigo).exists():
                    self.codigo = codigo
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.usuario_creador.username}"

class Club(models.Model):
    """Modelo para representar clubes de robótica."""

    LINEAS_INVESTIGACION_CHOICES = [
        ("electronica", "Electrónica y Circuitos"),
        ("programacion", "Programación y Algoritmos"),
        ("mecanica", "Mecánica y Estructuras"),
        ("ia", "Inteligencia Artificial"),
        ("iot", "Internet de las Cosas (IoT)"),
        ("automatizacion", "Automatización Industrial"),
        ("diseno_3d", "Diseño e Impresión 3D"),
        ("telecom", "Telecomunicaciones"),
    ]

    ESTADO_VINCULACION_CHOICES = [
        ('abierto', 'Abierto'),
        ('cerrado', 'Cerrado'),
        ('invitacion', 'Bajo Invitación'),
    ]

    nombre = models.CharField(
        max_length=200, verbose_name="Nombre del Club", db_index=True
    )
    logo = models.ImageField(upload_to='clubes/logos/', blank=True, null=True)
    siglas = models.CharField(max_length=10, blank=True)
    descripcion = models.TextField(verbose_name="Descripción")
    ubicacion = models.CharField(max_length=255, verbose_name="Ubicación")
    fecha_fundacion = models.DateField(null=True, blank=True)
    institucion_creadora = models.ForeignKey(
        Institucion, on_delete=models.CASCADE, related_name='clubes_creados',
        null=True, blank=True
    )
    linea_1 = models.CharField(
        max_length=50,
        choices=LINEAS_INVESTIGACION_CHOICES,
        verbose_name="Línea de investigación 1",
    )
    linea_2 = models.CharField(
        max_length=50,
        choices=LINEAS_INVESTIGACION_CHOICES,
        verbose_name="Línea de investigación 2",
        blank=True,
        null=True,
    )
    linea_3 = models.CharField(
        max_length=50,
        choices=LINEAS_INVESTIGACION_CHOICES,
        verbose_name="Línea de investigación 3",
        blank=True,
        null=True,
    )
    estado_vinculacion = models.CharField(
        max_length=20, choices=ESTADO_VINCULACION_CHOICES, default='abierto'
    )
    cupo_maximo = models.IntegerField(default=10, verbose_name="Cupo máximo de instituciones")
    requisitos = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Club"
        verbose_name_plural = "Clubes"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["activo", "nombre"], name="idx_club_activo_nombre"),
        ]

    def __str__(self):
        return self.nombre

    @property
    def lineas_investigacion(self):
        """Retorna una lista con las líneas de investigación del club."""
        lineas = [self.linea_1]
        if self.linea_2:
            lineas.append(self.linea_2)
        if self.linea_3:
            lineas.append(self.linea_3)
        return lineas

    @property
    def cupos_disponibles(self):
        """Retorna cuántos cupos quedan disponibles."""
        miembros_actuales = self.membresias.filter(estado='aprobada').count()
        return max(0, self.cupo_maximo - miembros_actuales)


class MembresiaClu(models.Model):
    """Modelo para gestionar solicitudes de membresía a clubes."""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='membresias')
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    carta_intencion = models.TextField()
    propuesta_tecnica = models.TextField()
    representante_legal = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Membresía de Club"
        verbose_name_plural = "Membresías de Clubes"
        unique_together = ['club', 'institucion']
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"{self.institucion.nombre} -> {self.club.nombre} ({self.estado})"


class InscripcionGrupoEvento(models.Model):
    """Modelo para inscripción de grupos a eventos."""

    ROL_CHOICES = [
        ('participante', 'Participante'),
        ('expositor', 'Expositor'),
        ('competidor', 'Competidor'),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='inscripciones_grupo')
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='inscripciones')
    rol_participacion = models.CharField(max_length=20, choices=ROL_CHOICES, default='participante')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Inscripción Grupo-Evento"
        verbose_name_plural = "Inscripciones Grupo-Evento"
        unique_together = ['evento', 'grupo']
        ordering = ['-fecha_inscripcion']

    def __str__(self):
        return f"{self.grupo.nombre} -> {self.evento.nombre}"
