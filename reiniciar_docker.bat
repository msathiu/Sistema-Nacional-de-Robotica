@echo off
echo Reiniciando Docker y aplicando cambios...
echo.

cd SistemaRegistro

echo 1. Recolectando archivos estaticos...
python manage.py collectstatic --noinput --clear

echo.
echo 2. Reiniciando contenedor Docker...
cd ..
docker compose restart

echo.
echo COMPLETADO. Prueba ahora en el admin.
pause
