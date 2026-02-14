from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
import uuid

from registry.models import (
    Club,
    Dependencia,
    Estado,
    Institucion,
    Municipio,
    Parroquia,
    Participante,
)


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

    def clean_cedula(self):
        cedula = self.cleaned_data.get("cedula", "").strip().upper()
        if not re.match(r"^[VE]\d{6,8}$", cedula):
            raise ValidationError("Cédula inválida. Formato: V12345678 o E12345678")
        return cedula

    def clean_nombres(self):
        nombres = self.cleaned_data.get("nombres", "").strip()
        if not re.match(r"^[a-zA-ZÁ-ú\s]+$", nombres):
            raise ValidationError("El nombre solo puede contener letras.")
        if len(nombres) > 100:
            raise ValidationError("El nombre es demasiado largo.")
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get("apellidos", "").strip()
        if not re.match(r"^[a-zA-ZÁ-ú\s]+$", apellidos):
            raise ValidationError("El apellido solo puede contener letras.")
        if len(apellidos) > 100:
            raise ValidationError("El apellido es demasiado largo.")
        return apellidos

    def clean_numero_telefono(self):
        numero = self.cleaned_data.get("numero_telefono", "").strip()
        if not numero.isdigit() or len(numero) != 7:
            raise ValidationError("El número debe tener exactamente 7 dígitos.")
        return numero

    def clean_direccion(self):
        direccion = self.cleaned_data.get("direccion", "").strip()
        if len(direccion) > 500:
            raise ValidationError("La dirección es demasiado larga.")
        if re.search(r'[<>"\']', direccion):
            raise ValidationError("La dirección contiene caracteres no permitidos.")
        return direccion


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
        ("", "Codigo"),
        ("0412", "0412"),
        ("0414", "0414"),
        ("0416", "0416"),
        ("0424", "0424"),
        ("0426", "0426"),
        ("0212", "0212"),
        ("0281", "0281"),
    ]

    tipo_institucion = forms.ChoiceField(
        choices=[("", "Seleccione el tipo de institucion")]
        + Institucion.TIPO_INSTITUCION_CHOICES
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
    rif_numero = forms.CharField(max_length=10)  # 8 dígitos + guión + 1 dígito

    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES)
    numero_telefono = forms.CharField(max_length=7, min_length=7)

    password = forms.CharField(label="Contrasena", widget=forms.PasswordInput())
    confirm_password = forms.CharField(
        label="Confirmar Contrasena", widget=forms.PasswordInput()
    )
    terminos = forms.BooleanField(required=False)

    class Meta:
        model = Institucion
        fields = [
            "nombre",
            "email",
            "estado",
            "municipio",
            "parroquia",
            "direccion",
            "tipo_institucion",
            "naturaleza",
            "subcategoria",
            "codigo_mppe",
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
                self.fields["municipio"].queryset = Municipio.objects.filter(
                    estado_id=estado_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                pass

        if "municipio" in self.data:
            try:
                municipio_id = int(self.data.get("municipio"))
                self.fields["parroquia"].queryset = Parroquia.objects.filter(
                    municipio_id=municipio_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()

        # Sanitizar y validar campos de texto
        nombre = (cleaned_data.get("nombre") or "").strip()
        if nombre:
            if len(nombre) > 255:
                self.add_error("nombre", "El nombre no puede exceder 255 caracteres.")
            if re.search(r'[<>"\']', nombre):
                self.add_error("nombre", "El nombre contiene caracteres no permitidos.")
            cleaned_data["nombre"] = nombre

        # Validar email
        email = cleaned_data.get("email")
        if email and Institucion.objects.filter(email=email).exists():
            self.add_error("email", "Este correo ya está registrado.")

        # Validar dirección
        direccion = (cleaned_data.get("direccion") or "").strip()
        if direccion:
            if len(direccion) > 500:
                self.add_error(
                    "direccion", "La dirección no puede exceder 500 caracteres."
                )
            cleaned_data["direccion"] = direccion

        tipo = cleaned_data.get("tipo_institucion")
        naturaleza = cleaned_data.get("naturaleza")
        subcategoria = (cleaned_data.get("subcategoria") or "").strip().lower()
        dependencia = cleaned_data.get("dependencia_existente")
        nueva_dependencia = (cleaned_data.get("nueva_dependencia") or "").strip()

        # Sanitizar nueva_dependencia
        if nueva_dependencia:
            if len(nueva_dependencia) > 255:
                self.add_error(
                    "nueva_dependencia", "El nombre de la dependencia es muy largo."
                )
            if re.search(r'[<>"\']', nueva_dependencia):
                self.add_error(
                    "nueva_dependencia", "Contiene caracteres no permitidos."
                )

        rif_letra = cleaned_data.get("rif_letra")
        rif_numero = (cleaned_data.get("rif_numero") or "").strip().replace("-", "")

        codigo_area = cleaned_data.get("codigo_area")
        numero_telefono = (cleaned_data.get("numero_telefono") or "").strip()
        password = cleaned_data.get("password") or ""
        confirm_password = cleaned_data.get("confirm_password") or ""

        # Validar tipo de institución
        if tipo not in dict(Institucion.TIPO_INSTITUCION_CHOICES):
            self.add_error("tipo_institucion", "Tipo de institución inválido.")

        if tipo in {"educativa", "otra"} and not naturaleza:
            self.add_error("naturaleza", "Debe seleccionar la naturaleza.")

        if naturaleza and naturaleza not in dict(Institucion.NATURALEZA_CHOICES):
            self.add_error("naturaleza", "Naturaleza inválida.")

        if tipo == "educativa" and subcategoria not in {
            key for key, _ in self.SUBCATEGORIAS_EDUCATIVA
        }:
            self.add_error(
                "subcategoria", "Seleccione una subcategoria educativa valida."
            )

        if (
            tipo == "otra"
            and naturaleza == "privada"
            and subcategoria not in {key for key, _ in self.SUBCATEGORIAS_OTRA_PRIVADA}
        ):
            self.add_error("subcategoria", "Seleccione una subcategoria valida.")

        if (
            tipo == "otra"
            and naturaleza == "publica"
            and not (dependencia or nueva_dependencia)
        ):
            self.add_error(
                "dependencia_existente",
                "Debe seleccionar o crear una dependencia publica.",
            )

        # Validar RIF letra
        if rif_letra not in ["J", "G", "V", "E"]:
            self.add_error("rif_letra", "Letra de RIF inválida.")

        # Validar RIF número
        if not rif_numero.isdigit() or len(rif_numero) != 9:
            self.add_error(
                "rif_numero", "El RIF debe tener 9 dígitos (8 + 1 verificador)."
            )

        if tipo == "educativa":
            if f"{rif_letra}-{rif_numero[:8]}-{rif_numero[8]}" != "G-20000009-0":
                self.add_error("rif_numero", "Para MPPE use G-20000009-0.")
            if not cleaned_data.get("codigo_mppe"):
                self.add_error("codigo_mppe", "El codigo MPPE es obligatorio.")

        # Validar código de área
        if not codigo_area or codigo_area not in [
            c[0] for c in self.CODIGO_AREA_CHOICES if c[0]
        ]:
            self.add_error("codigo_area", "Seleccione un codigo de operadora válido.")

        # Validar número de teléfono
        if not numero_telefono.isdigit() or len(numero_telefono) != 7:
            self.add_error(
                "numero_telefono", "El numero debe tener exactamente 7 dígitos."
            )

        # Validar contraseña
        if len(password) < 8:
            self.add_error(
                "password", "La contrasena debe tener al menos 8 caracteres."
            )
        if len(password) > 128:
            self.add_error("password", "La contrasena es demasiado larga.")
        if not any(ch.isupper() for ch in password):
            self.add_error("password", "Debe incluir al menos una letra mayuscula.")
        if not any(ch.isdigit() for ch in password):
            self.add_error("password", "Debe incluir al menos un numero.")
        if not any(ch in '!@#$%^&*(),.?":{}|<>' for ch in password):
            self.add_error("password", "Debe incluir al menos un caracter especial.")

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
        instance.tipo_institucion = self.cleaned_data.get("tipo_institucion")
        instance.naturaleza = self.cleaned_data.get("naturaleza") or None
        instance.subcategoria = self.cleaned_data.get("subcategoria") or None
        instance.codigo_mppe = self.cleaned_data.get("codigo_mppe") or None

        # Nuevo flujo: el estado federado se gestiona como booleano (si/no).
        # Por defecto siempre se registra en False (No) hasta revision/aprobacion interna.
        instance.federado = False

        # IMPORTANTE: Asegurar que las instituciones nuevas estén desactivadas por defecto
        # Solo el admin puede activarlas desde el panel de administración
        if not instance.pk:  # Si es una nueva institución
            instance.activa = False
            instance.estatus = "pendiente"

        dependencia = self.cleaned_data.get("dependencia_existente")
        nueva_dependencia = (self.cleaned_data.get("nueva_dependencia") or "").strip()
        if nueva_dependencia:
            dependencia, _ = Dependencia.objects.get_or_create(nombre=nueva_dependencia)
        instance.dependencia_rel = dependencia
        instance.dependencia = dependencia.nombre if dependencia else None

        if not instance.codigo:
            instance.codigo = f"TEMP-{uuid.uuid4().hex[:8].upper()}"

        if commit:
            instance.save()
        return instance


class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["nombre", "descripcion", "ubicacion", "linea_1", "linea_2", "linea_3"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": 'Ej: Club de Robotica "Simon Rodriguez"',
                }
            ),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "ubicacion": forms.TextInput(attrs={"class": "form-control"}),
            "linea_1": forms.Select(attrs={"class": "form-select"}),
            "linea_2": forms.Select(attrs={"class": "form-select"}),
            "linea_3": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        l1 = cleaned_data.get("linea_1")
        l2 = cleaned_data.get("linea_2")
        l3 = cleaned_data.get("linea_3")

        lineas = [l for l in [l1, l2, l3] if l]
        if len(lineas) != len(set(lineas)):
            raise forms.ValidationError(
                "No puedes seleccionar la misma linea de investigacion mas de una vez."
            )

        return cleaned_data
