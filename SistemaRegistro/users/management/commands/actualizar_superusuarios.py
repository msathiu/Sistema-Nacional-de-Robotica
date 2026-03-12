"""
Comando para actualizar perfiles de superusuarios existentes.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile


class Command(BaseCommand):
    help = 'Actualiza los perfiles de superusuarios existentes'

    def handle(self, *args, **options):
        superusers = User.objects.filter(is_superuser=True)
        updated = 0
        
        for user in superusers:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if profile.user_type != 'superuser':
                profile.user_type = 'superuser'
                profile.save()
                self.stdout.write(f'✅ Actualizado perfil de {user.username}')
                updated += 1
            else:
                self.stdout.write(f'ℹ️  {user.username} ya tiene perfil de superusuario')
        
        if updated > 0:
            self.stdout.write(self.style.SUCCESS(f'\n✅ {updated} perfiles actualizados'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Todos los superusuarios ya tienen sus perfiles correctos'))
