"""
Comando de Django para verificar el perfil del usuario fed_central
Uso: python manage.py verificar_perfil
"""
from django.core.management.base import BaseCommand
from users.models import UserProfile
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Verifica los perfiles de usuario y especialmente fed_central'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('LISTADO DE PERFILES DE USUARIO')
        self.stdout.write('=' * 60)

        # Listar todos los perfiles
        perfiles = UserProfile.objects.select_related('user', 'estado').all()

        self.stdout.write(f'\nTotal de perfiles: {perfiles.count()}')
        self.stdout.write('-' * 60)

        for perfil in perfiles:
            self.stdout.write(f'\nUsuario: {perfil.user.username}')
            self.stdout.write(f'  Email: {perfil.user.email}')
            self.stdout.write(f'  User Type: {perfil.user_type}')
            self.stdout.write(f'  Estado: {perfil.estado.nombre if perfil.estado else "Sin asignar"}')
            self.stdout.write(f'  Institution: {perfil.institution.nombre if perfil.institution else "Sin asignar"}')
            self.stdout.write(f'  Activo: {perfil.user.is_active}')

        # Buscar específicamente fed_central
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('BUSCANDO USUARIOS fed_central')
        self.stdout.write('=' * 60)

        fed_central_perfiles = UserProfile.objects.filter(user_type='fed_central')

        if fed_central_perfiles.exists():
            self.stdout.write(f'\nSe encontraron {fed_central_perfiles.count()} usuario(s) con user_type="fed_central":')
            for perfil in fed_central_perfiles:
                self.stdout.write(f'\n  Usuario: {perfil.user.username}')
                self.stdout.write(f'  Email: {perfil.user.email}')
                self.stdout.write(f'  user_type: {perfil.user_type}')
        else:
            self.stdout.write(self.style.ERROR('\n¡ATENCIÓN! No se encontró ningún usuario con user_type="fed_central"'))

        # Verificar si hay usuarios que podrían ser fed_central pero tienen otro tipo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('USUARIOS CON is_staff=True (potenciales administradores)')
        self.stdout.write('=' * 60)

        admin_users = User.objects.filter(is_staff=True)
        for user in admin_users:
            try:
                perfil = user.userprofile
                self.stdout.write(f'\n  Usuario: {user.username} - user_type: {perfil.user_type}')
            except UserProfile.DoesNotExist:
                self.stdout.write(f'\n  Usuario: {user.username} - SIN PERFIL')

        # Verificar instituciones pendientes
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('INSTITUCIONES PENDIENTES DE APROBACIÓN')
        self.stdout.write('=' * 60)
        
        from registry.models import Institucion
        pendientes = Institucion.objects.filter(activa=False, eliminado=False, estatus='pendiente')
        self.stdout.write(f'\nTotal de instituciones pendientes: {pendientes.count()}')
        
        if pendientes.exists():
            for inst in pendientes[:10]:  # Mostrar solo las primeras 10
                self.stdout.write(f'  - {inst.nombre} (Estado: {inst.estado.nombre if inst.estado else "Sin estado"})')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('VERIFICACIÓN COMPLETADA')
        self.stdout.write('=' * 60)
