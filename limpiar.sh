#!/bin/bash
echo "Limpiando cache del sistema..."
docker compose exec web python manage.py limpiar_cache
echo ""
echo "Limpieza completada!"
