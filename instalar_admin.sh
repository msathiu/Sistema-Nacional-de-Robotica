#!/bin/bash

echo "Instalando django-jazzmin y aplicando cambios..."

# Instalar dependencias
pip install django-jazzmin==3.0.0

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

echo "✅ Instalación completada"
echo ""
echo "Reinicia el servidor para ver los cambios:"
echo "docker compose restart"
