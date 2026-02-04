from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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
    rif_letra = forms.ChoiceField(choices=RIF_LETRA_CHOICES, label="Letra RIF")
    rif_numero = forms.CharField(max_length=15, label="Número RIF")
    categoria = forms.ChoiceField(choices=CATEGORIA_CHOICES, label="Categoría")
    codigo_mppe = forms.CharField(required=False, label="Código MPPE / Plantel")
    institucion_procedencia = forms.ChoiceField(
        choices=PROCEDENCIA_CHOICES, label="Institución de Procedencia"
    )
    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES, label="Cód.")
    numero_telefono = forms.CharField(max_length=7, min_length=7, label="Número")

    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    confirm_password = forms.CharField(
        label="Confirmar Contraseña", widget=forms.PasswordInput
    )

    class Meta:
        model = Institucion
        # OJO: Se incluyeron municipio y parroquia en fields
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
            "tipo_federado": forms.Select(attrs={"class": "form-control form-select"}),
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
        elif self.instance.pk:
            self.fields[
                "municipio"
            ].queryset = self.instance.estado.municipios.all().order_by("nombre")
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
        elif self.instance.pk:
            self.fields[
                "parroquia"
            ].queryset = self.instance.municipio.parroquias.all().order_by("nombre")
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

        # Asignación de campos manuales
        instance.categoria = self.cleaned_data.get("categoria")
        instance.codigo_mppe = self.cleaned_data.get("codigo_mppe")
        instance.institucion_procedencia = self.cleaned_data.get(
            "institucion_procedencia"
        )

        if commit:
            instance.save()
        return instance
