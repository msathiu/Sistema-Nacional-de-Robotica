from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile 
import uuid

from django.core.exceptions import ValidationError
from datetime import date
from registry.models import (
    Club,
    Dependencia,
    Estado,
    Institucion,
    Municipio,
    Parroquia,
    Participante,
)

# --- FORMULARIO DE SEDE REGIONAL (ADMINISTRACIÓN CENTRAL) ---
class SedeRegionalForm(forms.Form):
    # Credenciales de Acceso
    username = forms.CharField(
        label="Usuario", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: sede_miranda'})
    )
    email = forms.EmailField(
        label="Correo", 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'sede@correo.com'})
    )
    password = forms.CharField(
        label="Contraseña", 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'id': 'id_password1',
            'autocomplete': 'new-password'
        })
    )
    
    # Datos Personales del Encargado
    nombres = forms.CharField(
        label="Nombres", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres del encargado'})
    )
    apellidos = forms.CharField(
        label="Apellidos", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del encargado'})
    )
    cedula = forms.CharField(
        label="Cédula", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'V-12345678'})
    )
    
    # Teléfono (Formato Código + Número de 7 dígitos)
    CODIGOS_AREA = [
        ('0412', '0412'), ('0414', '0414'), ('0424', '0424'), 
        ('0416', '0416'), ('0426', '0426'), ('0212', '0212')
    ]
    codigo_area = forms.ChoiceField(
        choices=CODIGOS_AREA, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    numero_telefono = forms.CharField(
        max_length=7, 
        min_length=7, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '1234567',
            'pattern': '[0-9]{7}',
            'title': 'El número debe tener exactamente 7 dígitos'
        })
    )
    
    # Ubicación (Soberanía Territorial)
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all().order_by('nombre'), 
        empty_label="Seleccione Estado", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# --- FORMULARIOS DE USUARIOS ---
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

class ParticipanteModalEditForm(forms.ModelForm):
    CODIGOS_AREA = [
        ('0412', '0412'), ('0414', '0414'), ('0424', '0424'), 
        ('0416', '0416'), ('0426', '0426'), ('0212', '0212'),
    ]
    
    # Usamos widgets para añadir clases de Bootstrap directamente
    codigo_area = forms.ChoiceField(
        choices=CODIGOS_AREA,
        widget=forms.Select(attrs={'class': 'form-select border-0 shadow-sm'})
    )
    numero_telefono = forms.CharField(
        max_length=7, 
        min_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm', 'maxlength': '7'})
    )

    class Meta:
        model = Participante
        fields = ['nombres', 'apellidos', 'email', 'codigo_area', 'numero_telefono']

class ParticipanteRegistrationForm(forms.ModelForm):
    # Campo de edad calculado (readonly)
    edad = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "readonly": "readonly", "id": "id_edad_display"}
        ),
    )
    
    # Campo para el título/profesión (Dinámico en el HTML)
    profesion = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ej: Ingeniería, Licenciatura..."}
        )
    )

    class Meta:
        model = Participante
        fields = [
            "nombres", "apellidos", "cedula", "fecha_nacimiento", "sexo",
            "codigo_area", "numero_telefono", "direccion", "estado",
            "municipio", "grado_escolar", "nombre_escuela",
            "nombre_representante", "cedula_representante",
            "codigo_area_representante", "numero_telefono_representante",
            "email_representante",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "cedula": forms.TextInput(attrs={"placeholder": "Solo números"}),
            "cedula_representante": forms.TextInput(attrs={"placeholder": "Solo números"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Estilizar todos los campos (Bootstrap 5)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
        
        # Uso de form-select para desplegables (mejor estética en BS5)
        for select_field in ['estado', 'municipio', 'parroquia', 'sexo', 'codigo_area', 'codigo_area_representante']:
            if select_field in self.fields:
                self.fields[select_field].widget.attrs.update({"class": "form-select"})

        # 2. Cargar el QuerySet inicial de Estados
        if 'estado' in self.fields:
            self.fields["estado"].queryset = Estado.objects.all().order_by("nombre")

        # 3. Lógica de encadenamiento dinámico (Seguro contra KeyError)
        
        # PRIORIDAD A: Datos enviados en el POST
        if 'municipio' in self.fields and self.data.get('estado'):
            try:
                estado_id = self.data.get('estado')
                self.fields['municipio'].queryset = Municipio.objects.filter(estado_id=estado_id).order_by('nombre')
            except (ValueError, TypeError):
                self.fields['municipio'].queryset = Municipio.objects.none()
                
        # PRIORIDAD B: Datos de la instancia al EDITAR
        elif self.instance.pk and hasattr(self.instance, 'estado') and self.instance.estado:
            if 'municipio' in self.fields:
                self.fields['municipio'].queryset = Municipio.objects.filter(
                    estado=self.instance.estado
                ).order_by('nombre')
            
            # Verificación de Parroquia (Solo si el campo existe en el Form y el Modelo)
            if 'parroquia' in self.fields and hasattr(self.instance, 'municipio') and self.instance.municipio:
                # Nota: Asegúrate de tener el modelo Parroquia importado
                try:
                    from .models import Parroquia
                    self.fields['parroquia'].queryset = Parroquia.objects.filter(
                        municipio=self.instance.municipio
                    ).order_by('nombre')
                except ImportError:
                    pass
        
        # PRIORIDAD C: Carga inicial limpia (GET)
        else:
            if 'municipio' in self.fields:
                self.fields["municipio"].queryset = Municipio.objects.none()
            if 'parroquia' in self.fields:
                self.fields["parroquia"].queryset = Municipio.objects.none() # O Parroquia.objects.none()

    def clean_fecha_nacimiento(self):
        fecha_nac = self.cleaned_data.get("fecha_nacimiento")
        if fecha_nac:
            today = date.today()
            edad = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
            
            if edad < 3:
                raise ValidationError("El participante debe tener al menos 3 años de edad.")
        return fecha_nac
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_nac = cleaned_data.get("fecha_nacimiento")
        
        if fecha_nac:
            today = date.today()
            edad = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
            
            # Lógica para Menores de Edad
            if edad < 18:
                campos_rep = [
                    'nombre_representante', 'cedula_representante', 
                    'codigo_area_representante', 'numero_telefono_representante', 
                    'email_representante'
                ]
                for campo in campos_rep:
                    if not cleaned_data.get(campo):
                        self.add_error(campo, "Este campo es obligatorio para menores de edad.")
        
        return cleaned_data

# --- FORMULARIO DE INSTITUCIONES ---
class InstitucionRegistrationForm(forms.ModelForm):
    SUBCATEGORIAS_EDUCATIVA = [
        ("preescolar", "Preescolar"),
        ("primaria", "Primaria (1ra y 2da etapa)"),
        ("secundaria", "Secundaria (3ra etapa)"),
        ("media_general", "Media General"),
        ("media_tecnica", "Media Tecnica"),
    ]
    SUBCATEGORIAS_OTRA_PRIVADA = [
        ("empresa", "Empresa"),
        ("fundacion", "Fundacion"),
    ]

    RIF_PREFIJO_CHOICES = [("J", "J"), ("G", "G"), ("V", "V"), ("E", "E")]
    CODIGO_AREA_CHOICES = [
        ("", "Codigo"), ("0412", "0412"), ("0414", "0414"), ("0416", "0416"),
        ("0424", "0424"), ("0426", "0426"), ("0212", "0212"), ("0281", "0281"),
    ]

    tipo_institucion = forms.ChoiceField(
        choices=[("", "Seleccione el tipo de institucion")] + Institucion.TIPO_INSTITUCION_CHOICES
    )
    naturaleza = forms.ChoiceField(
        choices=[("", "Seleccione naturaleza")] + Institucion.NATURALEZA_CHOICES,
        required=False,
    )
    subcategoria = forms.CharField(max_length=120, required=False)
    dependencia_existente = forms.ModelChoiceField(
        queryset=Dependencia.objects.filter(activa=True).order_by("nombre"),
        required=False,
        empty_label="Busque o seleccione una dependencia",
    )
    nueva_dependencia = forms.CharField(max_length=255, required=False)
    rif_letra = forms.ChoiceField(choices=RIF_PREFIJO_CHOICES)
    rif_numero = forms.CharField(max_length=10)
    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES)
    numero_telefono = forms.CharField(max_length=7, min_length=7)
    password = forms.CharField(label="Contrasena", widget=forms.PasswordInput())
    confirm_password = forms.CharField(label="Confirmar Contrasena", widget=forms.PasswordInput())
    terminos = forms.BooleanField(required=False)

    class Meta:
        model = Institucion
        fields = [
            "nombre", "email", "estado", "municipio", "parroquia",
            "direccion", "tipo_institucion", "naturaleza", "subcategoria", "codigo_mppe",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control form-select"}),
            "municipio": forms.Select(attrs={"class": "form-control form-select"}),
            "parroquia": forms.Select(attrs={"class": "form-control form-select"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "codigo_mppe": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado"].queryset = Estado.objects.order_by("nombre")
        self.fields["municipio"].queryset = Municipio.objects.none()
        self.fields["parroquia"].queryset = Parroquia.objects.none()

        if "estado" in self.data:
            try:
                estado_id = int(self.data.get("estado"))
                self.fields["municipio"].queryset = Municipio.objects.filter(estado_id=estado_id).order_by("nombre")
            except (ValueError, TypeError): pass

        if "municipio" in self.data:
            try:
                municipio_id = int(self.data.get("municipio"))
                self.fields["parroquia"].queryset = Parroquia.objects.filter(municipio_id=municipio_id).order_by("nombre")
            except (ValueError, TypeError): pass

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password") or ""
        confirm_password = cleaned_data.get("confirm_password") or ""
        # Validaciones de seguridad de contraseña
        if len(password) < 8:
            self.add_error("password", "La contrasena debe tener al menos 8 caracteres.")
        if not any(ch.isupper() for ch in password):
            self.add_error("password", "Debe incluir al menos una letra mayuscula.")
        if not any(ch.isdigit() for ch in password):
            self.add_error("password", "Debe incluir al menos un numero.")
        if password != confirm_password:
            self.add_error("confirm_password", "Las contrasenas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        rif_letra = self.cleaned_data.get("rif_letra")
        rif_numero = self.cleaned_data.get("rif_numero").replace("-", "")
        codigo_area = self.cleaned_data.get("codigo_area")
        numero_telefono = self.cleaned_data.get("numero_telefono")
        instance.rif = f"{rif_letra}-{rif_numero[:8]}-{rif_numero[8]}"
        instance.telefono_codigo = codigo_area
        instance.telefono_numero = numero_telefono
        instance.telefono = f"{codigo_area}{numero_telefono}"
        instance.federado = False
        if not instance.pk:
            instance.activa = False
            instance.estatus = 'pendiente'
        dependencia = self.cleaned_data.get("dependencia_existente")
        nueva_dependencia = (self.cleaned_data.get("nueva_dependencia") or "").strip()
        if nueva_dependencia:
            dependencia, _ = Dependencia.objects.get_or_create(nombre=nueva_dependencia)
        instance.dependencia_rel = dependencia
        instance.dependencia = dependencia.nombre if dependencia else None
        if not instance.codigo:
            instance.codigo = f"TEMP-{uuid.uuid4().hex[:8].upper()}"
        if commit: instance.save()
        return instance


# --- FORMULARIO DE CLUBES ---
class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['nombre', 'descripcion', 'ubicacion', 'linea_1', 'linea_2', 'linea_3']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Club de Robotica "Simon Rodriguez"'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'linea_1': forms.Select(attrs={'class': 'form-select'}),
            'linea_2': forms.Select(attrs={'class': 'form-select'}),
            'linea_3': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        l1 = cleaned_data.get('linea_1')
        l2 = cleaned_data.get('linea_2')
        l3 = cleaned_data.get('linea_3')
        lineas = [l for l in [l1, l2, l3] if l]
        if len(lineas) != len(set(lineas)):
            raise forms.ValidationError("No puedes seleccionar la misma linea de investigacion mas de una vez.")
        return cleaned_data