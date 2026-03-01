from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from .models import UserProfile

# 1. Limpieza de registros previos
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# 1. Formulario personalizado para el perfil
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('user_type', 'institution', 'phone', 'estado', 'municipio', 'parroquia', 'ubicacion')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer user_type requerido
        self.fields['user_type'].required = True
        
        # Hacer municipio y parroquia opcionales
        self.fields['municipio'].required = False
        self.fields['parroquia'].required = False

# 2. Inline para editar perfil dentro de Usuario
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Información de Perfil / Sede'
    fk_name = 'user'
    form = UserProfileForm
    fields = ('user_type', 'institution', 'phone', 'estado', 'municipio', 'parroquia', 'ubicacion')
    extra = 1
    
    def get_extra(self, request, obj=None):
        # Mostrar 1 campo extra solo si estamos creando un usuario nuevo
        if obj is None:
            return 1  # Mostrar campos al crear usuario
        # Si el usuario existe, no mostrar campos extra (el perfil ya debe existir)
        return 0

    def has_add_permission(self, request, obj=None):
        # Permitir crear/editar perfiles en admin
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
        """Guardar el usuario. La señal creará automáticamente el perfil"""
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        """Manejar el guardado del formset para evitar duplicados de perfil"""
        if formset.model == UserProfile:
            # Obtener el usuario base
            user = form.instance
            instances = formset.save(commit=False)
            
            for instance in instances:
                # Usar get_or_create para evitar duplicados
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'user_type': instance.user_type,
                        'institution': instance.institution,
                        'phone': instance.phone,
                        'estado': instance.estado,
                        'municipio': instance.municipio,
                        'parroquia': instance.parroquia,
                        'ubicacion': instance.ubicacion,
                    }
                )
                # Si ya existe, actualizar los campos
                if not created:
                    profile.user_type = instance.user_type
                    profile.institution = instance.institution
                    profile.phone = instance.phone
                    profile.estado = instance.estado
                    profile.municipio = instance.municipio
                    profile.parroquia = instance.parroquia
                    profile.ubicacion = instance.ubicacion
                    profile.save()
        else:
            super().save_formset(request, form, formset, change)
    
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