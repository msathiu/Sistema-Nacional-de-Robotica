import logging

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils import timezone

class UserProfile(models.Model):
    USER_TYPES = (
        ('participante', 'Participante'),
        ('institucional', 'Usuario Institucional (Sedes/Matriz)'),
        ('fed_central', 'Federación Central (Ente Rector)'), # Único que aprueba
        ('fed_regional', 'Federación Regional (Delegación)'), # Solo ve su estado
        ('tecnologico', 'Administrador Tecnológico (Django)'), # Soporte técnico
        ('superuser', 'Superusuario'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=25, choices=USER_TYPES, default='participante')
    institution = models.ForeignKey('registry.Institucion', on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Ubicación para territorialidad (Crucial para Federación Regional)
    estado = models.ForeignKey('registry.Estado', on_delete=models.SET_NULL, null=True, blank=True)
    municipio = models.ForeignKey('registry.Municipio', on_delete=models.SET_NULL, null=True, blank=True)
    parroquia = models.ForeignKey('registry.Parroquia', on_delete=models.SET_NULL, null=True, blank=True)
    
    ubicacion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

    @property
    def es_federacion_central(self):
        return self.user_type == 'fed_central'

    @property
    def es_federacion_regional(self):
        return self.user_type == 'fed_regional'


@receiver(post_save, sender=UserProfile)
def sync_user_permissions(sender, instance, **kwargs):
    """Sincroniza permisos: Central y Tecnológico tienen acceso al admin (staff)"""
    user = instance.user
    updated = False
    
    # Superusuario y Tecnológico: Acceso total a infraestructura
    if instance.user_type in ['superuser', 'tecnologico']:
        if not (user.is_active and user.is_staff and user.is_superuser):
            user.is_active, user.is_staff, user.is_superuser = True, True, True
            updated = True
            
    # Federación Central: Acceso al panel administrativo pero no es superuser global
    elif instance.user_type == 'fed_central':
        if not user.is_active or not user.is_staff or user.is_superuser:
            user.is_active, user.is_staff, user.is_superuser = True, True, False
            updated = True
            
    # Resto de roles: Usuarios finales (Sin acceso al backend de Django)
    else:
        if not user.is_active or user.is_staff or user.is_superuser:
            user.is_active, user.is_staff, user.is_superuser = True, False, False
            updated = True
    
    if updated:
        user.save(update_fields=['is_active', 'is_staff', 'is_superuser'])


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Crea o actualiza el perfil automáticamente al tocar el usuario"""
    logger = logging.getLogger(__name__)
    
    try:
        if created:
            # Si se marca para saltar creación (ej. desde admin), no crear
            if hasattr(instance, '_skip_profile_creation') and instance._skip_profile_creation:
                return
            user_type = 'superuser' if instance.is_superuser else 'participante'
            # Usar get_or_create para evitar errores de duplicado
            profile, was_created = UserProfile.objects.get_or_create(
                user=instance, 
                defaults={'user_type': user_type}
            )
            if not was_created:
                logger.warning(f"El perfil para el usuario {instance.username} ya existía")
        else:
            # Actualizar perfil existente si el usuario se modifica
            try:
                profile = instance.userprofile
                # Sincronización inversa: si se activa superuser en admin, se refleja en el perfil
                if instance.is_active and instance.is_staff and instance.is_superuser:
                    if profile.user_type != 'superuser':
                        profile.user_type = 'superuser'
                        profile.save(update_fields=['user_type'])
            except UserProfile.DoesNotExist:
                # Si el perfil no existe, crearlo
                user_type = 'superuser' if instance.is_superuser else 'participante'
                UserProfile.objects.get_or_create(
                    user=instance, 
                    defaults={'user_type': user_type}
                )
            except Exception as e:
                logger.error(f"Error al actualizar perfil de usuario {instance.username}: {e}")
    except Exception as e:
        # Manejar cualquier error de integridad de base de datos
        logger.error(f"Error en señal create_or_update_user_profile para {instance.username}: {e}")

# Modelos de referencia para la base de datos externa (Managed=False)
class Estados(models.Model):
    id_estado = models.IntegerField(primary_key=True)
    estado = models.CharField(max_length=100)
    iso_3166_2 = models.CharField(max_length=4)

    class Meta:
        managed = False
        db_table = 'estados'

class Municipios(models.Model):
    id_municipio = models.IntegerField(primary_key=True)
    id_estado = models.ForeignKey(Estados, models.DO_NOTHING, db_column='id_estado')
    municipio = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'municipios'
