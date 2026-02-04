from django import forms
from django.core.exceptions import ValidationError

from .models import Estado, Institucion, Municipio, Parroquia, Participante


class ParticipanteForm(forms.ModelForm):
    class Meta:
        model = Participante
        fields = [
            "cedula",
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "sexo",
            "email",
            "codigo_area",
            "numero_telefono",
            "direccion",
            "estado",
            "municipio",
            "institucion",
            "grado_escolar",
            "nombre_representante",
            "cedula_representante",
            "codigo_area_representante",
            "numero_telefono_representante",
            "email_representante",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "direccion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["municipio"].queryset = Municipio.objects.none()

        if "estado" in self.data:
            try:
                estado_id = int(self.data.get("estado"))
                self.fields["municipio"].queryset = Municipio.objects.filter(
                    estado_id=estado_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields[
                "municipio"
            ].queryset = self.instance.estado.municipio_set.order_by("nombre")


class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        # Agregamos municipio y parroquia porque son necesarios para el registro
        fields = [
            "nombre",
            "estado",
            "municipio",
            "parroquia",
            "direccion",
            "telefono",
            "email",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
            "municipio": forms.Select(attrs={"class": "form-control"}),
            "parroquia": forms.Select(attrs={"class": "form-control"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Configuración de Estados
        self.fields["estado"].queryset = Estado.objects.all().order_by("nombre")
        self.fields["estado"].empty_label = "Seleccione un estado"

        # 2. Lógica Dinámica para Municipio y Parroquia
        # Si el formulario es nuevo o no hay estado seleccionado en POST
        if "estado" not in self.data and not self.instance.pk:
            self.fields["municipio"].queryset = Municipio.objects.none()
            self.fields["parroquia"].queryset = Parroquia.objects.none()

        # Si estamos procesando un envío (POST) o editando una instancia
        elif "estado" in self.data or self.instance.pk:
            try:
                # Obtenemos el ID del estado del POST o de la instancia guardada
                estado_id = (
                    int(self.data.get("estado"))
                    if self.data.get("estado")
                    else self.instance.estado_id
                )
                self.fields["municipio"].queryset = Municipio.objects.filter(
                    estado_id=estado_id
                ).order_by("nombre")

                if "municipio" in self.data or self.instance.pk:
                    mun_id = (
                        int(self.data.get("municipio"))
                        if self.data.get("municipio")
                        else self.instance.municipio_id
                    )
                    self.fields["parroquia"].queryset = Parroquia.objects.filter(
                        municipio_id=mun_id
                    ).order_by("nombre")
            except (ValueError, TypeError):
                pass

    def clean(self):
        """Validación de integridad geográfica en el servidor"""
        cleaned_data = super().clean()
        estado = cleaned_data.get("estado")
        municipio = cleaned_data.get("municipio")
        parroquia = cleaned_data.get("parroquia")

        # Validar relación Estado -> Municipio
        if estado and municipio and municipio.estado != estado:
            raise ValidationError(
                {
                    "municipio": f"El municipio '{municipio}' no pertenece al estado '{estado}'."
                }
            )

        # Validar relación Municipio -> Parroquia
        if municipio and parroquia and parroquia.municipio != municipio:
            raise ValidationError(
                {
                    "parroquia": f"La parroquia '{parroquia}' no pertenece al municipio '{municipio}'."
                }
            )

        return cleaned_data
