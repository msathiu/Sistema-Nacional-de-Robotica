@echo off
REM Script de verificación de seguridad para Windows
REM SNR-PRO - Sistema Nacional de Robótica

echo ============================================================
echo   VERIFICACION DE SEGURIDAD - SNR-PRO
echo ============================================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "SistemaRegistro" (
    echo [ERROR] No se encuentra el directorio SistemaRegistro
    echo Por favor ejecuta este script desde la raiz del proyecto
    pause
    exit /b 1
)

echo [1/6] Verificando archivo .env...
if not exist ".env" (
    echo [X] Archivo .env NO encontrado
    echo [!] Copia .env.example a .env y configuralo
    set ERROR=1
) else (
    echo [OK] Archivo .env encontrado
)
echo.

echo [2/6] Verificando decorators.py...
if not exist "SistemaRegistro\users\decorators.py" (
    echo [X] Archivo decorators.py NO encontrado
    set ERROR=1
) else (
    echo [OK] Archivo decorators.py encontrado
)
echo.

echo [3/6] Verificando middleware.py...
if not exist "SistemaRegistro\users\middleware.py" (
    echo [X] Archivo middleware.py NO encontrado
    set ERROR=1
) else (
    echo [OK] Archivo middleware.py encontrado
)
echo.

echo [4/6] Verificando configuracion de seguridad en settings.py...
findstr /C:"RateLimitMiddleware" "SistemaRegistro\SistemaRegistro\settings.py" >nul
if errorlevel 1 (
    echo [X] RateLimitMiddleware NO configurado
    set ERROR=1
) else (
    echo [OK] RateLimitMiddleware configurado
)
echo.

echo [5/6] Verificando que no haya credenciales hardcodeadas...
findstr /C:"EMAIL_HOST_USER = \"470" "SistemaRegistro\SistemaRegistro\settings.py" >nul
if not errorlevel 1 (
    echo [X] CREDENCIALES HARDCODEADAS ENCONTRADAS
    echo [!] Las credenciales deben estar en .env, no en settings.py
    set ERROR=1
) else (
    echo [OK] No se encontraron credenciales hardcodeadas
)
echo.

echo [6/6] Verificando script de verificacion Python...
if not exist "verificar_seguridad.py" (
    echo [X] Script verificar_seguridad.py NO encontrado
    set ERROR=1
) else (
    echo [OK] Script verificar_seguridad.py encontrado
    echo.
    echo Ejecutando verificacion completa...
    python verificar_seguridad.py
)
echo.

echo ============================================================
if defined ERROR (
    echo   RESULTADO: ALGUNAS VERIFICACIONES FALLARON
    echo   Revisa los errores arriba y corrigelos
) else (
    echo   RESULTADO: TODAS LAS VERIFICACIONES PASARON
    echo   El sistema esta configurado de forma segura
)
echo ============================================================
echo.

if defined ERROR (
    echo.
    echo ACCIONES REQUERIDAS:
    echo 1. Si falta .env: cp .env.example .env
    echo 2. Configurar SECRET_KEY en .env
    echo 3. Configurar credenciales de email en .env
    echo 4. Ejecutar: python verificar_seguridad.py
    echo.
)

pause
