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
    fields = ('user_type', 'estado', 'institution', 'phone')
    
    # TRUCO PROFESIONAL: 
    # Si estamos creando un usuario nuevo (obj es None), 
    # forzamos a que no se muestre el Inline para que no choque con la señal.
    def get_extra(self, request, obj=None):
        if obj is None:
            return 0 # No mostrar campos extra al crear
        return 0 if hasattr(obj, 'userprofile') else 1

    def has_add_permission(self, request, obj=None):
        # Si el usuario ya existe y ya tiene perfil, prohibido añadir otro
        if obj and hasattr(obj, 'userprofile'):
            return False
        # Si es un usuario nuevo, dejamos que la SEÑAL se encargue, no el Admin
        if obj is None:
            return False 
        return True

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