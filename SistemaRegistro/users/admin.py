from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from users.models import UserProfile

# 1. Quitar el registro por defecto de Django
admin.site.unregister(User)

# 2. Crear tu clase personalizada heredando de UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "get_user_type", "get_codigo_rnr", "is_staff", "is_superuser")
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
        # Crear perfil si no existe
        if not change:
            user_type = 'superuser' if obj.is_superuser else 'participante'
            UserProfile.objects.get_or_create(user=obj, defaults={'user_type': user_type})

# Registrar el modelo UserProfile en el admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_type", "institution", "phone", "estado", "created_at")
    list_filter = ("user_type", "estado", "created_at")
    search_fields = ("user__username", "user__email", "phone", "ubicacion")
    list_editable = ("user_type",)
    readonly_fields = ("created_at", "updated_at")
    fields = ('user', 'user_type', 'institution', 'phone', 'estado', 'municipio', 'parroquia', 'ubicacion', 'created_at', 'updated_at')
    
    class Media:
        js = ('https://code.jquery.com/jquery-3.6.0.min.js', 'admin/js/userprofile_location.js',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "municipio":
            # Si hay un objeto siendo editado, cargar municipios del estado
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    profile = UserProfile.objects.get(pk=obj_id)
                    if profile.estado:
                        kwargs["queryset"] = db_field.related_model.objects.filter(estado=profile.estado)
                    else:
                        kwargs["queryset"] = db_field.related_model.objects.none()
                except UserProfile.DoesNotExist:
                    kwargs["queryset"] = db_field.related_model.objects.none()
            else:
                kwargs["queryset"] = db_field.related_model.objects.none()
        
        if db_field.name == "parroquia":
            # Si hay un objeto siendo editado, cargar parroquias del municipio
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    profile = UserProfile.objects.get(pk=obj_id)
                    if profile.municipio:
                        kwargs["queryset"] = db_field.related_model.objects.filter(municipio=profile.municipio)
                    else:
                        kwargs["queryset"] = db_field.related_model.objects.none()
                except UserProfile.DoesNotExist:
                    kwargs["queryset"] = db_field.related_model.objects.none()
            else:
                kwargs["queryset"] = db_field.related_model.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
