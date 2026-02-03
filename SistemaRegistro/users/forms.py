import re
from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Importación de modelos desde tu app 'registry'
from registry.models import Participante, Institucion, Estado, Municipio

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    class Meta:
        model = User
        fields = ('username', 'email')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class ParticipanteRegistrationForm(forms.ModelForm):
    edad = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'readonly': 'readonly'
    }))
    class Meta:
        model = Participante
        fields = [
            'cedula', 'nombres', 'apellidos', 'fecha_nacimiento', 'sexo',
            'codigo_area', 'numero_telefono','direccion', 'estado', 'municipio', 'institucion', 
            'grado_escolar', 'nombre_escuela', 'nombre_representante', 'cedula_representante',
            'codigo_area_representante', 'numero_telefono_representante', 'email_representante'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'onchange': 'calcularEdad()'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['estado'].queryset = Estado.objects.all().order_by('nombre')
        self.fields['municipio'].queryset = Municipio.objects.none()

class InstitucionRegistrationForm(forms.ModelForm):
    # CHOICES
    RIF_LETRA_CHOICES = [('J', 'J - '), ('G', 'G - '), ('V', 'V - '), ('E', 'E - '), ('P', 'P - ')]
    CODIGO_AREA_CHOICES = [('', '----'), ('0412', '0412'), ('0414', '0414'), ('0416', '0416'), ('0424', '0424'), ('0426', '0426')]
    CATEGORIA_CHOICES = [('', 'Seleccione categoría'), ('publica', 'Pública'), ('privada', 'Privada'), ('fundacion', 'Fundación'), ('entidad', 'Entidad Gubernamental')]
    PROCEDENCIA_CHOICES = [
    ('', 'Seleccione Procedencia'),
    ('publica', 'Instituciones Educativas Públicas'),
    ('gubernamental', 'Entidad Gubernamental / Fundación dependiente del Estado'),
    ('privada', 'Institución Privada'),
    ]

    # Campos manuales (Para el Template y guardado manual)
    rif_letra = forms.ChoiceField(choices=RIF_LETRA_CHOICES, label="Letra RIF")
    rif_numero = forms.CharField(max_length=15, label="Número RIF")
    categoria = forms.ChoiceField(choices=CATEGORIA_CHOICES, label="Categoría")
    codigo_mppe = forms.CharField(required=False, label="Código MPPE / Plantel")
    institucion_procedencia = forms.ChoiceField(choices=PROCEDENCIA_CHOICES, label="Institución de Procedencia")
    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES, label="Cód.")
    numero_telefono = forms.CharField(max_length=7, min_length=7, label="Número")
    parroquia = forms.CharField(required=True, label="Parroquia")
    municipio = forms.ModelChoiceField(queryset=Municipio.objects.none(), label="Municipio", required=True)
    
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Institucion
        fields = ['nombre', 'tipo_federado', 'email', 'codigo', 'estado', 'direccion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].widget.attrs['readonly'] = True
        self.fields['codigo'].required = False  
        
        if 'estado' in self.data:
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['municipio'].queryset = Municipio.objects.filter(id_estado_id=estado_id).order_by('nombre')
            except (ValueError, TypeError): pass
        elif self.instance.pk and self.instance.estado:
            self.fields['municipio'].queryset = Municipio.objects.filter(id_estado=self.instance.estado).order_by('nombre')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Unificar campos especiales
        instance.rif = f"{self.cleaned_data.get('rif_letra')}-{self.cleaned_data.get('rif_numero')}"
        instance.telefono = f"{self.cleaned_data.get('codigo_area')}{self.cleaned_data.get('numero_telefono')}"
        instance.categoria = self.cleaned_data.get('categoria')
        instance.codigo_mppe = self.cleaned_data.get('codigo_mppe')
        instance.institucion_procedencia = self.cleaned_data.get('institucion_procedencia')
        instance.parroquia = self.cleaned_data.get('parroquia')
        # Si el modelo Institucion tiene FK a municipio:
        if hasattr(instance, 'municipio'):
            instance.municipio = self.cleaned_data.get('municipio')
        if commit:
            instance.save()
        return instance