from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import UserProfile
from django import forms

# 1. Limpieza de registros previos
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

from django import forms

# 1. Formulario personalizado para el perfil
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('user_type', 'estado', 'institution', 'phone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer user_type requerido
        self.fields['user_type'].required = True

# 2. Inline para editar perfil dentro de Usuario
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Información de Perfil / Sede'
    fk_name = 'user'
    form = UserProfileForm
    # Campos que se pueden editar directamente en el usuario
    fields = ('user_type', 'estado', 'institution', 'phone')
    
    # Este método evita que se intente crear un nuevo perfil si ya existe
    def has_add_permission(self, request, obj=None):
        """Evitar crear nuevos perfiles desde el inline"""
        if obj and hasattr(obj, 'userprofile'):
            # Si el usuario ya tiene perfil, no permitir agregar otro
            return False
        return True
    
    def get_extra(self, request, obj=None):
        """No permitir agregar perfiles adicionales"""
        if obj and hasattr(obj, 'userprofile'):
            return 0
        return 1

# 3. Nuevo Admin de Usuarios
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "email", "get_user_type", "get_estado", "is_active", "is_staff")
    list_filter = ("is_staff", "is_active", "userprofile__user_type", "userprofile__estado")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    
    def save_model(self, request, obj, form, change):
        """Guardar el usuario y marcar para evitar creación duplicada de perfil"""
        if not change:  # Creando nuevo usuario
            obj._skip_profile_creation = True
        super().save_model(request, obj, form, change)
    
    @admin.display(description="Rol")
    def get_user_type(self, obj):
        try:
            return obj.userprofile.get_user_type_display()
        except: return "-"

    @admin.display(description="Estado/Sede")
    def get_estado(self, obj):
        try:
            return obj.userprofile.estado.nombre if obj.userprofile.estado else "-"
        except: return "-"

    # Aseguramos que el superusuario siempre tenga permiso a todo en el admin
    def has_module_permission(self, request):
        return True
    
    def has_view_permission(self, request, obj=None):
        return True

# 4. Admin de Perfiles (para ajustes finos)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_type", "estado", "institution", "phone", "created_at")
    list_filter = ("user_type", "estado", "created_at")
    search_fields = ("user__username", "phone", "user__email")
    readonly_fields = ("created_at", "updated_at")
    
    # Esto evita el error PermissionDenied al añadir perfiles
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True