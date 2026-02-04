from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# 1. Quitar el registro por defecto de Django
admin.site.unregister(User)


# 2. Crear tu clase personalizada heredando de UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Campos a mostrar en la tabla
    list_display = ("username", "email", "get_codigo_rnr", "is_staff")

    # Método para obtener el código desde la Institución
    @admin.display(description="Código RNR")
    def get_codigo_rnr(self, obj):
        if hasattr(obj, "institucion"):
            return obj.institucion.codigo
        return "Sin Código"

    # Si quieres que el código aparezca en el formulario de edición (solo lectura)
    readonly_fields = ("get_codigo_rnr",)
