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
from .models import Estados, Municipios

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
    # 1. Definimos las opciones de códigos de operadoras
    CODIGO_AREA_CHOICES = [
        ('', '----'), 
        ('0412', '0412'), ('0414', '0414'), ('0416', '0416'),
        ('0422', '0422'), ('0424', '0424'), ('0426', '0426'),
    ]

    CATEGORIA_CHOICES = (
        ('', 'Seleccione categoría'),
        ('publica', 'Pública'),
        ('privada', 'Privada'),
        ('fundacion', 'Fundación'),
        ('entidad', 'Entidad Gubernamental'),
    )

    # Campos que NO están en el modelo pero se usan en el Form/Template
    rif = forms.CharField(label="RIF", widget=forms.TextInput(attrs={'placeholder': 'J-12345678-9'}))
    
    categoria = forms.ChoiceField(choices=CATEGORIA_CHOICES, label="Categoría")
    

    municipio = forms.ModelChoiceField(queryset=Municipios.objects.none()) 
    parroquia = forms.CharField(required=True, label="Parroquia")

    # Teléfono separado para validación
    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES, label="Cód.")
    numero_telefono = forms.CharField(
        max_length=7, 
        min_length=7, 
        label="Número", 
        widget=forms.TextInput(attrs={'placeholder': '1234567'})
    )

    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Institucion
        fields = ('nombre', 'rif', 'codigo', 'email', 'direccion', 'estado')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].widget.attrs['readonly'] = True
        self.fields['codigo'].required = False  
        self.fields['codigo'].initial = ""
        
      
        if 'estado' in self.data:
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['municipio'].queryset = Municipios.objects.filter(id_estado_id=estado_id).order_by('municipio')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.estado:
            self.fields['municipio'].queryset = self.instance.estado.municipios_set.order_by('municipio')

    def clean(self):
        cleaned_data = super().clean()
        rif = cleaned_data.get("rif")
        codigo = cleaned_data.get("codigo")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        num_tel = cleaned_data.get("numero_telefono")

        # 1. Validación RIF MPPE
        rif_mppe = "G200000010" 
        if rif == rif_mppe and not codigo:
            self.add_error('codigo', "Para el RIF del MPPE, el código de plantel es obligatorio.")

        # 2. Validación Teléfono (solo números)
        if num_tel and not num_tel.isdigit():
            self.add_error('numero_telefono', "El número debe contener solo caracteres numéricos.")

        # 3. Validación Seguridad Contraseña
        if password:
            if len(password) < 8:
                self.add_error('password', "Mínimo 8 caracteres.")
            if not re.search('[A-Z]', password):
                self.add_error('password', "Debe incluir al menos una mayúscula.")
            if not re.search('[0-9]', password):
                self.add_error('password', "Debe incluir al menos un número.")
            if password != confirm_password:
                self.add_error('confirm_password', "Las contraseñas no coinciden.")
        
        return cleaned_data