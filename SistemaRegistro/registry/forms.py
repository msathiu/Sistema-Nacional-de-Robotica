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
    Tutor,
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener queryset de líneas de investigación activas
        lineas_qs = LineaInvestigacion.objects.filter(activa=True).order_by('orden', 'nombre')
        
        # Asignar queryset a cada campo
        self.fields['linea_investigacion_1'].queryset = lineas_qs
        self.fields['linea_investigacion_2'].queryset = lineas_qs
        self.fields['linea_investigacion_3'].queryset = lineas_qs
        
        # Verificar si hay líneas disponibles
        if not lineas_qs.exists():
            # Si no hay líneas, hacer el campo 1 opcional
            self.fields['linea_investigacion_1'].required = False
            self.fields['linea_investigacion_1'].empty_label = "No hay líneas disponibles - Contacte al administrador"
        else:
            self.fields['linea_investigacion_1'].empty_label = "Seleccione una línea"
        
        # Si estamos editando, cargar las líneas existentes
        if self.instance and self.instance.pk:
            lineas_existentes = self.instance.club_lineas.select_related('linea').order_by('orden')
            
            for idx, club_linea in enumerate(lineas_existentes, start=1):
                field_name = f'linea_investigacion_{idx}'
                if field_name in self.fields:
                    self.fields[field_name].initial = club_linea.linea
    
    # Campos para líneas de investigación (hasta 3)
    linea_investigacion_1 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.none(),
        required=True,
        label="Línea de Investigación 1 (Principal)",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    linea_investigacion_2 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.none(),
        required=False,
        label="Línea de Investigación 2 (Opcional)",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    linea_investigacion_3 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.none(),
        required=False,
        label="Línea de Investigación 3 (Opcional)",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
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
    
    def clean(self):
        cleaned_data = super().clean()
        
        linea_1 = cleaned_data.get('linea_investigacion_1')
        linea_2 = cleaned_data.get('linea_investigacion_2')
        linea_3 = cleaned_data.get('linea_investigacion_3')
        
        # Validar que la línea 1 sea obligatoria si hay líneas disponibles
        lineas_disponibles = LineaInvestigacion.objects.filter(activa=True).exists()
        if lineas_disponibles and not linea_1:
            raise ValidationError({
                'linea_investigacion_1': 'Debe seleccionar al menos una línea de investigación principal.'
            })
        
        # Validar que no se repitan líneas
        lineas = [l for l in [linea_1, linea_2, linea_3] if l]
        if len(lineas) != len(set(lineas)):
            raise ValidationError("No puede seleccionar la misma línea de investigación más de una vez.")
        
        return cleaned_data
    
    def save(self, commit=True):
        club = super().save(commit=commit)
        
        if commit:
            # Obtener las líneas del formulario
            linea_1 = self.cleaned_data.get('linea_investigacion_1')
            linea_2 = self.cleaned_data.get('linea_investigacion_2')
            linea_3 = self.cleaned_data.get('linea_investigacion_3')
            
            # Verificar si hay líneas disponibles en la base de datos
            lineas_disponibles = LineaInvestigacion.objects.filter(activa=True).exists()
            
            # Solo guardar líneas si hay líneas disponibles y seleccionadas
            if lineas_disponibles and (linea_1 or linea_2 or linea_3):
                # Eliminar líneas existentes
                ClubLineaInvestigacion.objects.filter(club=club).delete()
                
                # Agregar nuevas líneas
                lineas_data = [
                    (linea_1, 'principal', 1),
                    (linea_2, 'soporte', 2),
                    (linea_3, 'afines', 3),
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


class TutorForm(forms.ModelForm):
    """
    Formulario para crear y editar tutores.
    
    Incluye todos los campos necesarios para el registro de un tutor
    asociado a una institución.
    """
    
    class Meta:
        model = Tutor
        fields = [
            'institucion',
            'nombres',
            'apellidos',
            'cedula',
            'telefono',
            'email',
            'profesion',
            'experiencia',
            'status',
        ]
        widgets = {
            'institucion': forms.Select(attrs={
                'class': 'form-select',
            }),
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres del tutor',
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos del tutor',
            }),
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: V12345678',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 0414-1234567',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
            'profesion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Profesión o especialidad',
            }),
            'experiencia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa la experiencia en robótica...',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'institucion': 'Institución',
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'cedula': 'Cédula de Identidad',
            'telefono': 'Teléfono de Contacto',
            'email': 'Correo Electrónico',
            'profesion': 'Profesión / Especialidad',
            'experiencia': 'Experiencia en Robótica',
            'status': 'Estado',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que institucion no sea requerido si se pasa inicialmente
        if 'initial' in kwargs and kwargs['initial'].get('institucion'):
            self.fields['institucion'].required = False
    
    def clean_cedula(self):
        """Validar formato de cédula."""
        cedula = self.cleaned_data.get('cedula', '')
        cedula = cedula.upper().strip()
        
        # Verificar formato básico
        if not cedula:
            raise ValidationError("La cédula es obligatoria.")
        
        # Permitir formato V o E seguido de números, o solo números
        import re
        if not re.match(r'^[VE]?\d+$', cedula):
            raise ValidationError(
                "Formato inválido. Use V12345678, E12345678 o solo números."
            )
        
        # Verificar unicidad (excluyendo la instancia actual en edición)
        queryset = Tutor.objects.filter(cedula=cedula)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError(
                f"Ya existe un tutor registrado con la cédula '{cedula}'."
            )
        
        return cedula
    
    def clean_email(self):
        """Validar email único."""
        email = self.cleaned_data.get('email', '')
        email = email.lower().strip()
        
        queryset = Tutor.objects.filter(email=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError(
                f"Ya existe un tutor registrado con el correo '{email}'."
            )
        
        return email
