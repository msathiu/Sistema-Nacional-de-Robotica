#!/bin/bash

# Script de Prueba - Sistema de Ubicación en Cascada
# Verifica que todas las funcionalidades estén correctamente implementadas

echo "=========================================="
echo "VERIFICACIÓN DE IMPLEMENTACIÓN"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar archivos
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (NO ENCONTRADO)"
        return 1
    fi
}

# Función para verificar directorios
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (NO ENCONTRADO)"
        return 1
    fi
}

echo "1. Verificando estructura de archivos..."
echo ""

# Verificar comando personalizado
echo "Comando createsuperuser:"
check_dir "SistemaRegistro/users/management"
check_dir "SistemaRegistro/users/management/commands"
check_file "SistemaRegistro/users/management/commands/__init__.py"
check_file "SistemaRegistro/users/management/commands/createsuperuser.py"
echo ""

# Verificar JavaScript
echo "JavaScript para admin:"
check_dir "SistemaRegistro/static/admin"
check_dir "SistemaRegistro/static/admin/js"
check_file "SistemaRegistro/static/admin/js/userprofile_location.js"
echo ""

# Verificar documentación
echo "Documentación:"
check_file "IMPLEMENTACION_UBICACION_CASCADA.md"
check_file "RESUMEN_IMPLEMENTACION_UBICACION.md"
echo ""

# Verificar ejemplo
echo "Template de ejemplo:"
check_dir "SistemaRegistro/templates/ejemplos"
check_file "SistemaRegistro/templates/ejemplos/filtrado_cascada_ejemplo.html"
echo ""

echo "=========================================="
echo "2. Verificando configuración en código..."
echo "=========================================="
echo ""

# Verificar que las rutas API estén en urls.py
if grep -q "api/municipios" SistemaRegistro/users/urls.py; then
    echo -e "${GREEN}✓${NC} Ruta API municipios configurada"
else
    echo -e "${RED}✗${NC} Ruta API municipios NO configurada"
fi

if grep -q "api/parroquias" SistemaRegistro/users/urls.py; then
    echo -e "${GREEN}✓${NC} Ruta API parroquias configurada"
else
    echo -e "${RED}✗${NC} Ruta API parroquias NO configurada"
fi

# Verificar que las vistas API existan
if grep -q "def api_municipios" SistemaRegistro/users/views.py; then
    echo -e "${GREEN}✓${NC} Vista api_municipios implementada"
else
    echo -e "${RED}✗${NC} Vista api_municipios NO implementada"
fi

if grep -q "def api_parroquias" SistemaRegistro/users/views.py; then
    echo -e "${GREEN}✓${NC} Vista api_parroquias implementada"
else
    echo -e "${RED}✗${NC} Vista api_parroquias NO implementada"
fi

# Verificar que el admin tenga Media class
if grep -q "class Media:" SistemaRegistro/users/admin.py; then
    echo -e "${GREEN}✓${NC} Media class configurada en admin"
else
    echo -e "${RED}✗${NC} Media class NO configurada en admin"
fi

echo ""
echo "=========================================="
echo "3. Próximos pasos"
echo "=========================================="
echo ""
echo -e "${YELLOW}Para completar la configuración:${NC}"
echo ""
echo "1. Aplicar migraciones:"
echo "   cd SistemaRegistro"
echo "   python manage.py migrate"
echo ""
echo "2. Recolectar archivos estáticos:"
echo "   python manage.py collectstatic --noinput"
echo ""
echo "3. Probar comando createsuperuser:"
echo "   python manage.py createsuperuser"
echo ""
echo "4. Iniciar servidor y probar en admin:"
echo "   python manage.py runserver"
echo "   Ir a: http://localhost:8000/admin/users/userprofile/"
echo ""
echo "=========================================="
echo "VERIFICACIÓN COMPLETADA"
echo "=========================================="
