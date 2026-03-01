#!/bin/bash

# Script de verificación de roles y menús
# Verifica que los context processors y templates estén correctamente configurados

echo "🔍 Verificando corrección de menús por roles..."
echo ""

# Verificar que el context processor existe
echo "1️⃣ Verificando context processor user_roles..."
if grep -q "def user_roles" SistemaRegistro/registry/context_processors.py; then
    echo "   ✅ Context processor user_roles encontrado"
else
    echo "   ❌ Context processor user_roles NO encontrado"
    exit 1
fi

# Verificar que está registrado en settings
echo ""
echo "2️⃣ Verificando registro en settings.py..."
if grep -q "registry.context_processors.user_roles" SistemaRegistro/SistemaRegistro/settings.py; then
    echo "   ✅ Context processor registrado en settings"
else
    echo "   ❌ Context processor NO registrado en settings"
    exit 1
fi

# Verificar que el template tiene la lógica separada
echo ""
echo "3️⃣ Verificando separación de menús en base_dashboard.html..."
if grep -q "elif es_regional" SistemaRegistro/templates/users/base_dashboard.html; then
    echo "   ✅ Menú separado para federación regional"
else
    echo "   ❌ Menú NO separado correctamente"
    exit 1
fi

# Verificar que no hay opciones administrativas en el menú regional
echo ""
echo "4️⃣ Verificando que menú regional no tiene opciones administrativas..."
REGIONAL_MENU=$(sed -n '/{% elif es_regional %}/,/{% else %}/p' SistemaRegistro/templates/users/base_dashboard.html)

if echo "$REGIONAL_MENU" | grep -q "revisar_clubes"; then
    echo "   ❌ ERROR: Menú regional contiene 'revisar_clubes'"
    exit 1
fi

if echo "$REGIONAL_MENU" | grep -q "revisar_solicitudes_eliminacion"; then
    echo "   ❌ ERROR: Menú regional contiene 'revisar_solicitudes_eliminacion'"
    exit 1
fi

if echo "$REGIONAL_MENU" | grep -q "clubes_eliminados"; then
    echo "   ❌ ERROR: Menú regional contiene 'clubes_eliminados'"
    exit 1
fi

if echo "$REGIONAL_MENU" | grep -q "gestionar_sedes"; then
    echo "   ❌ ERROR: Menú regional contiene 'gestionar_sedes'"
    exit 1
fi

echo "   ✅ Menú regional no contiene opciones administrativas"

# Verificar que el menú regional tiene las opciones correctas
echo ""
echo "5️⃣ Verificando opciones permitidas en menú regional..."
if echo "$REGIONAL_MENU" | grep -q "lista_instituciones"; then
    echo "   ✅ Tiene 'lista_instituciones'"
else
    echo "   ❌ Falta 'lista_instituciones'"
fi

if echo "$REGIONAL_MENU" | grep -q "lista_participantes"; then
    echo "   ✅ Tiene 'lista_participantes'"
else
    echo "   ❌ Falta 'lista_participantes'"
fi

if echo "$REGIONAL_MENU" | grep -q "dashboard_metricas_clubes"; then
    echo "   ✅ Tiene 'dashboard_metricas_clubes'"
else
    echo "   ❌ Falta 'dashboard_metricas_clubes'"
fi

echo ""
echo "✅ Verificación completada exitosamente"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Reiniciar el servidor: python manage.py runserver"
echo "   2. Iniciar sesión con un usuario regional"
echo "   3. Verificar que solo vea las opciones permitidas"
echo ""
