from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from registry.models import Estado, Municipio, Parroquia
from .utils import StringUtils

class LocationFormMixin:
    """
    Mixin para manejar la lógica dinámica de Estados, Municipios y Parroquias en formularios.
    """
    def setup_location_fields(self):
        self.fields["estado"].queryset = Estado.objects.all().order_by("nombre")
        self.fields["municipio"].queryset = Municipio.objects.none()
        self.fields["parroquia"].queryset = Parroquia.objects.none()

        # Prioridad 1: Datos en POST (vienen como strings de IDs)
        # Prioridad 2: Datos en la instancia (vienen como objetos)
        # Prioridad 3: Datos iniciales (self.initial)
        
        estado_id = self.data.get("estado") or (self.instance.estado_id if self.instance.pk else None) or self.initial.get("estado")
        municipio_id = self.data.get("municipio") or (self.instance.municipio_id if self.instance.pk else None) or self.initial.get("municipio")
        parroquia_id = self.data.get("parroquia") or (self.instance.parroquia_id if self.instance.pk else None) or self.initial.get("parroquia")

        if estado_id:
            try:
                municipio_qs = Municipio.objects.filter(estado_id=estado_id).order_by("nombre")
                # Si se seleccionó un municipio que no pertenece a este estado,
                # inclúyalo para poder mostrar la validación de cascada en el formulario.
                if municipio_id:
                    try:
                        municipio_obj = Municipio.objects.get(pk=municipio_id)
                        if municipio_obj not in municipio_qs:
                            municipio_qs = Municipio.objects.filter(pk=municipio_obj.pk) | municipio_qs
                    except Municipio.DoesNotExist:
                        pass

                self.fields["municipio"].queryset = municipio_qs
            except (ValueError, TypeError):
                pass

        if municipio_id:
            try:
                parroquia_qs = Parroquia.objects.filter(municipio_id=municipio_id).order_by("nombre")
                # Si se seleccionó una parroquia de otro municipio, inclúyala para mostrar la validación.
                if parroquia_id:
                    try:
                        parroquia_obj = Parroquia.objects.get(pk=parroquia_id)
                        if parroquia_obj not in parroquia_qs:
                            parroquia_qs = Parroquia.objects.filter(pk=parroquia_obj.pk) | parroquia_qs
                    except Parroquia.DoesNotExist:
                        pass

                self.fields["parroquia"].queryset = parroquia_qs
            except (ValueError, TypeError):
                pass

    def clean_location_integrity(self, cleaned_data):
        estado = cleaned_data.get("estado")
        municipio = cleaned_data.get("municipio")
        parroquia = cleaned_data.get("parroquia")

        if estado and municipio and municipio.estado_id != estado.id:
            self.add_error("municipio", f"El municipio '{municipio}' no pertenece al estado '{estado}'.")

        if municipio and parroquia and parroquia.municipio_id != municipio.id:
            self.add_error("parroquia", f"La parroquia '{parroquia}' no pertenece al municipio '{municipio}'.")
        
        return cleaned_data

class ParticipanteBaseFormMixin:
    """
    Mixin para validaciones comunes de Participantes (Edad, Cédulas, Representantes).
    """
    def clean_id_fields(self, cleaned_data):
        # Obtener cédulas de cleaned_data (donde ya deben estar limpias por clean_cedula_x)
        # o del POST si no están en cleaned_data
        cedula_personal = cleaned_data.get('cedula_personal') or StringUtils.clean_numeric_id(self.data.get('cedula_personal', ''))
        cedula_escolar = cleaned_data.get('cedula_escolar_input') or StringUtils.clean_numeric_id(self.data.get('cedula_escolar_input', ''))
        
        # Convertir a None si son strings vacíos para evitar conflictos de unicidad en DB
        cedula_personal = cedula_personal if cedula_personal else None
        cedula_escolar = cedula_escolar if cedula_escolar else None

        if not cedula_personal and not cedula_escolar:
            raise ValidationError("Debe proporcionar al menos una cédula (personal o escolar).")
        
        # Guardar en cleaned_data para que el servicio las reciba limpias
        cleaned_data['cedula_personal'] = cedula_personal
        cleaned_data['cedula_escolar_input'] = cedula_escolar
        return cleaned_data

    def validate_age_and_representative(self, cleaned_data):
        fecha_nac = cleaned_data.get("fecha_nacimiento")
        if not fecha_nac:
            return cleaned_data

        today = date.today()
        edad = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
        
        if edad < 3:
            self.add_error("fecha_nacimiento", "El participante debe tener al menos 3 años de edad.")
        
        cedula_personal = cleaned_data.get('cedula_personal')
        if edad > 10 and not cedula_personal:
            self.add_error("cedula_personal", "La cédula personal es obligatoria para mayores de 10 años.")
        
        if edad < 18:
            campos_rep = [
                'nombre_representante', 'nacionalidad_representante', 'cedula_representante', 
                'codigo_area_representante', 'numero_telefono_representante', 
                'email_representante'
            ]
            for campo in campos_rep:
                if not cleaned_data.get(campo):
                    self.add_error(campo, "Este campo es obligatorio para menores de edad.")
        
        return cleaned_data
