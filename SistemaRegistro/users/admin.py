from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from users.models import UserProfile

# 1. Quitar el registro por defecto de Django
admin.site.unregister(User)


# 2. Crear tu clase personalizada heredando de UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "get_user_type",
        "get_codigo_rnr",
        "is_staff",
        "is_superuser",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "userprofile__user_type")

    @admin.display(description="Tipo de Usuario")
    def get_user_type(self, obj):
        try:
            return obj.userprofile.get_user_type_display()
        except UserProfile.DoesNotExist:
            return "Sin Perfil"

    @admin.display(description="Código RNR")
    def get_codigo_rnr(self, obj):
        try:
            if hasattr(obj, "institucion"):
                return obj.institucion.codigo
            elif obj.userprofile.institution:
                return obj.userprofile.institution.codigo
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        return "Sin Código"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # La señal post_save se encarga de crear/actualizar el perfil automáticamente


# Registrar el modelo UserProfile en el admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "user_type",
        "institution",
        "phone",
        "get_ubicacion",
        "created_at",
    )
    list_filter = ("user_type", "created_at")
    search_fields = ("user__username", "user__email", "phone")
    list_editable = ("user_type",)
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "user",
        "user_type",
        "institution",
        "phone",
        "estado",
        "municipio",
        "parroquia",
        "ubicacion",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Ubicación")
    def get_ubicacion(self, obj):
        partes = []
        if obj.estado:
            partes.append(obj.estado.nombre)
        if obj.municipio:
            partes.append(obj.municipio.nombre)
        if obj.parroquia:
            partes.append(obj.parroquia.nombre)
        return " → ".join(partes) if partes else "-"
