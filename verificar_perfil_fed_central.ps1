# Script para verificar el perfil del usuario fed_central
# Uso: .\verificar_perfil_fed_central.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verificando perfiles de usuario fed_central" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio del proyecto
Set-Location "c:\Users\Argenis\Desktop\AREA_DE_TRABAJO_LIMPIO\club\SistemaRegistro"

# Ejecutar Django shell con el comando de verificación
python manage.py shell << 'EOF'
from users.models import UserProfile
from django.contrib.auth.models import User

print("=" * 60)
print("LISTADO DE PERFILES DE USUARIO")
print("=" * 60)

# Listar todos los perfiles
perfiles = UserProfile.objects.select_related('user', 'estado').all()

print(f"\nTotal de perfiles: {perfiles.count()}")
print("-" * 60)

for perfil in perfiles:
    print(f"\nUsuario: {perfil.user.username}")
    print(f"  Email: {perfil.user.email}")
    print(f"  User Type: {perfil.user_type}")
    print(f"  Estado: {perfil.estado.nombre if perfil.estado else 'Sin asignar'}")
    print(f"  Institution: {perfil.institution.nombre if perfil.institution else 'Sin asignar'}")
    print(f"  Activo: {perfil.user.is_active}")

# Buscar específicamente fed_central
print("\n" + "=" * 60)
print("BUSCANDO USUARIOS fed_central")
print("=" * 60)

fed_central_perfiles = UserProfile.objects.filter(user_type='fed_central')

if fed_central_perfiles.exists():
    print(f"\nSe encontraron {fed_central_perfiles.count()} usuario(s) con user_type='fed_central':")
    for perfil in fed_central_perfiles:
        print(f"\n  Usuario: {perfil.user.username}")
        print(f"  Email: {perfil.user.email}")
        print(f"  user_type: {perfil.user_type}")
else:
    print("\n¡ATENCIÓN! No se encontró ningún usuario con user_type='fed_central'")

# Verificar si hay usuarios que podrían ser fed_central pero tienen otro tipo
print("\n" + "=" * 60)
print("POSIBLES USUARIOS ADMINISTRATIVOS (que no sean superuser)")
print("=" * 60)

admin_users = User.objects.filter(is_superuser=False, is_staff=True)
for user in admin_users:
    try:
        perfil = user.userprofile
        print(f"\nUsuario: {user.username} - user_type: {perfil.user_type}")
    except:
        print(f"\nUsuario: {user.username} - SIN PERFIL")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETADA")
print("=" * 60)
EOF

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..." -ForegroundColor Yellow
$x = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
