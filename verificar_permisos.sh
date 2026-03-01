#!/bin/bash

# Script de verificación de correcciones de permisos
echo "🔍 Verificando correcciones de permisos..."
echo ""

ERRORES=0

# 1. Verificar corrección en views_avanzadas.py
echo "1️⃣ Verificando views_avanzadas.py..."

if grep -q "user_type not in \['fed_central', 'superuser'\]" SistemaRegistro/registry/views_avanzadas.py; then
    echo "   ✅ clubes_eliminados() corregido"
else
    echo "   ❌ clubes_eliminados() NO corregido"
    ERRORES=$((ERRORES + 1))
fi

if grep -q "def restaurar_club" SistemaRegistro/registry/views_avanzadas.py && \
   grep -A 5 "def restaurar_club" SistemaRegistro/registry/views_avanzadas.py | grep -q "fed_central"; then
    echo "   ✅ restaurar_club() corregido"
else
    echo "   ❌ restaurar_club() NO corregido"
    ERRORES=$((ERRORES + 1))
fi

if grep -q "def eliminar_permanente_club" SistemaRegistro/registry/views_avanzadas.py && \
   grep -A 5 "def eliminar_permanente_club" SistemaRegistro/registry/views_avanzadas.py | grep -q "fed_central"; then
    echo "   ✅ eliminar_permanente_club() corregido"
else
    echo "   ❌ eliminar_permanente_club() NO corregido"
    ERRORES=$((ERRORES + 1))
fi

# 2. Verificar corrección en views_reportes.py
echo ""
echo "2️⃣ Verificando views_reportes.py..."

if grep -q "@login_required" SistemaRegistro/registry/views_reportes.py && \
   grep -A 10 "def dashboard_metricas_clubes" SistemaRegistro/registry/views_reportes.py | grep -q "es_regional"; then
    echo "   ✅ dashboard_metricas_clubes() refactorizado"
else
    echo "   ❌ dashboard_metricas_clubes() NO refactorizado"
    ERRORES=$((ERRORES + 1))
fi

if grep -A 20 "def dashboard_metricas_clubes" SistemaRegistro/registry/views_reportes.py | grep -q "clubes_base"; then
    echo "   ✅ Filtrado por estado implementado"
else
    echo "   ❌ Filtrado por estado NO implementado"
    ERRORES=$((ERRORES + 1))
fi

# 3. Verificar corrección en views_institucional.py
echo ""
echo "3️⃣ Verificando views_institucional.py..."

if grep -A 5 "def mis_notificaciones" SistemaRegistro/registry/views_institucional.py | grep -q "Notificacion.objects.filter"; then
    echo "   ✅ mis_notificaciones() corregido"
else
    echo "   ❌ mis_notificaciones() NO corregido"
    ERRORES=$((ERRORES + 1))
fi

if grep -A 5 "def marcar_todas_leidas" SistemaRegistro/registry/views_institucional.py | grep -q "Notificacion.objects.filter"; then
    echo "   ✅ marcar_todas_leidas() corregido"
else
    echo "   ❌ marcar_todas_leidas() NO corregido"
    ERRORES=$((ERRORES + 1))
fi

# Resumen
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORES -eq 0 ]; then
    echo "✅ Todas las verificaciones pasaron correctamente"
    echo ""
    echo "📝 Próximos pasos:"
    echo "   1. Reiniciar el servidor: python manage.py runserver"
    echo "   2. Probar con Fed. Central → Papelera"
    echo "   3. Probar con Fed. Regional → Métricas Clubes"
    echo "   4. Probar con Institucional → Notificaciones"
else
    echo "❌ Se encontraron $ERRORES errores"
    echo "   Revisar los archivos manualmente"
    exit 1
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
