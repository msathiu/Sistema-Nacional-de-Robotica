from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    USER_TYPES = (
        ("participante", "Participante"),
        ("institucional", "Usuario Institucional"),
        ("admin", "Administrador (Ministerio)"),
        ("superuser", "Superusuario"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(
        max_length=20, choices=USER_TYPES, default="participante"
    )
    institution = models.ForeignKey(
        "registry.Institucion", on_delete=models.CASCADE, null=True, blank=True
    )
    phone = models.CharField(max_length=20, blank=True)
    estado = models.ForeignKey(
        "registry.Estado", on_delete=models.SET_NULL, null=True, blank=True
    )
    municipio = models.ForeignKey(
        "registry.Municipio", on_delete=models.SET_NULL, null=True, blank=True
    )
    parroquia = models.ForeignKey(
        "registry.Parroquia", on_delete=models.SET_NULL, null=True, blank=True
    )
    ubicacion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


@receiver(post_save, sender=UserProfile)
def sync_user_permissions(sender, instance, **kwargs):
    """Sincroniza los permisos del User según el tipo de usuario en el perfil."""
    user = instance.user
    updated = False

    if instance.user_type == "superuser":
        # Superusuario: activar los 3 checks
        if not user.is_active or not user.is_staff or not user.is_superuser:
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            updated = True
    elif instance.user_type == "admin":
        # Admin Ministerio: staff activo pero no superuser
        if not user.is_active or not user.is_staff or user.is_superuser:
            user.is_active = True
            user.is_staff = True
            user.is_superuser = False
            updated = True
    elif instance.user_type == "institucional":
        # Institucional: solo activo
        if not user.is_active or user.is_staff or user.is_superuser:
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            updated = True
    elif instance.user_type == "participante":
        # Participante: solo activo
        if not user.is_active or user.is_staff or user.is_superuser:
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            updated = True

    if updated:
        user.save(update_fields=["is_active", "is_staff", "is_superuser"])


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Crea o actualiza el perfil del usuario automáticamente."""
    if created:
        # Al crear: asignar tipo según permisos
        user_type = "superuser" if instance.is_superuser else "participante"
        UserProfile.objects.create(user=instance, user_type=user_type)
    else:
        # Al actualizar: verificar si debe ser superuser por los checks
        if hasattr(instance, "userprofile"):
            profile = instance.userprofile
            # Si tiene los 3 checks activos, cambiar a superuser
            if instance.is_active and instance.is_staff and instance.is_superuser:
                if profile.user_type != "superuser":
                    profile.user_type = "superuser"
                    profile.save(update_fields=["user_type"])
        else:
            # Si no tiene perfil, crearlo
            user_type = "superuser" if instance.is_superuser else "participante"
            UserProfile.objects.create(user=instance, user_type=user_type)


class Estados(models.Model):
    id_estado = models.IntegerField(primary_key=True)
    estado = models.CharField(max_length=100)
    iso_3166_2 = models.CharField(max_length=4)

    class Meta:
        managed = False
        db_table = "estados"


class Municipios(models.Model):
    id_municipio = models.IntegerField(primary_key=True)
    id_estado = models.ForeignKey(Estados, models.DO_NOTHING, db_column="id_estado")
    municipio = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "municipios"
