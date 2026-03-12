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
            "nombre_escuela",
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
            "nombre_escuela": forms.TextInput(attrs={"placeholder": "Nombre de la escuela/universidad", "class": "form-control"}),
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
        
        # Configurar querysets de ubicación
        self.fields["municipio"].queryset = Municipio.objects.none()
        self.fields["parroquia"].queryset = Parroquia.objects.none()
        
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
            cedula = getattr(self.instance, 'cedula', '') or ''
            # Limpiar la cédula (quitar prefijo V- o E- si existe)
            self.initial['cedula_personal'] = ''.join(filter(str.isdigit, cedula))
            self.initial['cedula_escolar_input'] = getattr(self.instance, 'cedula_escolar', '') or ''
            
            # Calcular edad inicial
            from datetime import date
            if self.instance.fecha_nacimiento:
                today = date.today()
                edad = today.year - self.instance.fecha_nacimiento.year
                if (today.month, today.day) < (self.instance.fecha_nacimiento.month, self.instance.fecha_nacimiento.day):
                    edad -= 1
                self.initial['edad'] = edad
            
            # Cargar municipios según el estado del participante
            if getattr(self.instance, "estado", None):
                try:
                    self.fields["municipio"].queryset = self.instance.estado.municipios.order_by("nombre")
                except AttributeError:
                    # Si el related_name es diferente, intentar另一种方式
                    self.fields["municipio"].queryset = Municipio.objects.filter(estado=self.instance.estado).order_by("nombre")
            
            # Cargar parroquias según el municipio del participante
            if getattr(self.instance, "municipio", None):
                try:
                    self.fields["parroquia"].queryset = self.instance.municipio.parroquias.order_by("nombre")
                except AttributeError:
                    self.fields["parroquia"].queryset = Parroquia.objects.filter(municipio=self.instance.municipio).order_by("nombre")

        # Lógica para cargar municipios y parroquias dinámicamente desde POST
        if "estado" in self.data:
            try:
                estado_id = int(self.data.get("estado"))
                self.fields["municipio"].queryset = Municipio.objects.filter(
                    estado_id=estado_id
                ).order_by("nombre")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and getattr(self.instance, "estado", None):
            # Ya cargado arriba
            
            # Cargar parroquias según municipio seleccionado
            if "municipio" in self.data:
                try:
                    municipio_id = int(self.data.get("municipio"))
                    self.fields["parroquia"].queryset = Parroquia.objects.filter(
                        municipio_id=municipio_id
                    ).order_by("nombre")
                except (ValueError, TypeError):
                    pass
            elif self.instance.pk and getattr(self.instance, "municipio", None):
                # Ya cargado arriba
                pass

    def clean_cedula_personal(self):
        """Limpia la cédula personal dejando solo números."""
        cedula = self.data.get('cedula_personal', '').strip()
        if cedula:
            # Remover todo excepto números
            cedula_limpia = ''.join(filter(str.isdigit, cedula))
            if cedula_limpia and len(cedula_limpia) > 10:
                raise ValidationError("La cédula personal no puede tener más de 10 dígitos.")
            return cedula_limpia
        return ''
    
    def clean_cedula_escolar_input(self):
        """Limpia la cédula escolar dejando solo números."""
        cedula = self.data.get('cedula_escolar_input', '').strip()
        if cedula:
            cedula_limpia = ''.join(filter(str.isdigit, cedula))
            if cedula_limpia and len(cedula_limpia) > 20:
                raise ValidationError("La cédula escolar no puede tener más de 20 dígitos.")
            return cedula_limpia
        return ''

    def clean(self):
        """
        Validaciones de negocio para el formulario de participante.

        Reglas (alineadas con ParticipanteRegistrationForm):
            - Edad mínima: 3 años
            - Al menos una cédula es obligatoria (personal O escolar)
            - Para mayores de 10 años, la cédula personal es obligatoria
            - Si es menor de 18, los datos completos del representante son obligatorios
            - El grupo debe pertenecer a la institución seleccionada
        """
        cleaned_data = super().clean()

        from datetime import date

        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")

        # --- Validación de edad mínima (3 años) y cálculo de edad ---
        edad = None
        if fecha_nacimiento:
            today = date.today()
            edad = (
                today.year
                - fecha_nacimiento.year
                - (
                    (today.month, today.day)
                    < (fecha_nacimiento.month, fecha_nacimiento.day)
                )
            )
            if edad < 3:
                raise ValidationError(
                    "El participante debe tener al menos 3 años de edad."
                )

        # --- Validación de cédulas (mismas reglas que en registro) ---
        # Obtener cédulas directamente del POST (como ParticipantRegistrationForm)
        cedula_personal = self.data.get('cedula_personal', '').strip()
        cedula_escolar = self.data.get('cedula_escolar_input', '').strip()
        
        # Limpiar cédulas (solo números)
        if cedula_personal:
            cedula_personal = ''.join(filter(str.isdigit, cedula_personal))
        if cedula_escolar:
            cedula_escolar = ''.join(filter(str.isdigit, cedula_escolar))
        
        # Al menos una cédula es obligatoria
        if not cedula_personal and not cedula_escolar:
            raise ValidationError(
                "Debe proporcionar al menos una cédula (personal o escolar)."
            )

        # Longitud máxima alineada con el registro
        if cedula_personal and len(cedula_personal) > 10:
            self.add_error(
                "cedula",
                "La cédula personal no puede tener más de 10 dígitos.",
            )
        if cedula_escolar and len(cedula_escolar) > 20:
            self.add_error(
                "cedula_escolar",
                "La cédula escolar no puede tener más de 20 dígitos.",
            )

        # Para mayores de 10 años, cédula personal obligatoria
        if edad is not None and edad > 10 and not cedula_personal:
            raise ValidationError(
                "La cédula personal es obligatoria para mayores de 10 años."
            )

        # --- Validación de representante para menores de 18 ---
        if edad is not None and edad < 18:
            campos_rep = [
                "nombre_representante",
                "cedula_representante",
                "codigo_area_representante",
                "numero_telefono_representante",
                "email_representante",
            ]
            for campo in campos_rep:
                valor = (cleaned_data.get(campo) or "").strip()
                if not valor:
                    self.add_error(
                        campo,
                        "Este campo es obligatorio para menores de edad.",
                    )

        # Validación de grupo (si se proporciona)
        grupo = cleaned_data.get("grupo")
        institucion = cleaned_data.get("institucion")
        
        if grupo and institucion:
            if grupo.institucion_id != institucion.id:
                raise ValidationError(
                    "El grupo seleccionado no pertenece a la institución elegida."
                )

        return cleaned_data


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
    
    NOTA: institucion se maneja en la vista, no en el formulario.
    El status se maneja por vinculación (TutorInstitucion).
    """
    
    # Campo adicional para seleccionar institución (no del modelo)
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(estatus='aprobado'),
        required=True,
        label='Institución',
        widget=forms.Select(attrs={'class': 'form-select'})
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
            'nacionalidad': forms.Select(attrs={
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
            'sexo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12345678',
                'inputmode': 'numeric',
                'pattern': '[0-9]+',
                'title': 'Ingrese solo números sin letras (V/E)',
                'autocomplete': 'off',
                'maxlength': '12',
            }),
            'telefono_codigo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1234567',
                'inputmode': 'numeric',
                'pattern': '[0-9]{7}',
                'maxlength': '7',
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
        }
        labels = {
            'nacionalidad': 'Nacionalidad',
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'sexo': 'Sexo',
            'cedula': 'Cédula de Identidad',
            'telefono_codigo': 'Código de Área',
            'telefono': 'Número de Teléfono',
            'email': 'Correo Electrónico',
            'profesion': 'Profesión / Especialidad',
            'experiencia': 'Experiencia en Robótica',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que institucion no sea requerido si se pasa inicialmente
        if 'initial' in kwargs and kwargs['initial'].get('institucion'):
            self.fields['institucion'].required = False
    
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
