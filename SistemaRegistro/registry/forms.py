from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Club,
    ClubLineaInvestigacion,
    Estado,
    Institucion,
    LineaInvestigacion,
    Municipio,
    Parroquia,
    Participante,
)


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


class ClubForm(forms.ModelForm):
    """Formulario para crear/editar clubes con líneas de investigación dinámicas."""
    
    # Campos para líneas de investigación (hasta 3)
    linea_investigacion_1 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True).order_by('orden', 'nombre'),
        required=True,
        label="Línea de Investigación 1 (Principal)",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    linea_investigacion_2 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True).order_by('orden', 'nombre'),
        required=False,
        label="Línea de Investigación 2 (Opcional)",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    linea_investigacion_3 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True).order_by('orden', 'nombre'),
        required=False,
        label="Línea de Investigación 3 (Opcional)",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, cargar las líneas existentes
        if self.instance and self.instance.pk:
            lineas_existentes = self.instance.club_lineas.select_related('linea').order_by('orden')
            
            for idx, club_linea in enumerate(lineas_existentes, start=1):
                field_name = f'linea_investigacion_{idx}'
                if field_name in self.fields:
                    self.fields[field_name].initial = club_linea.linea
    
    class Meta:
        model = Club
        fields = [
            'nombre',
            'siglas',
            'descripcion',
            'ubicacion',
            'fecha_fundacion',
            'estado_vinculacion',
            'cupo_maximo',
            'requisitos',
            'documento_legal',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Club de Robótica Educativa'}),
            'siglas': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: CRE', 'maxlength': '10'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe los objetivos y actividades del club...'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección física del club'}),
            'fecha_fundacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado_vinculacion': forms.Select(attrs={'class': 'form-select'}),
            'cupo_maximo': forms.NumberInput(attrs={'class': 'form-control', 'value': '10', 'min': '1', 'max': '100'}),
            'requisitos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Requisitos para que una institución pueda ser miembro...'}),
            'documento_legal': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Número de documento legal, resolución, etc.'}),
        }
    
    def save(self, commit=True):
        club = super().save(commit=False)
        
        # Guardar el club primero si commit=True
        if commit:
            club.save()
            
            # Limpiar líneas existentes
            club.club_lineas.all().delete()
            
            # Guardar nuevas líneas
            from registry.models import ClubLineaInvestigacion
            
            lineas = [
                (self.cleaned_data.get('linea_investigacion_1'), 'principal', 1),
                (self.cleaned_data.get('linea_investigacion_2'), 'soporte', 2),
                (self.cleaned_data.get('linea_investigacion_3'), 'afines', 3),
            ]
            
            for linea, tipo, orden in lineas:
                if linea:
                    ClubLineaInvestigacion.objects.create(
                        club=club,
                        linea=linea,
                        tipo_linea=tipo,
                        orden=orden
                    )
        
        return club
    
    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.get('instance').pk if kwargs.get('instance') else None
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, cargar líneas existentes
        if self.instance.pk:
            lineas = self.instance.club_lineas.select_related('linea').order_by('orden')
            if lineas.exists():
                for i, club_linea in enumerate(lineas[:3], start=1):
                    field_name = f'linea_investigacion_{i}'
                    if field_name in self.fields:
                        self.fields[field_name].initial = club_linea.linea
    
    def clean(self):
        cleaned_data = super().clean()
        linea_1 = cleaned_data.get('linea_investigacion_1')
        linea_2 = cleaned_data.get('linea_investigacion_2')
        linea_3 = cleaned_data.get('linea_investigacion_3')
        
        # Validar que no se repitan líneas
        lineas = [l for l in [linea_1, linea_2, linea_3] if l]
        if len(lineas) != len(set(lineas)):
            raise ValidationError("No puede seleccionar la misma línea de investigación más de una vez.")
        
        return cleaned_data
    
    def save(self, commit=True):
        club = super().save(commit=commit)
        
        if commit:
            # Eliminar líneas existentes
            ClubLineaInvestigacion.objects.filter(club=club).delete()
            
            # Agregar nuevas líneas
            lineas_data = [
                (self.cleaned_data.get('linea_investigacion_1'), 'principal', 1),
                (self.cleaned_data.get('linea_investigacion_2'), 'soporte', 2),
                (self.cleaned_data.get('linea_investigacion_3'), 'afines', 3),
            ]
            
            for linea, tipo, orden in lineas_data:
                if linea:
                    ClubLineaInvestigacion.objects.create(
                        club=club,
                        linea=linea,
                        tipo_linea=tipo,
                        orden=orden
                    )
        
        return club
