from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Crea un superusuario con perfil de tipo superusuario'

    def handle(self, *args, **options):
        # Ejecutar el comando original
        super().handle(*args, **options)
        
        # Obtener el usuario recién creado
        username = options.get('username')
        if username:
            from django.contrib.auth.models import User
            from users.models import UserProfile
            
            try:
                user = User.objects.get(username=username)
                # Crear o actualizar el perfil con tipo superusuario
                UserProfile.objects.update_or_create(
                    user=user,
                    defaults={'user_type': 'superuser'}
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Perfil de superusuario creado para {username}')
                )
            except User.DoesNotExist:
                raise CommandError(f'Usuario {username} no encontrado')
