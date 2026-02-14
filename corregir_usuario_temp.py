"""
Corrección: Usuario TEMP-EE7CE070
==================================
"""
from registry.models import Institucion

inst = Institucion.objects.get(codigo="TEMP-EE7CE070")
print(f"Institución: {inst.nombre}")
print(f"Activa: {inst.activa}")
print(f"Estatus: {inst.estatus}")

if inst.usuario:
    print(f"Usuario: {inst.usuario.username}")
    print(f"Usuario is_active: {inst.usuario.is_active}")

    # Corregir
    inst.usuario.is_active = False
    inst.usuario.save()
    print("✅ Usuario corregido: is_active = False")
else:
    print("⚠️ No tiene usuario asociado")
