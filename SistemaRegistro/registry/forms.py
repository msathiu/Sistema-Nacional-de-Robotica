from django import forms
from .models import Participante, Estado, Municipio, Institucion

class ParticipanteForm(forms.ModelForm):
    class Meta:
        model = Participante
        fields = [
            'cedula', 'nombres', 'apellidos', 'fecha_nacimiento', 'sexo',
            'email', 'codigo_area', 
            'numero_telefono', 'direccion', 'estado', 'municipio',
            'institucion', 'grado_escolar', 'nombre_representante',
            'cedula_representante', 'codigo_area_representante',
            'numero_telefono_representante', 'email_representante'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['municipio'].queryset = Municipio.objects.none()
        
        if 'estado' in self.data:
            try:
                estado_id = int(self.data.get('estado'))
                self.fields['municipio'].queryset = Municipio.objects.filter(estado_id=estado_id).order_by('nombre')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['municipio'].queryset = self.instance.estado.municipio_set.order_by('nombre')

class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ['nombre', 'estado', 'codigo', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: UENB-001'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el queryset de estados esté ordenado y sea accesible
        self.fields['estado'].queryset = Estado.objects.all().order_by('nombre')
        
        # Si no hay estados, mostrar un mensaje
        if self.fields['estado'].queryset.count() == 0:
            self.fields['estado'].empty_label = "No hay estados disponibles"
        else:
            self.fields['estado'].empty_label = "Seleccione un estado"