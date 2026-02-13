from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    USER_TYPES = (
        ('participante', 'Participante'),
        ('institucional', 'Usuario Institucional'),
        ('admin', 'Administrador (Ministerio)'),
        ('superuser', 'Superusuario'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='participante')
    institution = models.ForeignKey('registry.Institucion', on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    estado = models.ForeignKey('registry.Estado', on_delete=models.SET_NULL, null=True, blank=True)
    municipio = models.ForeignKey('registry.Municipio', on_delete=models.SET_NULL, null=True, blank=True)
    parroquia = models.ForeignKey('registry.Parroquia', on_delete=models.SET_NULL, null=True, blank=True)
    ubicacion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

# Señales deshabilitadas - se manejan desde el admin y vistas
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         user_type = 'superuser' if instance.is_superuser else 'participante'
#         UserProfile.objects.get_or_create(user=instance, defaults={'user_type': user_type})

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     if hasattr(instance, 'userprofile'):
#         instance.userprofile.save()

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