#!/bin/bash

echo "🚀 Aplicando migraciones del sistema institucional..."

# Aplicar migraciones
docker compose exec web python manage.py migrate

echo "✅ Migraciones aplicadas correctamente"
