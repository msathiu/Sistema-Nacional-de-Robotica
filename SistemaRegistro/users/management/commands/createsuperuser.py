from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = "Crea un superusuario con perfil de tipo superusuario"

    def handle(self, *args, **options):
        # Ejecutar el comando original
        super().handle(*args, **options)

        # Obtener el usuario recién creado
        username = options.get("username")
        if username:
            from django.contrib.auth.models import User
            from users.models import UserProfile

            try:
                user = User.objects.get(username=username)
                # Actualizar el perfil (la señal ya lo creó)
                if hasattr(user, "userprofile"):
                    profile = user.userprofile
                    if profile.user_type != "superuser":
                        profile.user_type = "superuser"
                        profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Perfil de superusuario configurado para {username}"
                        )
                    )
            except User.DoesNotExist:
                raise CommandError(f"Usuario {username} no encontrado")
