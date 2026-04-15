"""
Comando para crear usuarios administradores del ministerio.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile
import getpass


class Command(BaseCommand):
    help = "Crea un usuario administrador del ministerio"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Nombre de usuario")
        parser.add_argument("email", type=str, help="Correo electrónico")

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'❌ El usuario "{username}" ya existe'))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'❌ El correo "{email}" ya está registrado')
            )
            return

        # Solicitar contraseña
        password = getpass.getpass("Contraseña: ")
        password_confirm = getpass.getpass("Confirmar contraseña: ")

        if password != password_confirm:
            self.stdout.write(self.style.ERROR("❌ Las contraseñas no coinciden"))
            return

        if len(password) < 8:
            self.stdout.write(
                self.style.ERROR("❌ La contraseña debe tener al menos 8 caracteres")
            )
            return

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_active=True,
        )

        # Actualizar perfil (la señal ya lo creó automáticamente)
        profile = UserProfile.objects.get(user=user)
        profile.user_type = "admin"
        profile.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Usuario administrador "{username}" creado exitosamente'
            )
        )
        self.stdout.write(f"   📧 Email: {email}")
        self.stdout.write(f"   👤 Tipo: Administrador (Ministerio)")
