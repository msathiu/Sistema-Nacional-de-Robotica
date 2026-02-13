@echo off
REM Script de Prueba - Sistema de Ubicación en Cascada
REM Verifica que todas las funcionalidades estén correctamente implementadas

echo ==========================================
echo VERIFICACIÓN DE IMPLEMENTACIÓN
echo ==========================================
echo.

echo 1. Verificando estructura de archivos...
echo.

echo Comando createsuperuser:
if exist "SistemaRegistro\users\management\commands\createsuperuser.py" (
    echo [OK] createsuperuser.py
) else (
    echo [ERROR] createsuperuser.py NO ENCONTRADO
)

if exist "SistemaRegistro\users\management\commands\__init__.py" (
    echo [OK] __init__.py
) else (
    echo [ERROR] __init__.py NO ENCONTRADO
)
echo.

echo JavaScript para admin:
if exist "SistemaRegistro\static\admin\js\userprofile_location.js" (
    echo [OK] userprofile_location.js
) else (
    echo [ERROR] userprofile_location.js NO ENCONTRADO
)
echo.

echo Documentación:
if exist "IMPLEMENTACION_UBICACION_CASCADA.md" (
    echo [OK] IMPLEMENTACION_UBICACION_CASCADA.md
) else (
    echo [ERROR] IMPLEMENTACION_UBICACION_CASCADA.md NO ENCONTRADO
)

if exist "RESUMEN_IMPLEMENTACION_UBICACION.md" (
    echo [OK] RESUMEN_IMPLEMENTACION_UBICACION.md
) else (
    echo [ERROR] RESUMEN_IMPLEMENTACION_UBICACION.md NO ENCONTRADO
)
echo.

echo Template de ejemplo:
if exist "SistemaRegistro\templates\ejemplos\filtrado_cascada_ejemplo.html" (
    echo [OK] filtrado_cascada_ejemplo.html
) else (
    echo [ERROR] filtrado_cascada_ejemplo.html NO ENCONTRADO
)
echo.

echo ==========================================
echo 2. Verificando configuración en código...
echo ==========================================
echo.

findstr /C:"api/municipios" SistemaRegistro\users\urls.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ruta API municipios configurada
) else (
    echo [ERROR] Ruta API municipios NO configurada
)

findstr /C:"api/parroquias" SistemaRegistro\users\urls.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ruta API parroquias configurada
) else (
    echo [ERROR] Ruta API parroquias NO configurada
)

findstr /C:"def api_municipios" SistemaRegistro\users\views.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Vista api_municipios implementada
) else (
    echo [ERROR] Vista api_municipios NO implementada
)

findstr /C:"def api_parroquias" SistemaRegistro\users\views.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Vista api_parroquias implementada
) else (
    echo [ERROR] Vista api_parroquias NO implementada
)

findstr /C:"class Media:" SistemaRegistro\users\admin.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Media class configurada en admin
) else (
    echo [ERROR] Media class NO configurada en admin
)

echo.
echo ==========================================
echo 3. Próximos pasos
echo ==========================================
echo.
echo Para completar la configuración:
echo.
echo 1. Aplicar migraciones:
echo    cd SistemaRegistro
echo    python manage.py migrate
echo.
echo 2. Recolectar archivos estáticos:
echo    python manage.py collectstatic --noinput
echo.
echo 3. Probar comando createsuperuser:
echo    python manage.py createsuperuser
echo.
echo 4. Iniciar servidor y probar en admin:
echo    python manage.py runserver
echo    Ir a: http://localhost:8000/admin/users/userprofile/
echo.
echo ==========================================
echo VERIFICACIÓN COMPLETADA
echo ==========================================
echo.
pause
