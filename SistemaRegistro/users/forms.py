from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from registry.models import Participante, Estado, Municipio, Institucion
import datetime
from datetime import date
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from registry.models import Institucion
# Importación necesaria para la validación de contraseñas
import re 
# Importación necesaria para la validación de contraseñas
from django.core.exceptions import ValidationError 

# Asumiendo que tu modelo Institucion está en la aplicación 'registry'
from registry.models import Institucion


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
class ParticipanteRegistrationForm(forms.ModelForm):
    # Campo adicional para calcular edad
    edad = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'readonly': 'readonly',
        'placeholder': 'Se calculará automáticamente'
    }))
    
    class Meta:
        model = Participante
        fields = [
            'cedula', 'nombres', 'apellidos', 'fecha_nacimiento', 'sexo',
            'codigo_area', 'numero_telefono','direccion', 'estado', 'municipio', 'institucion', 
            'grado_escolar', 'nombre_escuela', 'nombre_representante', 'cedula_representante',
            'codigo_area_representante',
            'numero_telefono_representante', 'email_representante'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'onchange': 'calcularEdad()'
            }),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'estado': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'cargarMunicipios()'
            }),
            'municipio': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_municipio'  # Asegurar que tenga el ID correcto
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if field_name not in ['fecha_nacimiento', 'estado', 'municipio']:
                field.widget.attrs['class'] = 'form-control'
        
        # Ordenar estados y municipios alfabéticamente
        self.fields['estado'].queryset = Estado.objects.all().order_by('nombre')
        
        # TEMPORAL: Cargar todos los municipios
        self.fields['municipio'].queryset = Municipio.objects.all().order_by('estado__nombre', 'nombre')
        
        self.fields['institucion'].queryset = Institucion.objects.all().order_by('nombre')
        
        # Hacer campos de representante no requeridos inicialmente
        self.fields['nombre_representante'].required = False
        self.fields['cedula_representante'].required = False
        # users/forms.py (LÍNEA CORREGIDA)
        self.fields['codigo_area_representante'].required = False 
        self.fields['numero_telefono_representante'].required = False
        self.fields['email_representante'].required = False
    

    def clean(self):
        cleaned_data = super().clean()
        
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        
        edad_calculada = None
        if fecha_nacimiento:
            # Lógica para calcular la edad en el backend
            today = date.today()
            edad_calculada = today.year - fecha_nacimiento.year - (
                (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
            )
            
            # Re-validación de edad mínima (la que te dio error antes)
            if edad_calculada < 4: 
                self.add_error('fecha_nacimiento', 'El participante debe tener al menos 4 años para registrarse.')

        # Lógica para campos del representante
        
        # Usamos 18 si no pudimos calcular la edad (asumimos adulto para no requerir representante)
        es_menor = edad_calculada is not None and edad_calculada < 18
        
        if es_menor:
            # Los campos del representante (nombre, cedula, telefono, email) se hacen obligatorios

            requeridos = {
                'nombre_representante': 'Nombre del representante',
                'cedula_representante': 'Cédula del representante',
                'codigo_area_representante': 'Código de área del representante',
                'numero_telefono_representante': 'Número de teléfono del representante',
                'email_representante': 'Email del representante',
            }

            for field_name, friendly_name in requeridos.items():
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, f'{friendly_name} es requerido para menores de edad.')
                
        return cleaned_data


class InstitucionRegistrationForm(forms.ModelForm):
    # 1. Definimos las opciones de códigos con una opción vacía al inicio
    CODIGO_AREA_CHOICES = [
        ('', 'Cod'), # Opción vacía implícita
        ('0412', '0412'),
        ('0414', '0414'),
        ('0416', '0416'),
        ('0424', '0424'),
        ('0426', '0426'),
    ]

    CATEGORIA_CHOICES = (
        ('', 'Seleccione categoría'),
        ('publica', 'Pública'),
        ('privada', 'Privada'),
        ('fundacion', 'Fundación'),
        ('entidad', 'Entidad Gubernamental'),
    )

    # 2. Agregamos el campo de confirmación de contraseña
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': '********'}),
        required=True
    )
    
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': '********'}),
        required=True
    )

    # 3. Ajustamos campos existentes
    categoria = forms.ChoiceField(
        choices=CATEGORIA_CHOICES,
        label="Categoría",
        widget=forms.Select
    )

    codigo_area = forms.ChoiceField(
        choices=CODIGO_AREA_CHOICES,
        label="Cód.", # Etiqueta corta para el layout
        required=True,
    )

    numero_telefono = forms.CharField(max_length=7, label="Número", widget=forms.TextInput(attrs={'placeholder': '1234567'}))

    class Meta:
        model = Institucion
        
        fields = ('nombre', 'codigo', 'email', 'direccion', 'estado', 'telefono')
        widgets = {
            'telefono': forms.HiddenInput(), # Lo ocultamos porque lo armaremos con codigo_area + numero_telefono
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].widget.attrs['readonly'] = True
        self.fields['codigo'].required = False  
        self.fields['codigo'].initial = "SISTEMA GENERARÁ CÓDIGO"
        # 5. Configuración del FormHelper para el Layout "Tech"
        self.helper = FormHelper()
        self.helper.form_tag = False # Evita que crispy cree el tag <form> duplicado
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-8 mb-3'),
                Column('codigo', css_class='form-group col-md-4 mb-3'),
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('categoria', css_class='form-group col-md-6 mb-3'),
            ),
            'direccion',
            Row(
                Column('estado', css_class='form-group col-md-4 mb-3'),
                # El teléfono ahora se ve en una sola línea
                Column('codigo_area', css_class='form-group col-md-3 mb-3'),
                Column('numero_telefono', css_class='form-group col-md-5 mb-3'),
            ),
            Row(
                Column('password', css_class='form-group col-md-6 mb-3'),
                Column('confirm_password', css_class='form-group col-md-6 mb-3'),
            ),
        )

    # 6. Validación completa de contraseñas
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password:
            # Complejidad
            if len(password) < 8:
                self.add_error('password', "Mínimo 8 caracteres.")
            if not re.search('[A-Z]', password):
                self.add_error('password', "Debe incluir una mayúscula.")
            if not re.search('[0-9]', password):
                self.add_error('password', "Debe incluir un número.")

            # Coincidencia
            if password != confirm_password:
                self.add_error('confirm_password', "Las contraseñas no coinciden.")
        
        return cleaned_data