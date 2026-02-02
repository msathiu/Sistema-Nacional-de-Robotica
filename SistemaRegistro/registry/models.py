from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError 
from datetime import date 
from django.conf import settings
import string
import random

class Estado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.nombre

class Municipio(models.Model):
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ['estado', 'nombre']
    
    def __str__(self):
        return f"{self.nombre}, {self.estado.nombre}"

def generar_codigo_unico():
    """Genera un código aleatorio de 6 caracteres alfanuméricos"""
    caracteres = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(random.choices(caracteres, k=6))
        # Verificamos que no exista ya en la base de datos
        if not Institucion.objects.filter(codigo=codigo).exists():
            return codigo

class Institucion(models.Model):
    
    TIPO_FEDERADO_CHOICES = [
        ('institucion', 'Institución Educativa'),
        ('organizacion', 'Organización / Club'),
        ('particular', 'Particular / Independiente'),
    ]
    nombre = models.CharField(max_length=255)
    rif = models.CharField(max_length=20, null=True, blank=True) # Agregamos null=True y blank=True
    tipo_federado = models.CharField(
        max_length=20, 
        choices=TIPO_FEDERADO_CHOICES, 
        default='institucion' # Al darle un default, evitamos el error de NotNull
    )
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=25, unique=True)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    activa = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=False)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.codigo or self.codigo == "SISTEMA GENERARÁ CÓDIGO":
            # RNR26- (6 chars) + 6 aleatorios = 12 caracteres total.
            # Esto cabe perfectamente en tu max_length=20
            nuevo_cod = f"RNR26-{generar_codigo_unico()}"
            
            while Institucion.objects.filter(codigo=nuevo_cod).exists():
                nuevo_cod = f"RNR26-{generar_codigo_unico()}"
                
            self.codigo = nuevo_cod
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Instituciones"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Participante(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    CODIGO_AREA_CHOICES = [
        ('0424', '0424'),
        ('0414', '0414'),
        ('0422', '0422'),
        ('0412', '0412'),
        ('0426', '0426'),
        ('0416', '0416'),
        
        
    ]

    GRADO_CHOICES = [
        ('NO', 'No estudia'),
        ('P1', 'Preescolar Nivel 1'),
        ('P2', 'Preescolar Nivel 2'),
        ('PR1', '1er Grado Primaria'),
        ('PR2', '2do Grado Primaria'),
        ('PR3', '3er Grado Primaria'),
        ('PR4', '4to Grado Primaria'),
        ('PR5', '5to Grado Primaria'),
        ('PR6', '6to Grado Primaria'),
        ('L1', '1er Año Liceo'),
        ('L2', '2do Año Liceo'),
        ('L3', '3er Año Liceo'),
        ('L4', '4to Año Liceo'),
        ('L5', '5to Año Liceo'),
        ('L6', '6to Año Liceo'),
        ('U', 'Estudios Universitarios'),
        ('OTRO', 'Otro/No especificado'),
    ]

    NUMERO_VALIDATOR = RegexValidator(
        regex='^[0-9]{7}$', 
        message='El número debe ser de 7 dígitos numéricos.'
    )

    # Datos personales
    cedula = models.CharField(
        max_length=20, 
        unique=True, 
        validators=[
            RegexValidator(
                regex='^[VE0-9]+$', 
                message='Cédula válida requerida'
            )
        ]
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
        default='0424', # Puedes establecer un valor predeterminado
        verbose_name='Código de Área'
    )
    numero_telefono = models.CharField(
        max_length=7,
        validators=[NUMERO_VALIDATOR],
        verbose_name='Número (7 dígitos)'
    )
    
    # Ubicación
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    
    # Institución
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    nombre_escuela = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name='Nombre de la Escuela/Universidad',
        help_text='Nombre del centro de estudio actual.'
    )
    grado_escolar = models.CharField(
        max_length=4, 
        choices=GRADO_CHOICES,
        default='NO',
        verbose_name='Nivel Educativo/Grado'
    )
    
    # Representante (para menores)
    nombre_representante = models.CharField(max_length=200, blank=True)
    cedula_representante = models.CharField(max_length=20, blank=True)
    

    codigo_area_representante = models.CharField(
        max_length=4, 
        choices=CODIGO_AREA_CHOICES,
        blank=True,
        verbose_name='Cód. Área Rep.'
    )
    numero_telefono_representante = models.CharField(
        max_length=7,
        validators=[NUMERO_VALIDATOR],
        blank=True,
        verbose_name='Número Rep. (7 dígitos)'
    )
    email_representante = models.EmailField(blank=True)
    
    # Metadata
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.cedula}"
    
    @property
    def edad(self):
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    @property
    def telefono_completo(self):
        return f"{self.codigo_area}-{self.numero_telefono}"

    # 5. PROPIEDAD PARA OBTENER EL NÚMERO COMPLETO DEL REPRESENTANTE
    @property
    def telefono_representante_completo(self):
        if self.codigo_area_representante and self.numero_telefono_representante:
            return f"{self.codigo_area_representante}-{self.numero_telefono_representante}"
        return ""


    # 2. MÉTODO CLEAN PARA VALIDAR LA EDAD MÍNIMA
    def clean(self):
        # Solo valida si la fecha de nacimiento ha sido proporcionada
        if self.fecha_nacimiento:
            
            # Usando la propiedad edad para simplificar:
            edad_calculada = self.edad
            
            # Condición de validación: debe ser mayor a 3 años
            if edad_calculada < 4: 
                # Si la edad es 3 o menos, levantamos un error
                raise ValidationError(
                    {'fecha_nacimiento': 'El participante debe tener al menos 4 años para registrarse.'}
                )
        
        # Llama al clean() del padre para cualquier otra validación de Django
        super().clean()


class Evento(models.Model):
    nombre = models.CharField(max_length=255)
    fecha = models.DateField()
    descripcion = models.TextField(blank=True)
    estado = models.ForeignKey("Estado", on_delete=models.SET_NULL, null=True)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre



class Inscripcion(models.Model):
    MODALIDAD_CHOICES = (
        ('individual', 'Individual'),
        ('equipo', 'Equipo'),
    )

    evento = models.ForeignKey('Evento', on_delete=models.CASCADE)
    lider = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE
)

    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    nombre_proyecto = models.CharField(max_length=150)
    descripcion_proyecto = models.TextField()
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evento.nombre} - {self.lider.username}"

class IntegranteEquipo(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion,
        related_name='integrantes',
        on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE
)

    def __str__(self):
        return self.usuario.username

class Grupo(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Grupo")
    
    # El usuario que crea el grupo (usualmente el representante de la institución)
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='grupos_creados'
    )
    
    # Datos del Tutor
    tutor_nombre = models.CharField(max_length=200)
    tutor_cedula = models.CharField(max_length=20)
    tutor_telefono = models.CharField(max_length=20, blank=True)
    
    # Relación con Participantes (Muchos a Muchos)
    participantes = models.ManyToManyField(
        Participante, 
        related_name='grupos',
        verbose_name="Integrantes del Grupo"
    )
    
    # Relación opcional con un evento para el estado de "Asignado"
    evento = models.ForeignKey(
        Evento, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='grupos_inscritos'
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.nombre} - {self.usuario_creador.username}"