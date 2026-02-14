#!/bin/bash

# Colores para que sea fácil de leer
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

echo -e "${GREEN}--- 1. CORRIENDO BANDIT (Seguridad de Código) ---${NC}"
docker compose exec web bandit -r .

echo -e "\n${GREEN}--- 2. CORRIENDO PIP-AUDIT (Seguridad de Librerías) ---${NC}"
docker compose exec web pip-audit

echo -e "\n${GREEN}--- 3. CORRIENDO CHECK DEPLOY (Configuración Django) ---${NC}"
# Usamos DEBUG=False temporalmente para que el check analice la seguridad real
docker compose exec web python manage.py check --deploy --database default
