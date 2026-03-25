from django import forms
from django.core.exceptions import ValidationError
from users.mixins import LocationFormMixin, ParticipanteBaseFormMixin
from users.utils import StringUtils

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
    TutorInstitucion,
)


class ParticipanteForm(ParticipanteBaseFormMixin, LocationFormMixin, forms.ModelForm):
    """
    Formulario para crear/editar participantes.
    
    NOTA: institucion y grupo se manejan en ParticipanteInstitucion, no aquí.
    Este formulario solo maneja datos personales del participante.
    """
    
    # Campos adicionales para manejo de cédulas
    cedula_personal = forms.CharField(
        required=False,
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Solo números",
                "pattern": "[0-9]+",
                "maxlength": "10"
            }
        ),
        label="Cédula Personal"
    )
    
    cedula_escolar_input = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Solo números",
                "pattern": "[0-9]+",
                "maxlength": "20"
            }
        ),
        label="Cédula Escolar"
    )
    
    edad = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control bg-light", "readonly": "readonly", "id": "id_edad_display"}
        ),
        label="Edad"
    )
    
    # Campos adicionales para vinculación (no del modelo Participante)
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(estatus='aprobado'),
        required=False,
        label='Institución',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    grupo = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Grupo',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Participante
        fields = [
            "nacionalidad",
            "cedula",
            "cedula_escolar",
            "nombres",
            "apellidos",
            "fecha_nacimiento",
            "sexo",
            "email",
            "estado",
            "municipio",
            "parroquia",
            "direccion",
            "codigo_area",
            "numero_telefono",
            "grado_escolar",
            "titulo_universitario",
            "campo1",
            "condicion_tea",
            "nombre_representante",
            "nacionalidad_representante",
            "cedula_representante",
            "codigo_area_representante",
            "numero_telefono_representante",
            "email_representante",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "direccion": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "cedula_escolar": forms.TextInput(attrs={"placeholder": "Cédula escolar (opcional)", "class": "form-control"}),
            "titulo_universitario": forms.TextInput(attrs={"placeholder": "Título o carrera universitaria", "class": "form-control"}),
            "campo1": forms.Textarea(attrs={"rows": 2, "placeholder": "Especifique el nivel/grado si seleccionó 'Otro'", "class": "form-control"}),
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "numero_telefono": forms.TextInput(attrs={"class": "form-control", "maxlength": "7"}),
            "nombre_representante": forms.TextInput(attrs={"class": "form-control"}),
            "cedula_representante": forms.TextInput(attrs={"class": "form-control", "placeholder": "Solo números"}),
            "numero_telefono_representante": forms.TextInput(attrs={"class": "form-control", "maxlength": "7"}),
            "email_representante": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        # Extraer institución si se pasa como parámetro
        institucion = kwargs.pop('institucion', None)
        super().__init__(*args, **kwargs)
        
        # Estilizar campos
        for field_name, field in self.fields.items():
            if field_name not in ['cedula_personal', 'cedula_escolar_input', 'edad']:
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs.update({"class": "form-select"})
                elif not field.widget.attrs.get('class'):
                    field.widget.attrs.update({"class": "form-control"})
        
        # Configurar querysets de ubicación usando el Mixin
        self.setup_location_fields()
        
        # Configurar queryset de grupos (vacío por defecto)
        from .models import Grupo
        self.fields["grupo"].queryset = Grupo.objects.none()
        
        # Si se pasa institución, configurar grupos
        if institucion:
            self.fields["institucion"].initial = institucion
            self.fields["grupo"].queryset = Grupo.objects.filter(
                institucion=institucion,
                activo=True
            ).order_by('nombre')
        
        # Cargar datos iniciales si es edición
        if self.instance.pk:
            # Inicializar campos de cédula separados
            self.initial['cedula_personal'] = StringUtils.clean_numeric_id(getattr(self.instance, 'cedula', ''))
            self.initial['cedula_escolar_input'] = getattr(self.instance, 'cedula_escolar', '') or ''

    def clean_cedula_personal(self):
        return StringUtils.clean_numeric_id(self.cleaned_data.get('cedula_personal'))
    
    def clean_cedula_escolar_input(self):
        return StringUtils.clean_numeric_id(self.cleaned_data.get('cedula_escolar_input'))

    def clean(self):
        cleaned_data = super().clean()
        # Usar validaciones centralizadas del Mixin
        cleaned_data = self.clean_id_fields(cleaned_data)
        cleaned_data = self.validate_age_and_representative(cleaned_data)
        cleaned_data = self.clean_location_integrity(cleaned_data)

        # Validación de grupo (específica de este formulario)
        grupo = cleaned_data.get("grupo")
        institucion = cleaned_data.get("institucion")
        if grupo and institucion and grupo.institucion_id != institucion.id:
            raise ValidationError("El grupo seleccionado no pertenece a la institución elegida.")

        return cleaned_data


class InstitucionForm(LocationFormMixin, forms.ModelForm):
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
        # Configurar querysets de ubicación usando el Mixin
        self.setup_location_fields()

    def clean(self):
        """Validación de integridad geográfica en el servidor"""
        cleaned_data = super().clean()
        # Usar validación centralizada del Mixin
        cleaned_data = self.clean_location_integrity(cleaned_data)
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
    
    Permite manejar vinculaciones institucionales, regionales y centrales.
    """
    
    tipo_vinculacion = forms.ChoiceField(
        choices=TutorInstitucion.TIPO_VINCULACION_CHOICES,
        initial='institucional',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_vinculacion'}),
        label='Tipo de Pertenencia'
    )
    
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(estatus='aprobado'),
        required=False,
        label='Institución Educativa / Club',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_institucion'})
    )

    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(),
        required=False,
        label='Estado (Sede Regional)',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_estado'})
    )
    
    rol = forms.ChoiceField(
        choices=TutorInstitucion.ROL_CHOICES,
        initial='colaborador',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Rol en el Ente'
    )

    class Meta:
        model = Tutor
        fields = [
            'nacionalidad',
            'nombres',
            'apellidos',
            'sexo',
            'cedula',
            'telefono_codigo',
            'telefono',
            'email',
            'profesion',
            'experiencia',
        ]
        widgets = {
            'nacionalidad': forms.Select(attrs={'class': 'form-select'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Solo números',
                'maxlength': '12',
            }),
            'telefono_codigo': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '7 dígitos'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'profesion': forms.TextInput(attrs={'class': 'form-control'}),
            'experiencia': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_vinculacion')
        institucion = cleaned_data.get('institucion')
        estado = cleaned_data.get('estado')

        if tipo == 'institucional' and not institucion:
            self.add_error('institucion', 'Debe seleccionar una institución para este tipo de vinculación.')
        
        if tipo == 'regional' and not estado:
            self.add_error('estado', 'Debe seleccionar un estado para la vinculación regional.')

        return cleaned_data
    
    def clean_cedula(self):
        """Validar formato de cédula (solo números)."""
        cedula = self.cleaned_data.get('cedula', '').strip()
        
        if not cedula:
            raise ValidationError("La cédula es obligatoria.")
        
        # Limpiar: solo números
        cedula_limpia = ''.join(filter(str.isdigit, cedula))
        
        if not cedula_limpia:
            raise ValidationError("La cédula debe contener números.")
        
        # NOTA: No validamos unicidad aquí porque el sistema permite
        # que un tutor esté vinculado a múltiples instituciones.
        # La validación de vinculación se hace en TutorService.
        
        return cedula_limpia
    
    def clean_email(self):
        """Validar formato de email."""
        email = self.cleaned_data.get('email', '')
        email = email.lower().strip()
        
        # NOTA: No validamos unicidad aquí porque el sistema permite
        # que un tutor esté vinculado a múltiples instituciones.
        # Un mismo tutor (mismo email) puede estar en varias instituciones.
        
        return email
