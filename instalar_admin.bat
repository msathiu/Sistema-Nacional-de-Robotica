@echo off
echo Instalando django-jazzmin y aplicando cambios...
echo.

cd SistemaRegistro

pip install django-jazzmin==3.0.0

python manage.py collectstatic --noinput

echo.
echo Instalacion completada
echo.
echo Reinicia Docker:
echo docker compose restart
echo.
pause
