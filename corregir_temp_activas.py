"""
Script de Corrección Rápida: Instituciones con Código Temporal
===============================================================

Este script corrige instituciones que tienen código temporal (TEMP-*)
pero están marcadas como activas.

Uso:
    cd SistemaRegistro
    python manage.py shell < corregir_temp_activas.py
"""

from registry.models import Institucion
from django.db import transaction

print("\n" + "=" * 70)
print("CORRECCIÓN: Instituciones con Código Temporal Activas")
print("=" * 70 + "\n")

# Buscar instituciones con código temporal pero activas
instituciones_problema = Institucion.objects.filter(
    codigo__startswith="TEMP-", activa=True
)

if instituciones_problema.exists():
    print(
        f"⚠️  Se encontraron {instituciones_problema.count()} instituciones con código temporal marcadas como activas:\n"
    )

    for inst in instituciones_problema:
        print(f"   • {inst.nombre}")
        print(f"     Código: {inst.codigo}")
        print(f"     Estatus: {inst.estatus}")
        print(f"     Activa: {inst.activa}")
        print()

    respuesta = input("\n¿Deseas corregirlas? (S/N): ").strip().upper()

    if respuesta == "S":
        with transaction.atomic():
            count = 0
            for inst in instituciones_problema:
                inst.activa = False
                inst.estatus = "pendiente"
                inst.save(update_fields=["activa", "estatus"])

                # Desactivar usuario asociado
                if inst.usuario:
                    inst.usuario.is_active = False
                    inst.usuario.save(update_fields=["is_active"])

                count += 1

            print(f"\n✅ {count} instituciones corregidas exitosamente.")
            print("\nCambios realizados:")
            print("   • activa = False")
            print("   • estatus = 'pendiente'")
            print("   • usuario.is_active = False")
    else:
        print("\n❌ Operación cancelada.")
else:
    print(
        "✅ No se encontraron instituciones con código temporal marcadas como activas."
    )
    print("   El sistema está funcionando correctamente.")

print("\n" + "=" * 70 + "\n")
