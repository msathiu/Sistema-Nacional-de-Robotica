"""
Script de Verificación: Status de Instituciones
================================================

Este script verifica que las instituciones nuevas se registren correctamente
con status 'pendiente' y activa=False por defecto.

Uso:
    python manage.py shell < verificar_status_instituciones.py

O desde Django shell:
    exec(open('verificar_status_instituciones.py').read())
"""

from registry.models import Institucion
from django.contrib.auth.models import User
from users.models import UserProfile
from django.utils import timezone
from datetime import timedelta

print("\n" + "=" * 70)
print("VERIFICACIÓN DE STATUS DE INSTITUCIONES")
print("=" * 70 + "\n")

# 1. VERIFICAR INSTITUCIONES RECIENTES
print("1️⃣  INSTITUCIONES REGISTRADAS EN LAS ÚLTIMAS 24 HORAS")
print("-" * 70)

hace_24h = timezone.now() - timedelta(hours=24)
instituciones_recientes = Institucion.objects.filter(
    fecha_registro__gte=hace_24h
).order_by("-fecha_registro")

if instituciones_recientes.exists():
    for inst in instituciones_recientes:
        print(f"\n📋 Institución: {inst.nombre}")
        print(f"   Código: {inst.codigo}")
        print(f"   Estatus: {inst.estatus}")
        print(f"   Activa: {'✅ Sí' if inst.activa else '❌ No'}")
        print(f"   Fecha: {inst.fecha_registro.strftime('%d/%m/%Y %H:%M')}")

        # Verificar usuario asociado
        if inst.usuario:
            print(f"   Usuario: {inst.usuario.username}")
            print(f"   Usuario Activo: {'✅ Sí' if inst.usuario.is_active else '❌ No'}")
        else:
            print(f"   Usuario: ⚠️  No tiene usuario asociado")

        # Verificar coherencia
        if inst.estatus == "pendiente" and inst.activa:
            print(f"   ⚠️  ADVERTENCIA: Institución pendiente pero marcada como activa")
        elif inst.estatus == "aprobado" and not inst.activa:
            print(
                f"   ⚠️  ADVERTENCIA: Institución aprobada pero marcada como inactiva"
            )
        else:
            print(f"   ✅ Estado coherente")
else:
    print("ℹ️  No hay instituciones registradas en las últimas 24 horas")

# 2. RESUMEN GENERAL
print("\n\n2️⃣  RESUMEN GENERAL DE INSTITUCIONES")
print("-" * 70)

total = Institucion.objects.count()
pendientes = Institucion.objects.filter(estatus="pendiente").count()
aprobadas = Institucion.objects.filter(estatus="aprobado").count()
rechazadas = Institucion.objects.filter(estatus="rechazado").count()
activas = Institucion.objects.filter(activa=True).count()
inactivas = Institucion.objects.filter(activa=False).count()

print(f"\n📊 Total de Instituciones: {total}")
print(f"\n   Por Estatus:")
print(f"   - Pendientes: {pendientes}")
print(f"   - Aprobadas: {aprobadas}")
print(f"   - Rechazadas: {rechazadas}")
print(f"\n   Por Estado Activo:")
print(f"   - Activas: {activas}")
print(f"   - Inactivas: {inactivas}")

# 3. VERIFICAR INSTITUCIONES PENDIENTES
print("\n\n3️⃣  INSTITUCIONES PENDIENTES DE APROBACIÓN")
print("-" * 70)

pendientes_list = Institucion.objects.filter(estatus="pendiente").order_by(
    "-fecha_registro"
)[:10]

if pendientes_list.exists():
    print(f"\nℹ️  Mostrando las 10 más recientes de {pendientes} pendientes:\n")
    for inst in pendientes_list:
        dias = (timezone.now() - inst.fecha_registro).days
        print(f"   • {inst.nombre}")
        print(f"     Código: {inst.codigo}")
        print(f"     Email: {inst.email}")
        print(f"     Esperando: {dias} día(s)")
        print()
else:
    print("\n✅ No hay instituciones pendientes de aprobación")

# 4. VERIFICAR INCONSISTENCIAS
print("\n4️⃣  VERIFICACIÓN DE INCONSISTENCIAS")
print("-" * 70)

# Instituciones pendientes pero activas
inconsistencia_1 = Institucion.objects.filter(estatus="pendiente", activa=True)

if inconsistencia_1.exists():
    print(
        f"\n⚠️  PROBLEMA: {inconsistencia_1.count()} instituciones pendientes marcadas como activas:"
    )
    for inst in inconsistencia_1:
        print(f"   - {inst.nombre} (ID: {inst.id})")
else:
    print("\n✅ No hay instituciones pendientes marcadas como activas")

# Instituciones aprobadas pero inactivas
inconsistencia_2 = Institucion.objects.filter(
    estatus="aprobado", activa=False, eliminado=False
)

if inconsistencia_2.exists():
    print(
        f"\n⚠️  ADVERTENCIA: {inconsistencia_2.count()} instituciones aprobadas pero inactivas:"
    )
    for inst in inconsistencia_2:
        print(f"   - {inst.nombre} (ID: {inst.id})")
    print("   (Esto puede ser intencional si fueron suspendidas)")
else:
    print("✅ No hay instituciones aprobadas marcadas como inactivas")

# Instituciones con códigos temporales pero aprobadas
inconsistencia_3 = Institucion.objects.filter(
    estatus="aprobado", codigo__startswith="TEMP-"
)

if inconsistencia_3.exists():
    print(
        f"\n⚠️  PROBLEMA: {inconsistencia_3.count()} instituciones aprobadas con código temporal:"
    )
    for inst in inconsistencia_3:
        print(f"   - {inst.nombre} (Código: {inst.codigo})")
else:
    print("✅ No hay instituciones aprobadas con códigos temporales")

# Usuarios inactivos con instituciones aprobadas
inconsistencia_4 = User.objects.filter(
    institucion__estatus="aprobado", institucion__activa=True, is_active=False
)

if inconsistencia_4.exists():
    print(
        f"\n⚠️  PROBLEMA: {inconsistencia_4.count()} usuarios inactivos con instituciones aprobadas:"
    )
    for user in inconsistencia_4:
        print(f"   - {user.username} ({user.institucion.nombre})")
else:
    print("✅ No hay usuarios inactivos con instituciones aprobadas")

# 5. RECOMENDACIONES
print("\n\n5️⃣  RECOMENDACIONES")
print("-" * 70)

if pendientes > 0:
    print(f"\n📌 Hay {pendientes} instituciones esperando aprobación.")
    print("   Accede al panel de administración para revisarlas:")
    print("   Admin → Registry → Instituciones → Filtrar por 'Pendiente'")

if inconsistencia_1.exists() or inconsistencia_3.exists() or inconsistencia_4.exists():
    print("\n⚠️  Se detectaron inconsistencias que requieren atención.")
    print("   Ejecuta el script de corrección o contacta al equipo técnico.")
else:
    print("\n✅ El sistema está funcionando correctamente.")
    print("   Todas las instituciones tienen estados coherentes.")

print("\n" + "=" * 70)
print("VERIFICACIÓN COMPLETADA")
print("=" * 70 + "\n")
