from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile 
from .mixins import LocationFormMixin, ParticipanteBaseFormMixin
from .utils import StringUtils
import uuid
import re

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
    ParticipanteInstitucion,
    NACIONALIDAD_CHOICES,
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
    ("0424", "0424"),
    ("0414", "0414"),
    ("0422", "0422"),
    ("0412", "0412"),
    ("0426", "0426"),
    ("0416", "0416"),
    ("0212", "0212"),
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

class ParticipanteRegistrationForm(ParticipanteBaseFormMixin, LocationFormMixin, forms.ModelForm):
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

    TIPO_VINCULACION_CHOICES = ParticipanteInstitucion.TIPO_VINCULACION_CHOICES

    tipo_vinculacion = forms.ChoiceField(
        choices=TIPO_VINCULACION_CHOICES,
        initial='institucional',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Vinculación'
    )

    vinculacion_institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(estatus='aprobado'),
        required=False,
        label='Institución de Vinculación',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    vinculacion_estado = forms.ModelChoiceField(
        queryset=Estado.objects.all().order_by('nombre'),
        required=False,
        label='Estado de Vinculación (Regional)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    nacionalidad = forms.ChoiceField(
        choices=NACIONALIDAD_CHOICES,
        initial="V",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Nacionalidad"
    )

    condicion_tea = forms.TypedChoiceField(
        choices=[("False", "No"), ("True", "Sí")],
        coerce=lambda x: x == "True",
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Condición TEA",
    )

    class Meta:
        model = Participante
        fields = [
            "nombres", "apellidos", "fecha_nacimiento", "sexo",
            "nacionalidad", "condicion_tea", "codigo_area", "numero_telefono",
            "direccion", "estado", "municipio", "parroquia", "grado_escolar",
            "titulo_universitario", "campo1",
            "nombre_representante", "nacionalidad_representante", "cedula_representante",
            "codigo_area_representante", "numero_telefono_representante",
            "email_representante", "email",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                format='%Y-%m-%d',
                attrs={"type": "date", "class": "form-control"}
            ),
            "direccion": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "cedula_representante": forms.TextInput(attrs={
                "placeholder": "Solo números", 
                "class": "form-control",
                "maxlength": "10",
                "pattern": "[0-9]+"
            }),
            "titulo_universitario": forms.TextInput(attrs={
                "class": "form-control border-primary shadow-sm",
                "placeholder": "Ej: Ingeniería, Licenciatura, etc."
            }),
            "campo1": forms.TextInput(attrs={
                "class": "form-control border-secondary shadow-sm",
                "placeholder": "Especifique el nivel educativo"
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extraer parámetros personalizados antes de llamar a super()
        self.user_role = kwargs.pop('user_role', 'institucional')
        self.user_institution = kwargs.pop('user_institution', None)
        
        super().__init__(*args, **kwargs)
        
        # 1. Estilizar todos los campos (Bootstrap 5)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
        
        # Uso de form-select para desplegables (mejor estética en BS5)
        for select_field in ['estado', 'municipio', 'parroquia', 'sexo', 'codigo_area', 'codigo_area_representante', 'nacionalidad', 'nacionalidad_representante', 'condicion_tea']:
            if select_field in self.fields:
                self.fields[select_field].widget.attrs.update({"class": "form-select"})

        # Hacer obligatorios los campos de ubicación georeferencial
        for loc in ['estado', 'municipio', 'parroquia']:
            if loc in self.fields:
                self.fields[loc].required = True

        # 1b. Marcar campos inválidos para feedback visual
        self.error_css_class = 'is-invalid'
        for field_name in self.errors:
            if field_name in self.fields:
                existing_class = self.fields[field_name].widget.attrs.get('class', '')
                if 'is-invalid' not in existing_class:
                    self.fields[field_name].widget.attrs['class'] = f"{existing_class} is-invalid".strip()

        # 2. Configurar querysets de ubicación usando el Mixin
        self.setup_location_fields()

        # 3. Precargar valores de cédula si existe instancia
        if hasattr(self, 'instance') and self.instance and hasattr(self.instance, 'pk') and self.instance.pk:
            self.fields['cedula_personal'].initial = self.instance.cedula
            self.fields['cedula_escolar_input'].initial = self.instance.cedula_escolar

        # 4. CONFIGURAR CAMPOS SEGÚN ROL DEL USUARIO
        self._configure_fields_by_role()

    def _configure_fields_by_role(self):
        """Configura los campos del formulario según el rol del usuario."""
        
        if self.user_role == 'fed_central':
            # Federación Central: TODOS los campos de vinculación visibles y funcionales
            # No hacer cambios, todos los campos ya están configurados
            pass
            
        elif self.user_role == 'institucional':
            # Usuario Institucional: Solo puede vincular a su propia institución
            # Ocultar selector de tipo de vinculación
            self.fields['tipo_vinculacion'].widget = forms.HiddenInput()
            self.fields['tipo_vinculacion'].initial = 'institucional'
            self.fields['tipo_vinculacion'].required = False
            
            # Configurar institución: solo la suya, oculta
            if self.user_institution:
                self.fields['vinculacion_institucion'].widget = forms.HiddenInput()
                self.fields['vinculacion_institucion'].queryset = Institucion.objects.filter(id=self.user_institution.id)
                self.fields['vinculacion_institucion'].initial = self.user_institution.id
                self.fields['vinculacion_institucion'].required = False
            else:
                # Si no tiene institución, ocultar campo
                self.fields['vinculacion_institucion'].widget = forms.HiddenInput()
                self.fields['vinculacion_institucion'].required = False
            
            # Ocultar campo de estado regional
            self.fields['vinculacion_estado'].widget = forms.HiddenInput()
            self.fields['vinculacion_estado'].required = False
            
        else:  # fed_regional u otros
            # Federación Regional: campos de vinculación ocultos
            self.fields['tipo_vinculacion'].widget = forms.HiddenInput()
            self.fields['tipo_vinculacion'].required = False
            self.fields['vinculacion_institucion'].widget = forms.HiddenInput()
            self.fields['vinculacion_institucion'].required = False
            self.fields['vinculacion_estado'].widget = forms.HiddenInput()
            self.fields['vinculacion_estado'].required = False

    def clean_cedula_personal(self):
        val = StringUtils.clean_numeric_id(self.cleaned_data.get('cedula_personal'))
        return val if val else None
    
    def clean_cedula_escolar_input(self):
        val = StringUtils.clean_numeric_id(self.cleaned_data.get('cedula_escolar_input'))
        return val if val else None
    
    def clean_cedula_representante(self):
        cedula = StringUtils.clean_numeric_id(self.cleaned_data.get('cedula_representante'))
        if cedula and len(cedula) > 10:
            raise forms.ValidationError("La cédula del representante no puede exceder los 10 dígitos.")
        if cedula and len(cedula) < 7:
            raise forms.ValidationError("La cédula del representante debe tener al menos 7 dígitos.")
        return cedula
    
    def clean(self):
        cleaned_data = super().clean()
        # Usar validaciones centralizadas del Mixin
        cleaned_data = self.clean_id_fields(cleaned_data)
        cleaned_data = self.validate_age_and_representative(cleaned_data)
        cleaned_data = self.clean_location_integrity(cleaned_data)

        # Validación de vínculo institucional/regional/central SEGÚN ROL
        if self.user_role == 'fed_central':
            # Federación Central: validar normalmente
            tipo_vinculacion = cleaned_data.get('tipo_vinculacion')
            institucion = cleaned_data.get('vinculacion_institucion')
            estado = cleaned_data.get('vinculacion_estado')

            if tipo_vinculacion == 'institucional' and not institucion:
                raise ValidationError('Debe seleccionar una institución para la vinculación institucional.')

            if tipo_vinculacion == 'regional' and not estado:
                raise ValidationError('Debe seleccionar un estado para la vinculación regional.')
                
        elif self.user_role == 'institucional':
            # Usuario Institucional: forzar vinculación institucional con su institución
            cleaned_data['tipo_vinculacion'] = 'institucional'
            if self.user_institution:
                cleaned_data['vinculacion_institucion'] = self.user_institution
            cleaned_data['vinculacion_estado'] = None
            
        else:  # fed_regional u otros
            # No validar campos de vinculación, estarán ocultos
            pass

        return cleaned_data

        # Central no requiere institucion/estado
        if tipo_vinculacion == 'central':
            cleaned_data['vinculacion_institucion'] = None
            cleaned_data['vinculacion_estado'] = None

        return cleaned_data

# --- FORMULARIO DE INSTITUCIONES ---
class InstitucionRegistrationForm(LocationFormMixin, forms.ModelForm):
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
        ("0241", "0241"),
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
        max_length=20,
        required=False,
        label="Cédula",
        widget=forms.TextInput(attrs={
            'placeholder': 'Solo números',
            'pattern': r'[0-9.\-\s]+',
            'maxlength': '20'
        })
    )

    def clean_particular_cedula(self):
        raw = self.cleaned_data.get("particular_cedula", "")
        cleaned = StringUtils.clean_numeric_id(raw)
        if cleaned and len(cleaned) > 10:
            raise forms.ValidationError("La cédula no puede tener más de 10 dígitos.")
        return cleaned
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
        # Usar Mixin para ubicación
        self.setup_location_fields()
        
        # Configurar campos dinámicos basados en tipo_institucion
        tipo_institucion = self.initial.get('tipo_institucion') or self.data.get('tipo_institucion')
        if tipo_institucion:
            self._configure_fields_by_tipo_institucion(tipo_institucion)
    
    def _configure_fields_by_tipo_institucion(self, tipo_institucion):
        """Configura campos dinámicos basados en el tipo de institución"""
        if tipo_institucion == 'educativa':
            # Código MPPE obligatorio para instituciones educativas
            self.fields['codigo_mppe'].required = True
        else:
            # Código MPPE no obligatorio para otros tipos
            self.fields['codigo_mppe'].required = False
            
        if tipo_institucion == 'particular':
            # Nacionalidad por defecto "V" para personas naturales
            self.fields['particular_nacionalidad'].initial = 'V'            # En persona natural, nombre puede derivarse de los datos de particular
            self.fields['nombre'].required = False
    def _handle_institucion_eliminada(self, institucion_eliminada, campo_validado, valor_campo):
        """
        Maneja el caso especial cuando una institución eliminada intenta registrarse.
        Verifica que todos los datos únicos coincidan antes de reactivar.
        """
        cleaned_data = self.cleaned_data
        
        # Verificar que TODOS los identificadores únicos coincidan
        if not self._validar_datos_coinciden(institucion_eliminada, cleaned_data):
            # Si no coinciden todos los datos, tratar como registro normal
            # (el error se manejará en otras validaciones)
            return valor_campo
        
        # ⚡ REACTIVAR INSTITUCIÓN ELIMINADA
        self._reactivar_institucion_eliminada(institucion_eliminada)
        
        # Retornar el valor sin error (no hay validación que falle)
        return valor_campo
    
    def _validar_datos_coinciden(self, institucion_eliminada, cleaned_data):
        """
        Verifica que todos los datos únicos coincidan antes de reactivar.
        """
        tipo_institucion = cleaned_data.get("tipo_institucion")
        
        # Para instituciones (no particulares)
        if tipo_institucion != "particular":
            # Validar RIF
            rif_letra = cleaned_data.get("rif_letra", "")
            rif_numero = cleaned_data.get("rif_numero", "")
            if rif_letra and rif_numero:
                rif_form = f"{rif_letra}-{rif_numero}"
                if institucion_eliminada.rif != rif_form:
                    return False
            
            # Validar Código MPPE si es educativa
            if tipo_institucion == "educativa":
                codigo_mppe = cleaned_data.get("codigo_mppe", "").strip().upper()
                if institucion_eliminada.codigo_mppe != codigo_mppe:
                    return False
        
        # Para personas naturales
        else:
            # Validar cédula
            cedula = StringUtils.clean_numeric_id(cleaned_data.get("particular_cedula", ""))
            if institucion_eliminada.particular_cedula != cedula:
                return False
        
        # Si llega aquí, todos los datos coinciden
        return True
    
    def _reactivar_institucion_eliminada(self, institucion):
        """
        Reactiva una institución eliminada poniéndola en estado pendiente.
        """
        # 1. Reactivar institución
        institucion.eliminado = False
        institucion.activa = False  # Queda inhabilitada hasta aprobación
        institucion.estatus = "pendiente"  # Requiere nueva aprobación
        
        # 2. Desactivar usuario hasta aprobación
        if institucion.usuario:
            institucion.usuario.is_active = False
            institucion.usuario.save()
        
        # 3. Limpiar fecha de eliminación si existe
        if hasattr(institucion, 'fecha_eliminacion'):
            institucion.fecha_eliminacion = None
        
        institucion.save()
        
        # 4. Marcar que se reactivó una institución (para lógica en save())
        self._institucion_reactivada = institucion

    def _buscar_institucion_eliminada_para_reactivar(self, cleaned_data):
        """
        Busca una institución eliminada que coincida exactamente con los datos proporcionados.
        Retorna la institución si existe y está eliminada, None en caso contrario.
        """
        tipo_institucion = cleaned_data.get("tipo_institucion")
        email = cleaned_data.get("email", "").strip().lower()
        
        if not email:
            return None
            
        # Buscar institución eliminada con este email
        institucion = Institucion.objects.filter(
            email=email,
            eliminado=True
        ).first()
        
        if not institucion:
            return None
            
        # Verificar que el tipo de institución coincida
        if institucion.tipo_institucion != tipo_institucion:
            return None
            
        # Para instituciones (no particulares)
        if tipo_institucion != "particular":
            # Verificar RIF
            rif_letra = cleaned_data.get("rif_letra", "")
            rif_numero = cleaned_data.get("rif_numero", "")
            if rif_letra and rif_numero:
                rif_form = f"{rif_letra}-{rif_numero}"
                if institucion.rif != rif_form:
                    return None
            
            # Verificar Código MPPE si es educativa
            if tipo_institucion == "educativa":
                codigo_mppe = cleaned_data.get("codigo_mppe", "").strip().upper()
                if institucion.codigo_mppe != codigo_mppe:
                    return None
        
        # Para personas naturales
        else:
            # Verificar cédula
            cedula = StringUtils.clean_numeric_id(cleaned_data.get("particular_cedula", ""))
            if institucion.particular_cedula != cedula:
                return None
        
        # Si llega aquí, todos los datos coinciden
        return institucion

    def clean_email(self):
        """
        Validar email con unicidad solo para instituciones activas (no eliminadas).
        """
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError("El email es obligatorio.")
        
        # Buscar institución activa (no eliminada) con este email
        existing = Institucion.objects.filter(email=email, eliminado=False).first()
        if existing:
            raise forms.ValidationError("Ya existe una institución registrada con este correo.")
        
        return email

    def clean(self):
        cleaned_data = super().clean()
        tipo_institucion = cleaned_data.get("tipo_institucion")
        password = cleaned_data.get("password") or ""
        confirm_password = cleaned_data.get("confirm_password") or ""
        
        # Validar integridad de ubicación usando Mixin
        cleaned_data = self.clean_location_integrity(cleaned_data)

        # ⚡ DETECCIÓN TEMPRANA DE INSTITUCIÓN ELIMINADA PARA REACTIVACIÓN
        # Buscar institución eliminada que coincida con los datos proporcionados
        institucion_eliminada = self._buscar_institucion_eliminada_para_reactivar(cleaned_data)
        if institucion_eliminada:
            # Verificar que TODOS los datos únicos coincidan
            if self._validar_datos_coinciden(institucion_eliminada, cleaned_data):
                # ⚡ MARCAR PARA REACTIVACIÓN - Esto bypass todas las validaciones de unicidad
                self._institucion_reactivada = institucion_eliminada
                # Reactivar inmediatamente para evitar conflictos de unicidad
                self._reactivar_institucion_eliminada(institucion_eliminada)
                # Retornar temprano - no ejecutar otras validaciones
                return cleaned_data

        # Validar campos según tipo de institución
        if tipo_institucion == "particular":
            if not cleaned_data.get("particular_nombres"):
                self.add_error("particular_nombres", "Los nombres son obligatorios para personas naturales.")
            if not cleaned_data.get("particular_apellidos"):
                self.add_error("particular_apellidos", "Los apellidos son obligatorios para personas naturales.")

            if not cleaned_data.get("nombre"):
                # Si no se indicó nombre institucional, usamos datos de persona natural
                nombres = cleaned_data.get("particular_nombres", "").strip()
                apellidos = cleaned_data.get("particular_apellidos", "").strip()
                if nombres or apellidos:
                    cleaned_data["nombre"] = f"{nombres} {apellidos}".strip()

            cedula = StringUtils.clean_numeric_id(cleaned_data.get("particular_cedula"))
            if not cedula:
                self.add_error("particular_cedula", "La cédula es obligatoria.")
            else:
                # Buscar institución existente con esta cédula
                existing = Institucion.objects.filter(particular_cedula=cedula).first()
                if existing:
                    if existing.eliminado:
                        # ⚡ ESCENARIO ESPECIAL: Reactivar institución eliminada
                        self._handle_institucion_eliminada(existing, "particular_cedula", cedula)
                    else:
                        # Validación normal: institución activa ya existe
                        self.add_error("particular_cedula", f"Cédula {cedula} ya registrada.")
                cleaned_data["particular_cedula"] = cedula
        else:
            rif_numero = cleaned_data.get("rif_numero")
            if not rif_numero:
                self.add_error("rif_numero", "El RIF es obligatorio.")
            
            # Validar código MPPE obligatorio para instituciones educativas
            if tipo_institucion == "educativa":
                codigo_mppe = cleaned_data.get("codigo_mppe")
                if not codigo_mppe or not codigo_mppe.strip():
                    self.add_error("codigo_mppe", "El código MPPE es obligatorio para instituciones educativas.")
                else:
                    # Normalizar el código MPPE (mayúsculas y espacios)
                    codigo_mppe_normalizado = codigo_mppe.strip().upper()
                    
                    # Buscar institución existente con este código MPPE
                    existing = Institucion.objects.filter(codigo_mppe=codigo_mppe_normalizado).first()
                    if existing:
                        if existing.eliminado:
                            # ⚡ ESCENARIO ESPECIAL: Reactivar institución eliminada
                            self._handle_institucion_eliminada(existing, "codigo_mppe", codigo_mppe_normalizado)
                        else:
                            # Validación normal: institución activa ya existe
                            self.add_error(
                                "codigo_mppe",
                                f"El código MPPE '{codigo_mppe_normalizado}' ya está registrado. "
                                "Si cree que esto es un error, por favor contacte con la administración."
                            )
                    
                    cleaned_data["codigo_mppe"] = codigo_mppe_normalizado
        
        # Validación de contraseña con requisitos fuertes
        if len(password) < 8:
            self.add_error("password", "Mínimo 8 caracteres.")
        else:
            # Validar mayúscula
            if not re.search(r'[A-Z]', password):
                self.add_error("password", "Debe incluir al menos 1 letra mayúscula.")
            # Validar número
            if not re.search(r'[0-9]', password):
                self.add_error("password", "Debe incluir al menos 1 número.")
            # Validar carácter especial
            if not re.search(r'[!@#$%^&*()_\-=\[\]{};:\'",.<>?/\\|`~]', password):
                self.add_error("password", "Debe incluir un carácter especial (!@#$%^&*...).")
        
        if password != confirm_password:
            self.add_error("confirm_password", "Las contraseñas no coinciden.")
        
        # Validación de cascada de ubicación
        estado = cleaned_data.get("estado")
        municipio = cleaned_data.get("municipio")
        parroquia = cleaned_data.get("parroquia")
        
        if municipio and estado:
            if municipio.estado_id != estado.id:
                self.add_error("municipio", 
                    f"El municipio '{municipio.nombre}' no pertenece al estado '{estado.nombre}'.")
        
        if parroquia and municipio:
            if parroquia.municipio_id != municipio.id:
                self.add_error("parroquia", 
                    f"La parroquia '{parroquia.nombre}' no pertenece al municipio '{municipio.nombre}'.")
        
        # 4. VALIDACIÓN ATÓMICA DE DUPLICIDAD (Nombre, RIF, Ubicación)
        nombre = cleaned_data.get("nombre")
        rif_letra = cleaned_data.get("rif_letra")
        rif_num = StringUtils.clean_numeric_id(cleaned_data.get("rif_numero"))

        if tipo_institucion != "particular" and nombre and rif_letra and rif_num and estado and municipio and parroquia:
            # Formato consistente: J-12345678 (8 dígitos máximo)
            # Si rif_num es 10 dígitos, usar primeros 8
            rif_num_limpio = rif_num[:10]  # Máximo 10 dígitos
            rif_completo = f"{rif_letra}-{rif_num_limpio[:8]}"
            if len(rif_num_limpio) > 8:
                rif_completo = f"{rif_letra}-{rif_num_limpio[:8]}-{rif_num_limpio[8:10]}"

            # Permitir considerar duplicado si el RIF coincide con el value base de 8 dígitos
            rif_base = f"{rif_letra}-{rif_num_limpio[:8]}"
            rif_posibles = [rif_completo]
            if rif_completo != rif_base:
                rif_posibles.append(rif_base)

            # Buscar coincidencia de RIF (exacto o base) + nombre + ubicación
            duplicado = Institucion.objects.filter(
                nombre__iexact=nombre,
                rif__in=rif_posibles,
                estado=estado,
                municipio=municipio,
                parroquia=parroquia,
                eliminado=False
            ).exists()

            if duplicado:
                raise ValidationError(
                    f"Ya existe una institución registrada con el nombre '{nombre}' y RIF '{rif_completo}' en esta ubicación (Estado {estado.nombre}, Municipio {municipio.nombre})."
                )

        return cleaned_data

    def save(self, commit=True):
        # Si se reactivó una institución eliminada, retornar la existente
        if hasattr(self, '_institucion_reactivada'):
            return self._institucion_reactivada
        
        # Lógica normal de creación de nueva institución
        instance = super().save(commit=False)
        tipo_institucion = self.cleaned_data.get("tipo_institucion")
        
        if tipo_institucion == "particular":
            instance.particular_nombres = self.cleaned_data.get("particular_nombres")
            instance.particular_apellidos = self.cleaned_data.get("particular_apellidos")
            instance.particular_nacionalidad = self.cleaned_data.get("particular_nacionalidad")
            instance.particular_cedula = self.cleaned_data.get("particular_cedula")
            instance.rif = None
        else:
            rif_letra = self.cleaned_data.get("rif_letra")
            rif_num = StringUtils.clean_numeric_id(self.cleaned_data.get("rif_numero"))
            if rif_letra and rif_num:
                # Formato consistente: J-12345678 o J-12345678-90
                rif_num_limpio = rif_num[:10]  # Máximo 10 dígitos
                if len(rif_num_limpio) <= 8:
                    instance.rif = f"{rif_letra}-{rif_num_limpio}"
                else:
                    instance.rif = f"{rif_letra}-{rif_num_limpio[:8]}-{rif_num_limpio[8:10]}"
        
        instance.telefono_codigo = self.cleaned_data.get("codigo_area")
        instance.telefono_numero = self.cleaned_data.get("numero_telefono")
        instance.telefono = f"{instance.telefono_codigo}{instance.telefono_numero}"
        
        if commit: 
            instance.save()
        return instance

# --- FORMULARIO DE CLUBES ---
class ClubRegistrationForm(forms.ModelForm):
    """
    Formulario para registrar clubes con líneas de investigación dinámicas.
    """
    from registry.models import LineaInvestigacion, ClubLineaInvestigacion
    
    linea_investigacion_1 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True).order_by('orden'),
        required=True,
        label="Línea Principal",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    linea_investigacion_2 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True).order_by('orden'),
        required=False,
        label="Línea 2 (Opcional)",
        empty_label="Seleccione una línea",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Club
        fields = ['nombre', 'descripcion', 'ubicacion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        l1 = cleaned_data.get('linea_investigacion_1')
        l2 = cleaned_data.get('linea_investigacion_2')
        if l1 and l2 and l1 == l2:
            raise ValidationError("No puedes repetir la línea de investigación.")
        return cleaned_data

    def save(self, commit=True):
        club = super().save(commit=False)
        if commit:
            club.save()
            # Guardar líneas en el modelo intermedio
            from registry.models import ClubLineaInvestigacion
            ClubLineaInvestigacion.objects.filter(club=club).delete()
            for i, l in enumerate([self.cleaned_data.get('linea_investigacion_1'), self.cleaned_data.get('linea_investigacion_2')]):
                if l:
                    ClubLineaInvestigacion.objects.create(club=club, linea=l, orden=i+1)
        return club
