@echo off
chcp 65001 >nul
echo.
echo ========================================================================
echo   GESTIÓN DE STATUS DE INSTITUCIONES - SNR-PRO
echo ========================================================================
echo.
echo   Este script te ayudará a verificar y corregir el estado de las
echo   instituciones en el sistema.
echo.
echo ========================================================================
echo.

:MENU
echo.
echo   Selecciona una opción:
echo.
echo   [1] Verificar status de instituciones
echo   [2] Corregir inconsistencias (requiere confirmación)
echo   [3] Ver instituciones pendientes de aprobación
echo   [4] Salir
echo.
set /p opcion="   Ingresa el número de tu opción: "

if "%opcion%"=="1" goto VERIFICAR
if "%opcion%"=="2" goto CORREGIR
if "%opcion%"=="3" goto PENDIENTES
if "%opcion%"=="4" goto SALIR

echo.
echo   ⚠️  Opción inválida. Intenta de nuevo.
goto MENU

:VERIFICAR
echo.
echo ========================================================================
echo   VERIFICANDO STATUS DE INSTITUCIONES...
echo ========================================================================
echo.
cd SistemaRegistro
python manage.py shell < ..\verificar_status_instituciones.py
cd ..
echo.
echo   Presiona cualquier tecla para volver al menú...
pause >nul
goto MENU

:CORREGIR
echo.
echo ========================================================================
echo   ⚠️  ADVERTENCIA: CORRECCIÓN DE INCONSISTENCIAS
echo ========================================================================
echo.
echo   Este proceso modificará datos en la base de datos.
echo   Se recomienda hacer un backup antes de continuar.
echo.
set /p confirmar="   ¿Deseas continuar? (S/N): "

if /i "%confirmar%"=="S" goto EJECUTAR_CORRECCION
if /i "%confirmar%"=="N" goto MENU

echo   Opción inválida.
goto CORREGIR

:EJECUTAR_CORRECCION
echo.
echo   Ejecutando correcciones...
echo.
cd SistemaRegistro
python manage.py shell < ..\corregir_status_instituciones.py
cd ..
echo.
echo   Presiona cualquier tecla para volver al menú...
pause >nul
goto MENU

:PENDIENTES
echo.
echo ========================================================================
echo   INSTITUCIONES PENDIENTES DE APROBACIÓN
echo ========================================================================
echo.
cd SistemaRegistro
python manage.py shell -c "from registry.models import Institucion; from django.utils import timezone; pendientes = Institucion.objects.filter(estatus='pendiente').order_by('-fecha_registro'); print(f'\n📋 Total de instituciones pendientes: {pendientes.count()}\n'); [print(f'  • {inst.nombre}\n    Código: {inst.codigo}\n    Email: {inst.email}\n    Fecha: {inst.fecha_registro.strftime(\"%%d/%%m/%%Y %%H:%%M\")}\n    Días esperando: {(timezone.now() - inst.fecha_registro).days}\n') for inst in pendientes[:10]]; print(f'\n💡 Para aprobar instituciones:\n   1. Accede al panel de administración\n   2. Ve a Registry → Instituciones\n   3. Filtra por estatus \"Pendiente\"\n   4. Selecciona las instituciones\n   5. Ejecuta la acción \"Aprobar y generar códigos RNR\"\n')"
cd ..
echo.
echo   Presiona cualquier tecla para volver al menú...
pause >nul
goto MENU

:SALIR
echo.
echo   ¡Hasta luego!
echo.
exit /b 0
