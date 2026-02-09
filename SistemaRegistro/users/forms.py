from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from registry.models import Club
import uuid
# Importación de modelos desde tu app 'registry'
from registry.models import Estado, Institucion, Municipio, Parroquia, Participante


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


class ParticipanteRegistrationForm(forms.ModelForm):
    edad = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "readonly": "readonly"}
        ),
    )

    class Meta:
        model = Participante
        fields = [
            "cedula",
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "sexo",
            "codigo_area",
            "numero_telefono",
            "direccion",
            "estado",
            "municipio",
            "institucion",
            "grado_escolar",
            "nombre_escuela",
            "nombre_representante",
            "cedula_representante",
            "codigo_area_representante",
            "numero_telefono_representante",
            "email_representante",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "onchange": "calcularEdad()"}
            ),
            "direccion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
        self.fields["estado"].queryset = Estado.objects.all().order_by("nombre")
        self.fields["municipio"].queryset = Municipio.objects.none()

class InstitucionRegistrationForm(forms.ModelForm):
    # --- CHOICES ---
    TIPO_USUARIO_CHOICES = [
        ('', 'Seleccione Tipo de Usuario'),
        ('Institución Educativa (MPPE) - Pública', [
            ('mppe_pub_pre', 'Preescolar '), ('mppe_pub_pri', 'Primaria '),
            ('mppe_pub_sec', 'Secundaria '), ('mppe_pub_gen', 'Media General '),
            ('mppe_pub_tec', 'Media Técnica '),
        ]),
        ('Institución Educativa (MPPE) - Privada', [
            ('mppe_priv_pre', 'Preescolar '), ('mppe_priv_pri', 'Primaria '),
            ('mppe_priv_sec', 'Secundaria '), ('mppe_priv_gen', 'Media General '),
            ('mppe_priv_tec', 'Media Técnica '),
        ]),
        ('Otras Instituciones - Pública', [
            ('otra_pub_dep', 'Dependencia Gubernamental / Estado'),
        ]),
        ('Otras Instituciones - Privada', [
            ('otra_priv_emp', 'Empresa Privada'), ('otra_priv_fun', 'Fundación Privada'),
        ]),
        ('Particular', [
            ('particular_nat', 'Persona Natural'),
        ]),
    ]

    PROCEDENCIA_CHOICES = [
        ("", "Seleccione Procedencia"),
        ("publica", "Instituciones Educativas Públicas"),
        ("gubernamental", "Entidad Gubernamental / Fundación dependiente del Estado"),
        ("privada", "Institución Privada"),
    ]

    CATEGORIA_CHOICES = [
        ("", "Seleccione categoría"),
        ("publica", "Pública"),
        ("privada", "Privada"),
        ("fundacion", "Fundación"),
        ("entidad", "Entidad Gubernamental"),
    ]

    RIF_LETRA_CHOICES = [("J", "J"), ("G", "G"), ("V", "V"), ("E", "E"), ("P", "P")]
    CODIGO_AREA_CHOICES = [("", "----"), ("0412", "0412"), ("0414", "0414"), ("0416", "0416"), ("0424", "0424"), ("0426", "0426")]

    # --- CAMPOS QUE TU HTML EXIGE (Declararlos aquí evita el CrispyError) ---
    tipo_federado = forms.ChoiceField(
        choices=TIPO_USUARIO_CHOICES,
        label="Tipo de Usuario",
        widget=forms.Select(attrs={'class': 'form-control form-select'})
    )
    categoria = forms.ChoiceField(choices=CATEGORIA_CHOICES, label="Categoría", required=False)
    institucion_procedencia = forms.ChoiceField(choices=PROCEDENCIA_CHOICES, label="Institución de Procedencia", required=False)
    codigo_mppe = forms.CharField(required=False, label="Código MPPE / Plantel")
    
    rif_letra = forms.ChoiceField(choices=RIF_LETRA_CHOICES, label="Letra")
    rif_numero = forms.CharField(max_length=15, label="Número RIF")
    
    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES, label="Cód.")
    numero_telefono = forms.CharField(max_length=7, min_length=7, label="Número")

    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput())
    confirm_password = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput())

    class Meta:
        model = Institucion
        fields = ["nombre", "email", "estado", "municipio", "parroquia", "direccion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control form-select"}),
            "municipio": forms.Select(attrs={"class": "form-control form-select"}),
            "parroquia": forms.Select(attrs={"class": "form-control form-select"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lógica dinámica de estados/municipios (se mantiene igual)
        if "estado" in self.data:
            try:
                self.fields["municipio"].queryset = Municipio.objects.filter(estado_id=int(self.data.get("estado"))).order_by("nombre")
            except: pass
        if "municipio" in self.data:
            try:
                self.fields["parroquia"].queryset = Parroquia.objects.filter(municipio_id=int(self.data.get("municipio"))).order_by("nombre")
            except: pass

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            self.add_error("confirm_password", "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 1. Procesar RIF y Teléfono
        instance.rif = f"{self.cleaned_data.get('rif_letra')}-{self.cleaned_data.get('rif_numero')}"
        instance.telefono = f"{self.cleaned_data.get('codigo_area')}{self.cleaned_data.get('numero_telefono')}"
        
        # 2. Asignar TIPO y DEPENDENCIA
        val_tipo = self.cleaned_data.get("tipo_federado")
        instance.tipo_federado = val_tipo
        instance.dependencia = val_tipo
        
        # 3. SOLUCIÓN AL ERROR DE CÓDIGO:
        # Si el código está vacío, le asignamos uno temporal basado en UUID
        # para que no choque con otros registros pendientes.
        if not instance.codigo:
            instance.codigo = f"TEMP-{uuid.uuid4().hex[:8].upper()}"

        # ... resto de tu lógica de dirección ...
        info_extra = f" | Cat: {self.cleaned_data.get('categoria')} | Proc: {self.cleaned_data.get('institucion_procedencia')}"
        instance.direccion += info_extra

        if commit:
            instance.save()
        return instance
    
class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['nombre', 'descripcion', 'ubicacion', 'linea_1', 'linea_2', 'linea_3']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Club de Robótica "Simon Rodriguez"'}),
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

        # Validación: No permitir líneas duplicadas
        lineas = [l for l in [l1, l2, l3] if l]
        if len(lineas) != len(set(lineas)):
            raise forms.ValidationError("No puedes seleccionar la misma línea de investigación más de una vez.")
        
        return cleaned_data