from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import UserProfile

# 1. Limpieza de registros previos
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# 2. Inline para editar perfil dentro de Usuario
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Información de Perfil / Sede'
    fk_name = 'user'
    # Campos que se pueden editar directamente en el usuario
    fields = ('user_type', 'estado', 'institution', 'phone')

# 3. Nuevo Admin de Usuarios
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "email", "get_user_type", "get_estado", "is_active", "is_staff")
    list_filter = ("is_staff", "is_active", "userprofile__user_type", "userprofile__estado")
    
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
    list_display = ("user", "user_type", "estado", "institution", "phone")
    list_filter = ("user_type", "estado")
    search_fields = ("user__username", "phone")
    
    # Esto evita el error PermissionDenied al añadir perfiles
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True