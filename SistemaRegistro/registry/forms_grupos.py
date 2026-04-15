"""
Formulario profesional para gestión de equipos (grupos).

Características:
- Validaciones robustas
- Generación automática de código
- Integración con tutores y participantes
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Grupo, Tutor, Participante


class GrupoForm(forms.ModelForm):
    """Formulario para crear y editar equipos."""

    class Meta:
        model = Grupo
        fields = [
            "nombre",
            "criterio",
            "edad_desde",
            "edad_hasta",
            "nivel_educativo",
            "nombre_proyecto",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Equipo Robótica Avanzada",
                    "maxlength": "150",
                }
            ),
            "criterio": forms.Select(
                attrs={"class": "form-select", "id": "id_criterio"}
            ),
            "edad_desde": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: 8",
                    "min": "4",
                    "max": "99",
                }
            ),
            "edad_hasta": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: 12",
                    "min": "4",
                    "max": "99",
                }
            ),
            "nivel_educativo": forms.Select(attrs={"class": "form-select"}),
            "nombre_proyecto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Robot Seguidor de Línea",
                    "maxlength": "200",
                }
            ),
        }
        labels = {
            "nombre": "Nombre del Equipo",
            "criterio": "Criterio de Agrupación",
            "edad_desde": "Edad Desde",
            "edad_hasta": "Edad Hasta",
            "nivel_educativo": "Nivel Educativo",
            "nombre_proyecto": "Nombre del Proyecto",
        }
        help_texts = {
            "nombre": "Nombre identificativo del equipo",
            "criterio": "Criterio utilizado para formar el equipo",
            "edad_desde": "Edad mínima de los participantes",
            "edad_hasta": "Edad máxima de los participantes",
            "nivel_educativo": "Grado escolar del equipo",
            "nombre_proyecto": "Nombre del proyecto que desarrollará el equipo",
        }

    def __init__(self, *args, **kwargs):
        self.institucion = kwargs.pop("institucion", None)
        self.usuario = kwargs.pop("usuario", None)
        super().__init__(*args, **kwargs)

        # Hacer campos requeridos
        self.fields["nombre"].required = True
        self.fields["criterio"].required = True

        # Campos condicionales no requeridos por defecto
        self.fields["edad_desde"].required = False
        self.fields["edad_hasta"].required = False
        self.fields["nivel_educativo"].required = False
        self.fields["nombre_proyecto"].required = False

    def clean(self):
        """Validaciones personalizadas del formulario."""
        cleaned_data = super().clean()
        criterio = cleaned_data.get("criterio")

        # Validar campos según criterio
        if criterio == "edad":
            edad_desde = cleaned_data.get("edad_desde")
            edad_hasta = cleaned_data.get("edad_hasta")

            if not edad_desde:
                self.add_error(
                    "edad_desde", 'Este campo es obligatorio para criterio "Por Edad"'
                )
            if not edad_hasta:
                self.add_error(
                    "edad_hasta", 'Este campo es obligatorio para criterio "Por Edad"'
                )

            if edad_desde and edad_hasta:
                if edad_desde > edad_hasta:
                    self.add_error(
                        "edad_desde", "La edad desde no puede ser mayor que edad hasta"
                    )
                if edad_desde < 4:
                    self.add_error("edad_desde", "La edad mínima debe ser 4 años")

        elif criterio == "nivel":
            nivel_educativo = cleaned_data.get("nivel_educativo")
            if not nivel_educativo:
                self.add_error(
                    "nivel_educativo",
                    'Este campo es obligatorio para criterio "Por Nivel Educativo"',
                )

        elif criterio == "proyecto":
            nombre_proyecto = cleaned_data.get("nombre_proyecto", "").strip()
            if not nombre_proyecto:
                self.add_error(
                    "nombre_proyecto",
                    'Este campo es obligatorio para criterio "Por Proyecto"',
                )
            else:
                cleaned_data["nombre_proyecto"] = nombre_proyecto

        return cleaned_data

    def clean_nombre(self):
        """Validar nombre del equipo."""
        nombre = self.cleaned_data.get("nombre", "").strip()

        if not nombre:
            raise ValidationError("El nombre del equipo es obligatorio")

        if len(nombre) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres")

        # Verificar unicidad dentro de la institución
        if self.institucion:
            queryset = Grupo.objects.filter(
                nombre__iexact=nombre, institucion=self.institucion, activo=True
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f"Ya existe un equipo con el nombre '{nombre}' en tu institución"
                )

        return nombre

    def save(self, commit=True):
        """Guardar equipo con código automático."""
        grupo = super().save(commit=False)

        # Generar código si es nuevo usando el método del modelo
        # para mantener consistencia con el formato EQP-YYMMDD-6CHARS
        if not grupo.codigo:
            grupo.codigo = grupo.generar_codigo_grupo()

        # Asignar institución y usuario
        if self.institucion:
            grupo.institucion = self.institucion
        if self.usuario:
            grupo.usuario_creador = self.usuario

        if commit:
            grupo.save()
            self.save_m2m()

        return grupo
