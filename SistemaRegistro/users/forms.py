from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from registry.models import Club
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
    # --- CHOICES ORGANIZADOS POR CATEGORÍAS ---
    TIPO_USUARIO_CHOICES = [
        ('', 'Seleccione Tipo de Usuario'),
        ('Institución Educativa (MPPE) - Pública', [
            ('mppe_pub_pre', 'Preescolar '),
            ('mppe_pub_pri', 'Primaria 1ra y 2da etapa '),
            ('mppe_pub_sec', 'Secundaria 3ra etapa '),
            ('mppe_pub_gen', 'Media General '),
            ('mppe_pub_tec', 'Media Técnica '),
        ]),
        ('Institución Educativa (MPPE) - Privada', [
            ('mppe_priv_pre', 'Preescolar '),
            ('mppe_priv_pri', 'Primaria 1ra y 2da etapa '),
            ('mppe_priv_sec', 'Secundaria 3ra etapa '),
            ('mppe_priv_gen', 'Media General '),
            ('mppe_priv_tec', 'Media Técnica '),
        ]),
        ('Otras Instituciones - Pública', [
            ('otra_pub_dep', 'Dependencia Gubernamental / Estado'),
        ]),
        ('Otras Instituciones - Privada', [
            ('otra_priv_emp', 'Empresa Privada'),
            ('otra_priv_fun', 'Fundación Privada'),
        ]),
        ('Particular', [
            ('particular_nat', 'Persona Natural'),
        ]),
    ]

    RIF_LETRA_CHOICES = [
        ("J", "J - "),
        ("G", "G - "),
        ("V", "V - "),
        ("E", "E - "),
        ("P", "P - "),
    ]
    
    CODIGO_AREA_CHOICES = [
        ("", "----"),
        ("0412", "0412"),
        ("0414", "0414"),
        ("0416", "0416"),
        ("0424", "0424"),
        ("0426", "0426"),
    ]
    
    CATEGORIA_CHOICES = [
        ("", "Seleccione categoría"),
        ("publica", "Pública"),
        ("privada", "Privada"),
        ("fundacion", "Fundación"),
        ("entidad", "Entidad Gubernamental"),
    ]
    
    PROCEDENCIA_CHOICES = [
        ("", "Seleccione Procedencia"),
        ("publica", "Instituciones Educativas Públicas"),
        ("gubernamental", "Entidad Gubernamental / Fundación dependiente del Estado"),
        ("privada", "Institución Privada"),
    ]

    # --- CAMPOS MANUALES (Lógica de Negocio) ---
    tipo_federado = forms.ChoiceField(
        choices=TIPO_USUARIO_CHOICES,
        label="Tipo de Usuario",
        widget=forms.Select(attrs={'class': 'form-control form-select'})
    )
    
    rif_letra = forms.ChoiceField(choices=RIF_LETRA_CHOICES, label="Letra RIF")
    rif_numero = forms.CharField(max_length=15, label="Número RIF")
    categoria = forms.ChoiceField(choices=CATEGORIA_CHOICES, label="Categoría")
    codigo_mppe = forms.CharField(required=False, label="Código MPPE / Plantel")
    institucion_procedencia = forms.ChoiceField(
        choices=PROCEDENCIA_CHOICES, label="Institución de Procedencia"
    )
    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES, label="Cód.")
    numero_telefono = forms.CharField(max_length=7, min_length=7, label="Número")

    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(
        label="Confirmar Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Institucion
        fields = [
            "nombre",
            "tipo_federado",
            "email",
            "estado",
            "municipio",
            "parroquia",
            "direccion",
        ]
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

        # 1. Queryset de municipios dinámico
        if "estado" in self.data:
            try:
                estado_id = int(self.data.get("estado"))
                self.fields["municipio"].queryset = Municipio.objects.filter(
                    estado_id=estado_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["municipio"].queryset = Municipio.objects.none()
        else:
            self.fields["municipio"].queryset = Municipio.objects.none()

        # 2. Queryset de parroquias dinámico
        if "municipio" in self.data:
            try:
                municipio_id = int(self.data.get("municipio"))
                self.fields["parroquia"].queryset = Parroquia.objects.filter(
                    municipio_id=municipio_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                self.fields["parroquia"].queryset = Parroquia.objects.none()
        else:
            self.fields["parroquia"].queryset = Parroquia.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Concatenación de datos procesados
        instance.rif = f"{self.cleaned_data.get('rif_letra')}-{self.cleaned_data.get('rif_numero')}"
        instance.telefono = f"{self.cleaned_data.get('codigo_area')}{self.cleaned_data.get('numero_telefono')}"

        # Asignación de campos manuales que no están en el Meta.fields directo
        instance.categoria = self.cleaned_data.get("categoria")
        instance.codigo_mppe = self.cleaned_data.get("codigo_mppe")
        instance.institucion_procedencia = self.cleaned_data.get("institucion_procedencia")
        
        # Guardar el tipo de usuario en el campo tipo_federado del modelo
        instance.tipo_federado = self.cleaned_data.get("tipo_federado")

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