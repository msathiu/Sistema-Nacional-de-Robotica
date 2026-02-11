from django.contrib import admin

from .models import Dependencia, Estado, Institucion, Municipio, Parroquia, Participante

from django.contrib.admin.exceptions import NotRegistered



@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "codigo")
    search_fields = ("nombre", "codigo")
    ordering = ("nombre",)


@admin.register(Dependencia)
class DependenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "activa")
    search_fields = ("nombre",)
    list_filter = ("activa",)


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado")
    list_filter = ("estado",)  # Filtro lateral por estado
    search_fields = ("nombre",)
    ordering = ("estado", "nombre")
    # Permite que Parroquia busque municipios de forma asíncrona
    search_fields = ["nombre"]


@admin.register(Parroquia)
class ParroquiaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "get_municipio", "get_estado")
    search_fields = ("nombre",)

    # Mejora de rendimiento: Filtra por el estado del municipio
    list_filter = ("municipio__estado",)

    # Nivel Pro: Autocompletado para no colapsar el navegador con miles de opciones
    autocomplete_fields = ["municipio"]

    @admin.display(description="Municipio", ordering="municipio__nombre")
    def get_municipio(self, obj):
        return obj.municipio.nombre

    @admin.display(description="Estado", ordering="municipio__estado__nombre")
    def get_estado(self, obj):
        return obj.municipio.estado.nombre


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    # Campos que se verán en la tabla principal (lista)
    list_display = ("codigo", "nombre", "estado", "email", "activa")

    # Permite buscar por nombre o código
    search_fields = ("nombre", "codigo", "email")

    # Filtros laterales
    list_filter = ("estado", "activa", "federado")

    # ESTA ES LA CLAVE:
    # Permite ver el campo en el formulario de edición aunque sea editable=False
    readonly_fields = ("codigo", "fecha_registro")

    # Organiza el formulario por secciones
    fieldsets = (
        ("Identificación del Sistema", {"fields": ("codigo",)}),
        (
            "Información General",
            {"fields": ("nombre", "rif", "federado", "email", "telefono")},
        ),
        (
            "Ubicación Geográfica",
            {"fields": ("estado", "municipio", "parroquia", "direccion")},
        ),
        ("Estado de la Cuenta", {"fields": ("activa", "eliminado", "fecha_registro")}),
    )


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ["cedula", "nombres", "apellidos", "institucion", "estado"]
    list_filter = ["estado", "institucion", "sexo"]
    search_fields = ["cedula", "nombres", "apellidos"]

    fieldsets = (
        (
            "Datos Personales",
            {
                "fields": (
                    "cedula",
                    "nombres",
                    "apellidos",
                    "fecha_nacimiento",
                    "sexo",
                    "email",
                    "telefono",
                    "direccion",
                )
            },
        ),
        ("Ubicación", {"fields": ("estado", "municipio")}),
        ("Institución", {"fields": ("institucion", "grado_escolar")}),
        (
            "Representante (para menores)",
            {
                "fields": (
                    "nombre_representante",
                    "cedula_representante",
                    "telefono_representante",
                    "email_representante",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("fecha_registro", "activo"), "classes": ("collapse",)},
        ),
    )


# 1. Definimos la acción
@admin.action(description="Aprobar y generar código RNR")
def aprobar_registros(modeladmin, request, queryset):
    count = 0
    for institucion in queryset:
        if institucion.aprobar_y_generar_codigo():
            count += 1
    modeladmin.message_user(request, f"Se han aprobado {count} instituciones correctamente.")

# 2. Intentamos desregistrar para evitar el error AlreadyRegistered
try:
    admin.site.unregister(Institucion)
except NotRegistered:
    pass

# 3. Registramos formalmente

@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rif', 'codigo', 'federado', 'activa')
    readonly_fields = ('codigo',) # Importante: que sea solo lectura
    exclude = ('tipo_federado',)
    list_filter = ('federado', 'activa')
    actions = ['aprobar_instituciones']

    def aprobar_instituciones(self, request, queryset):
        for inst in queryset:
            inst.activa = True
            inst.estatus = 'aprobado'
            # Al llamar a save(), si el codigo es TEMP-* se reemplaza por RNR...
            inst.save()
        self.message_user(request, "Las instituciones seleccionadas han sido aprobadas y sus codigos generados.")
    
    aprobar_instituciones.short_description = "Aprobar y generar códigos RNR"
