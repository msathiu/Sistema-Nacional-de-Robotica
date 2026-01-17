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
    list_display = ('nombre', 'estado', 'codigo', 'activa', 'telefono', 'fecha_registro')# Esto crea columnas en la lista del admin
    list_filter = ('activa', 'estado') # Esto añade filtros laterales
    search_fields = ('nombre', 'codigo')# Esto permite buscar por nombre o código en la barra superior
    list_editable = ('activa',) # ¡Truco! Esto permite activar instituciones desde la lista principal sin entrar a cada una.

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