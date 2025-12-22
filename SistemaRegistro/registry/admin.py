from django.contrib import admin
from .models import Estado, Municipio, Institucion, Participante

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo']
    search_fields = ['nombre']

@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado']
    list_filter = ['estado']
    search_fields = ['nombre']

@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'estado', 'telefono', 'activa']
    list_filter = ['estado', 'activa']
    search_fields = ['nombre', 'codigo']
    list_editable = ['activa']

@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombres', 'apellidos', 'institucion', 'estado']
    list_filter = ['estado', 'institucion', 'sexo']
    search_fields = ['cedula', 'nombres', 'apellidos']
    
    fieldsets = (
        ('Datos Personales', {
            'fields': (
                'cedula', 'nombres', 'apellidos', 'fecha_nacimiento', 
                'sexo', 'email', 'telefono', 'direccion'
            )
        }),
        ('Ubicación', {
            'fields': ('estado', 'municipio')
        }),
        ('Institución', {
            'fields': ('institucion', 'grado_escolar')
        }),
        ('Representante (para menores)', {
            'fields': (
                'nombre_representante', 'cedula_representante',
                'telefono_representante', 'email_representante'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_registro', 'activo'),
            'classes': ('collapse',)
        })
    )