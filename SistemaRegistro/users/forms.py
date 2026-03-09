from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile 
import uuid

from django.core.exceptions import ValidationError
from datetime import date
from registry.models import (
    Club,
    Dependencia,
    Estado,
    Institucion,
    Municipio,
    Parroquia,
    Participante,
)

# --- FORMULARIO DE SEDE REGIONAL (ADMINISTRACIÓN CENTRAL) ---
class SedeRegionalForm(forms.Form):
    # Credenciales de Acceso
    username = forms.CharField(
        label="Usuario", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: sede_miranda'})
    )
    email = forms.EmailField(
        label="Correo", 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'sede@correo.com'})
    )
    password = forms.CharField(
        label="Contraseña", 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'id': 'id_password1',
            'autocomplete': 'new-password'
        })
    )
    
    # Datos Personales del Encargado
    nombres = forms.CharField(
        label="Nombres", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres del encargado'})
    )
    apellidos = forms.CharField(
        label="Apellidos", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del encargado'})
    )
    cedula = forms.CharField(
        label="Cédula", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'V-12345678'})
    )
    
    # Teléfono (Formato Código + Número de 7 dígitos)
    CODIGOS_AREA = [
        ('0412', '0412'), ('0414', '0414'), ('0424', '0424'), 
        ('0416', '0416'), ('0426', '0426'), ('0212', '0212')
    ]
    codigo_area = forms.ChoiceField(
        choices=CODIGOS_AREA, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    numero_telefono = forms.CharField(
        max_length=7, 
        min_length=7, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '1234567',
            'pattern': '[0-9]{7}',
            'title': 'El número debe tener exactamente 7 dígitos'
        })
    )
    
    # Ubicación (Soberanía Territorial)
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all().order_by('nombre'), 
        empty_label="Seleccione Estado", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# --- FORMULARIOS DE USUARIOS ---
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

class ParticipanteModalEditForm(forms.ModelForm):
    CODIGOS_AREA = [
        ('0412', '0412'), ('0414', '0414'), ('0424', '0424'), 
        ('0416', '0416'), ('0426', '0426'), ('0212', '0212'),
    ]
    
    # Usamos widgets para añadir clases de Bootstrap directamente
    codigo_area = forms.ChoiceField(
        choices=CODIGOS_AREA,
        widget=forms.Select(attrs={'class': 'form-select border-0 shadow-sm'})
    )
    numero_telefono = forms.CharField(
        max_length=7, 
        min_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm', 'maxlength': '7'})
    )

    class Meta:
        model = Participante
        fields = ['nombres', 'apellidos', 'email', 'codigo_area', 'numero_telefono']

class ParticipanteRegistrationForm(forms.ModelForm):
    # Campos de cédula separados
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
    
    # Campo de edad calculado (readonly)
    edad = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "readonly": "readonly", "id": "id_edad_display"}
        ),
    )
    
    # Campo para el título/profesión (Dinámico en el HTML)
    profesion = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ej: Ingeniería, Licenciatura..."}
        )
    )

    class Meta:
        model = Participante
        fields = [
            "nombres", "apellidos", "fecha_nacimiento", "sexo",
            "codigo_area", "numero_telefono", "direccion", "estado",
            "municipio", "parroquia", "grado_escolar", "nombre_escuela",
            "nombre_representante", "cedula_representante",
            "codigo_area_representante", "numero_telefono_representante",
            "email_representante",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "cedula_representante": forms.TextInput(attrs={"placeholder": "Solo números"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Estilizar todos los campos (Bootstrap 5)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
        
        # Uso de form-select para desplegables (mejor estética en BS5)
        for select_field in ['estado', 'municipio', 'parroquia', 'sexo', 'codigo_area', 'codigo_area_representante']:
            if select_field in self.fields:
                self.fields[select_field].widget.attrs.update({"class": "form-select"})

        # 2. Cargar el QuerySet inicial de Estados
        if 'estado' in self.fields:
            self.fields["estado"].queryset = Estado.objects.all().order_by("nombre")

        # 3. Lógica de encadenamiento dinámico (Seguro contra KeyError)
        
        # PRIORIDAD A: Datos enviados en el POST
        if 'municipio' in self.fields and self.data.get('estado'):
            try:
                estado_id = self.data.get('estado')
                self.fields['municipio'].queryset = Municipio.objects.filter(estado_id=estado_id).order_by('nombre')
            except (ValueError, TypeError):
                self.fields['municipio'].queryset = Municipio.objects.none()
                
        # PRIORIDAD B: Datos de la instancia al EDITAR
        elif self.instance.pk and hasattr(self.instance, 'estado') and self.instance.estado:
            if 'municipio' in self.fields:
                self.fields['municipio'].queryset = Municipio.objects.filter(
                    estado=self.instance.estado
                ).order_by('nombre')
            
            # Verificación de Parroquia (Solo si el campo existe en el Form y el Modelo)
            if 'parroquia' in self.fields and hasattr(self.instance, 'municipio') and self.instance.municipio:
                # Nota: Asegúrate de tener el modelo Parroquia importado
                try:
                    from .models import Parroquia
                    self.fields['parroquia'].queryset = Parroquia.objects.filter(
                        municipio=self.instance.municipio
                    ).order_by('nombre')
                except ImportError:
                    pass
        
        # PRIORIDAD C: Carga inicial limpia (GET)
        else:
            if 'municipio' in self.fields:
                self.fields["municipio"].queryset = Municipio.objects.none()
            if 'parroquia' in self.fields:
                self.fields["parroquia"].queryset = Municipio.objects.none()

    def clean_fecha_nacimiento(self):
        fecha_nac = self.cleaned_data.get("fecha_nacimiento")
        if fecha_nac:
            today = date.today()
            edad = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
            
            if edad < 3:
                raise ValidationError("El participante debe tener al menos 3 años de edad.")
        return fecha_nac
    
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
            # Remover todo excepto números
            cedula_limpia = ''.join(filter(str.isdigit, cedula))
            if cedula_limpia and len(cedula_limpia) > 20:
                raise ValidationError("La cédula escolar no puede tener más de 20 dígitos.")
            return cedula_limpia
        return ''
    
    def clean_cedula_representante(self):
        """Limpia la cédula del representante dejando solo números."""
        cedula = self.cleaned_data.get('cedula_representante', '').strip()
        if cedula:
            cedula_limpia = ''.join(filter(str.isdigit, cedula))
            if cedula_limpia and len(cedula_limpia) > 10:
                raise ValidationError("La cédula del representante no puede tener más de 10 dígitos.")
            return cedula_limpia
        return cedula
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_nac = cleaned_data.get("fecha_nacimiento")
        
        # Obtener cédulas directamente del POST
        cedula_personal = self.data.get('cedula_personal', '').strip()
        cedula_escolar = self.data.get('cedula_escolar_input', '').strip()
        
        # Limpiar cédulas (solo números)
        if cedula_personal:
            cedula_personal = ''.join(filter(str.isdigit, cedula_personal))
        if cedula_escolar:
            cedula_escolar = ''.join(filter(str.isdigit, cedula_escolar))
        
        # Validar que tenga al menos una cédula
        if not cedula_personal and not cedula_escolar:
            raise ValidationError("Debe proporcionar al menos una cédula (personal o escolar).")
        
        if fecha_nac:
            today = date.today()
            edad = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
            
            # Para mayores de 10 años: cédula personal obligatoria
            if edad > 10 and not cedula_personal:
                raise ValidationError("La cédula personal es obligatoria para mayores de 10 años.")
            
            # Lógica para Menores de Edad (< 18 años)
            if edad < 18:
                campos_rep = [
                    'nombre_representante', 'cedula_representante', 
                    'codigo_area_representante', 'numero_telefono_representante', 
                    'email_representante'
                ]
                for campo in campos_rep:
                    if not cleaned_data.get(campo):
                        self.add_error(campo, "Este campo es obligatorio para menores de edad.")
        
        return cleaned_data

# --- FORMULARIO DE INSTITUCIONES ---
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
        ("", "Codigo"), ("0412", "0412"), ("0414", "0414"), ("0416", "0416"),
        ("0424", "0424"), ("0426", "0426"), ("0212", "0212"), ("0281", "0281"),
    ]

    tipo_institucion = forms.ChoiceField(
        choices=[("", "Seleccione el tipo de institucion")] + Institucion.TIPO_INSTITUCION_CHOICES
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
    rif_letra = forms.ChoiceField(choices=RIF_PREFIJO_CHOICES, required=False)
    rif_numero = forms.CharField(max_length=10, required=False)
    
    # Campos para Persona Natural
    particular_nombres = forms.CharField(max_length=100, required=False, label="Nombres")
    particular_apellidos = forms.CharField(max_length=100, required=False, label="Apellidos")
    particular_nacionalidad = forms.ChoiceField(
        choices=[('', 'Seleccione'), ('V', 'V'), ('E', 'E')],
        required=False,
        label="Nacionalidad"
    )
    particular_cedula = forms.CharField(
        max_length=10, 
        required=False,
        label="Cédula",
        widget=forms.TextInput(attrs={
            'placeholder': 'Solo números',
            'pattern': '[0-9]+',
            'maxlength': '10'
        })
    )
    codigo_area = forms.ChoiceField(choices=CODIGO_AREA_CHOICES)
    numero_telefono = forms.CharField(max_length=7, min_length=7)
    password = forms.CharField(label="Contrasena", widget=forms.PasswordInput())
    confirm_password = forms.CharField(label="Confirmar Contrasena", widget=forms.PasswordInput())
    terminos = forms.BooleanField(required=False)

    class Meta:
        model = Institucion
        fields = [
            "nombre", "email", "estado", "municipio", "parroquia",
            "direccion", "tipo_institucion", "naturaleza", "subcategoria", "codigo_mppe",
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
                self.fields["municipio"].queryset = Municipio.objects.filter(estado_id=estado_id).order_by("nombre")
            except (ValueError, TypeError): pass

        if "municipio" in self.data:
            try:
                municipio_id = int(self.data.get("municipio"))
                self.fields["parroquia"].queryset = Parroquia.objects.filter(municipio_id=municipio_id).order_by("nombre")
            except (ValueError, TypeError): pass

    def clean(self):
        cleaned_data = super().clean()
        tipo_institucion = cleaned_data.get("tipo_institucion")
        password = cleaned_data.get("password") or ""
        confirm_password = cleaned_data.get("confirm_password") or ""
        
        # Validar campos según tipo de institución
        if tipo_institucion == "particular":
            # Para particulares: validar campos de persona natural
            if not cleaned_data.get("particular_nombres"):
                self.add_error("particular_nombres", "Los nombres son obligatorios para personas naturales.")
            if not cleaned_data.get("particular_apellidos"):
                self.add_error("particular_apellidos", "Los apellidos son obligatorios para personas naturales.")
            if not cleaned_data.get("particular_nacionalidad"):
                self.add_error("particular_nacionalidad", "La nacionalidad es obligatoria para personas naturales.")
            
            cedula = cleaned_data.get("particular_cedula") or ""
            cedula = cedula.strip() if cedula else ""
            if not cedula:
                self.add_error("particular_cedula", "La cédula es obligatoria para personas naturales.")
            else:
                # Limpiar cédula: solo números
                cedula_limpia = ''.join(filter(str.isdigit, cedula))
                if not cedula_limpia:
                    self.add_error("particular_cedula", "La cédula debe contener números.")
                elif len(cedula_limpia) > 10:
                    self.add_error("particular_cedula", "La cédula no puede tener más de 10 dígitos.")
                else:
                    # Validación atómica: verificar que no exista otra institución con la misma cédula
                    from registry.models import Institucion
                    if Institucion.objects.filter(particular_cedula=cedula_limpia).exists():
                        self.add_error(
                            "particular_cedula",
                            f"Ya existe un registro con la cédula {cedula_limpia}. No se puede registrar más de una vez."
                        )
                    cleaned_data["particular_cedula"] = cedula_limpia
        else:
            # Para otros tipos: validar RIF
            rif_numero = cleaned_data.get("rif_numero")
            if not rif_numero:
                self.add_error("rif_numero", "El RIF es obligatorio para instituciones.")
        
        # Validación atómica de duplicados: tipo_institucion + nombre + rif + estado + municipio + parroquia
        if not self.errors:  # Solo validar si no hay errores previos
            nombre = cleaned_data.get("nombre")
            estado = cleaned_data.get("estado")
            municipio = cleaned_data.get("municipio")
            parroquia = cleaned_data.get("parroquia")
            
            # Construir RIF completo para instituciones
            rif_completo = None
            if tipo_institucion != "particular":
                rif_letra = cleaned_data.get("rif_letra")
                rif_numero = cleaned_data.get("rif_numero") or ""
                rif_numero_limpio = rif_numero.replace("-", "") if rif_numero else ""
                if rif_letra and rif_numero_limpio:
                    rif_completo = f"{rif_letra}-{rif_numero_limpio[:8]}-{rif_numero_limpio[8:]}"
            
            # Buscar duplicados atómicos
            from registry.models import Institucion
            from django.db.models import Q
            
            filtro_duplicado = Q(
                tipo_institucion=tipo_institucion,
                nombre__iexact=nombre,
                estado=estado,
                municipio=municipio,
                parroquia=parroquia,
                eliminado=False
            )
            
            # Agregar filtro de RIF solo para instituciones (no particulares)
            if tipo_institucion != "particular" and rif_completo:
                filtro_duplicado &= Q(rif=rif_completo)
            
            institucion_duplicada = Institucion.objects.filter(filtro_duplicado).first()
            
            if institucion_duplicada:
                raise ValidationError(
                    f"Ya existe una institución registrada con los mismos datos: "
                    f"Tipo: {institucion_duplicada.get_tipo_institucion_display()}, "
                    f"Razón Social: {institucion_duplicada.nombre}, "
                    f"RIF: {institucion_duplicada.rif or 'N/A'}, "
                    f"Ubicación: {estado.nombre if estado else 'N/A'} - {municipio.nombre if municipio else 'N/A'} - {parroquia.nombre if parroquia else 'N/A'}. "
                    f"No se permite el registro duplicado."
                )
        
        # Validaciones de seguridad de contraseña
        if len(password) < 8:
            self.add_error("password", "La contrasena debe tener al menos 8 caracteres.")
        if not any(ch.isupper() for ch in password):
            self.add_error("password", "Debe incluir al menos una letra mayuscula.")
        if not any(ch.isdigit() for ch in password):
            self.add_error("password", "Debe incluir al menos un numero.")
        if password != confirm_password:
            self.add_error("confirm_password", "Las contrasenas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        tipo_institucion = self.cleaned_data.get("tipo_institucion")
        
        # Procesar según tipo de institución
        if tipo_institucion == "particular":
            # Para personas naturales
            instance.particular_nombres = self.cleaned_data.get("particular_nombres")
            instance.particular_apellidos = self.cleaned_data.get("particular_apellidos")
            instance.particular_nacionalidad = self.cleaned_data.get("particular_nacionalidad")
            instance.particular_cedula = self.cleaned_data.get("particular_cedula")
            # RIF no es obligatorio para particulares
            instance.rif = None
            # Código MPPE no aplica para particulares
            instance.codigo_mppe = None
        else:
            # Para instituciones
            rif_letra = self.cleaned_data.get("rif_letra")
            rif_numero = self.cleaned_data.get("rif_numero") or ""
            rif_numero = rif_numero.replace("-", "") if rif_numero else ""
            if rif_letra and rif_numero:
                instance.rif = f"{rif_letra}-{rif_numero[:8]}-{rif_numero[8]}"
            
            # Limpiar código MPPE: si está vacío o es solo espacios, guardarlo como None
            codigo_mppe = self.cleaned_data.get("codigo_mppe") or ""
            codigo_mppe = codigo_mppe.strip() if codigo_mppe else ""
            instance.codigo_mppe = codigo_mppe if codigo_mppe else None
        
        # Teléfono
        codigo_area = self.cleaned_data.get("codigo_area")
        numero_telefono = self.cleaned_data.get("numero_telefono")
        instance.telefono_codigo = codigo_area
        instance.telefono_numero = numero_telefono
        instance.telefono = f"{codigo_area}{numero_telefono}"
        instance.federado = False
        
        if not instance.pk:
            instance.activa = False
            instance.estatus = 'pendiente'
        
        # Dependencia
        dependencia = self.cleaned_data.get("dependencia_existente")
        nueva_dependencia = self.cleaned_data.get("nueva_dependencia") or ""
        nueva_dependencia = nueva_dependencia.strip() if nueva_dependencia else ""
        if nueva_dependencia:
            from registry.models import Dependencia
            dependencia, _ = Dependencia.objects.get_or_create(nombre=nueva_dependencia)
        instance.dependencia_rel = dependencia
        instance.dependencia = dependencia.nombre if dependencia else None
        
        if not instance.codigo:
            import uuid
            instance.codigo = f"TEMP-{uuid.uuid4().hex[:8].upper()}"
        
        if commit: 
            instance.save()
        return instance


# --- FORMULARIO DE CLUBES ---
class ClubRegistrationForm(forms.ModelForm):
    """
    Formulario para registrar clubes con líneas de investigación dinámicas.
    Usa el modelo ClubLineaInvestigacion en lugar de campos deprecated.
    """
    from registry.models import LineaInvestigacion, ClubLineaInvestigacion
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener queryset de líneas de investigación activas
        lineas_qs = LineaInvestigacion.objects.filter(activa=True).order_by('orden', 'nombre')
        
        # Verificar si hay líneas disponibles
        if not lineas_qs.exists():
            # Si no hay líneas, hacer todos los campos opcionales para evitar errores
            self.fields['linea_investigacion_1'].required = False
            self.fields['linea_investigacion_1'].empty_label = "No hay líneas disponibles - Contacte al administrador"
        else:
            # Mensaje por defecto cuando hay líneas
            self.fields['linea_investigacion_1'].empty_label = "Seleccione una línea"
    
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
        fields = ['nombre', 'descripcion', 'ubicacion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Club de Robotica "Simon Rodriguez"'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Obtener las líneas
        linea_1 = cleaned_data.get('linea_investigacion_1')
        linea_2 = cleaned_data.get('linea_investigacion_2')
        linea_3 = cleaned_data.get('linea_investigacion_3')
        
        # Validar que la línea 1 sea obligatoria si hay líneas disponibles
        lineas_disponibles = LineaInvestigacion.objects.filter(activa=True).exists()
        if lineas_disponibles and not linea_1:
            raise forms.ValidationError({
                'linea_investigacion_1': 'Debe seleccionar al menos una línea de investigación principal.'
            })
        
        # Validar que no se repitan líneas
        lineas = [l for l in [linea_1, linea_2, linea_3] if l]
        if len(lineas) != len(set(lineas)):
            raise forms.ValidationError("No puedes seleccionar la misma línea de investigación más de una vez.")
        
        return cleaned_data

    def save(self, commit=True):
        from registry.models import ClubLineaInvestigacion
        
        club = super().save(commit=False)
        
        if commit:
            club.save()
            
            # Obtener las líneas del formulario
            linea_1 = self.cleaned_data.get('linea_investigacion_1')
            linea_2 = self.cleaned_data.get('linea_investigacion_2')
            linea_3 = self.cleaned_data.get('linea_investigacion_3')
            
            # Verificar si hay líneas disponibles en la base de datos
            lineas_disponibles = LineaInvestigacion.objects.filter(activa=True).exists()
            
            # Solo guardar líneas si hay líneas disponibles y seleccionadas
            if lineas_disponibles and (linea_1 or linea_2 or linea_3):
                # Eliminar líneas existentes si las hay
                ClubLineaInvestigacion.objects.filter(club=club).delete()
                
                # Agregar nuevas líneas de investigación
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
