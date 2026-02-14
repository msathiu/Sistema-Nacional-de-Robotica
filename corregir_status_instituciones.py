"""
Script de Corrección: Status de Instituciones
==============================================

Este script corrige instituciones con estados inconsistentes.

⚠️  ADVERTENCIA: Este script modifica datos en la base de datos.
    Asegúrate de hacer un backup antes de ejecutarlo.

Uso:
    python manage.py shell < corregir_status_instituciones.py
"""

from registry.models import Institucion
from django.contrib.auth.models import User
from django.db import transaction

print("\n" + "=" * 70)
print("CORRECCIÓN DE STATUS DE INSTITUCIONES")
print("=" * 70 + "\n")

# Contador de correcciones
correcciones = {
    "pendientes_activadas": 0,
    "aprobadas_desactivadas": 0,
    "codigos_temporales": 0,
    "usuarios_desactivados": 0,
}

# 1. CORREGIR INSTITUCIONES PENDIENTES MARCADAS COMO ACTIVAS
print("1️⃣  Corrigiendo instituciones pendientes marcadas como activas...")
print("-" * 70)

with transaction.atomic():
    instituciones_problema = Institucion.objects.filter(
        estatus="pendiente", activa=True
    )

    if instituciones_problema.exists():
        for inst in instituciones_problema:
            print(f"   Corrigiendo: {inst.nombre}")
            inst.activa = False
            inst.save(update_fields=["activa"])

            # Desactivar usuario asociado
            if inst.usuario and inst.usuario.is_active:
                inst.usuario.is_active = False
                inst.usuario.save(update_fields=["is_active"])
                print(f"   - Usuario desactivado: {inst.usuario.username}")

            correcciones["pendientes_activadas"] += 1

        print(f"\n✅ {correcciones['pendientes_activadas']} instituciones corregidas")
    else:
        print("✅ No se encontraron instituciones pendientes marcadas como activas")

# 2. CORREGIR INSTITUCIONES APROBADAS CON CÓDIGOS TEMPORALES
print("\n\n2️⃣  Corrigiendo instituciones aprobadas con códigos temporales...")
print("-" * 70)

with transaction.atomic():
    instituciones_temp = Institucion.objects.filter(
        estatus="aprobado", activa=True, codigo__startswith="TEMP-"
    )

    if instituciones_temp.exists():
        for inst in instituciones_temp:
            print(f"   Generando código RNR para: {inst.nombre}")
            codigo_anterior = inst.codigo

            # Generar código RNR
            try:
                nuevo_codigo = inst.generar_codigo_rnr()
                inst.codigo = nuevo_codigo
                inst.save(update_fields=["codigo"])

                # Actualizar username del usuario
                if inst.usuario:
                    inst.usuario.username = nuevo_codigo
                    inst.usuario.save(update_fields=["username"])
                    print(f"   - Código: {codigo_anterior} → {nuevo_codigo}")

                correcciones["codigos_temporales"] += 1
            except Exception as e:
                print(f"   ⚠️  Error al generar código: {e}")

        print(f"\n✅ {correcciones['codigos_temporales']} códigos RNR generados")
    else:
        print("✅ No se encontraron instituciones aprobadas con códigos temporales")

# 3. SINCRONIZAR USUARIOS CON INSTITUCIONES APROBADAS
print("\n\n3️⃣  Sincronizando usuarios con instituciones aprobadas...")
print("-" * 70)

with transaction.atomic():
    usuarios_problema = User.objects.filter(
        institucion__estatus="aprobado", institucion__activa=True, is_active=False
    )

    if usuarios_problema.exists():
        for user in usuarios_problema:
            print(f"   Activando usuario: {user.username}")
            user.is_active = True
            user.save(update_fields=["is_active"])
            correcciones["usuarios_desactivados"] += 1

        print(f"\n✅ {correcciones['usuarios_desactivados']} usuarios activados")
    else:
        print("✅ Todos los usuarios están sincronizados correctamente")

# 4. VERIFICAR INSTITUCIONES APROBADAS PERO INACTIVAS (SUSPENDIDAS)
print("\n\n4️⃣  Verificando instituciones suspendidas...")
print("-" * 70)

instituciones_suspendidas = Institucion.objects.filter(
    estatus="aprobado", activa=False, eliminado=False
)

if instituciones_suspendidas.exists():
    print(
        f"\nℹ️  Se encontraron {instituciones_suspendidas.count()} instituciones suspendidas:"
    )
    for inst in instituciones_suspendidas:
        print(f"   • {inst.nombre} (ID: {inst.id})")
    print("\n   Estas instituciones fueron aprobadas pero luego suspendidas.")
    print("   Si esto es intencional, no se requiere acción.")
    print("   Si deseas reactivarlas, hazlo manualmente desde el admin.")
else:
    print("✅ No hay instituciones suspendidas")

# RESUMEN DE CORRECCIONES
print("\n\n" + "=" * 70)
print("RESUMEN DE CORRECCIONES")
print("=" * 70)

total_correcciones = sum(correcciones.values())

if total_correcciones > 0:
    print(f"\n✅ Se realizaron {total_correcciones} correcciones:")
    print(
        f"   • Instituciones pendientes corregidas: {correcciones['pendientes_activadas']}"
    )
    print(f"   • Códigos RNR generados: {correcciones['codigos_temporales']}")
    print(f"   • Usuarios activados: {correcciones['usuarios_desactivados']}")
    print("\n📌 Recomendación: Ejecuta el script de verificación para confirmar.")
else:
    print(
        "\n✅ No se requirieron correcciones. El sistema está funcionando correctamente."
    )

print("\n" + "=" * 70 + "\n")
