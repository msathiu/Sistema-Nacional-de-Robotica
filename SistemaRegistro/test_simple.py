#!/usr/bin/env python
"""
Test simple de Reactivación de Instituciones Eliminadas
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SistemaRegistro.settings')
sys.path.insert(0, '/app')

django.setup()

from registry.models import Estado, Municipio, Parroquia, Institucion
from users.forms import InstitucionRegistrationForm

def test_reactivacion():
    print("Iniciando test de reactivación...")

    # Crear datos básicos
    estado, _ = Estado.objects.get_or_create(nombre="Miranda")
    municipio, _ = Municipio.objects.get_or_create(nombre="Los Teques", estado=estado)
    parroquia, _ = Parroquia.objects.get_or_create(nombre="San Juan", municipio=municipio)

    # Crear institución eliminada
    inst_eliminada = Institucion.objects.create(
        nombre='Colegio Test',
        tipo_institucion='educativa',
        codigo_mppe='ME999999',
        email='test@test.com',
        rif='J-12345678',
        estado=estado,
        municipio=municipio,
        parroquia=parroquia,
        eliminado=True,
        activa=False,
        estatus='aprobado'
    )

    print(f"Institución eliminada creada: {inst_eliminada.nombre} (ID: {inst_eliminada.id})")

    # Intentar registrar con mismos datos
    data = {
        'tipo_institucion': 'educativa',
        'naturaleza': 'publica',
        'subcategoria': 'primaria',
        'nombre': 'Colegio Test',
        'rif_letra': 'J',
        'rif_numero': '12345678',
        'codigo_mppe': 'ME999999',
        'estado': estado.id,
        'municipio': municipio.id,
        'parroquia': parroquia.id,
        'direccion': 'Calle Test',
        'email': 'test@test.com',
        'codigo_area': '0212',
        'numero_telefono': '1234567',
        'password': 'Test@1234',
        'confirm_password': 'Test@1234',
    }

    form = InstitucionRegistrationForm(data=data)
    is_valid = form.is_valid()

    print(f"Formulario válido: {is_valid}")

    if is_valid:
        inst_guardada = form.save()
        inst_guardada.refresh_from_db()

        print(f"Institución guardada ID: {inst_guardada.id}")
        print(f"Es la misma institución: {inst_guardada.id == inst_eliminada.id}")
        print(f"eliminado: {inst_guardada.eliminado}")
        print(f"activa: {inst_guardada.activa}")
        print(f"estatus: {inst_guardada.estatus}")

        # Verificar reactivación correcta
        if (inst_guardada.id == inst_eliminada.id and
            inst_guardada.eliminado == False and
            inst_guardada.activa == False and
            inst_guardada.estatus == "pendiente"):
            print("✅ TEST PASÓ: Reactivación exitosa")
            success = True
        else:
            print("❌ TEST FALLÓ: Reactivación incorrecta")
            success = False
    else:
        print(f"❌ Errores: {dict(form.errors)}")
        success = False

    # Limpiar
    inst_eliminada.delete()

    return success

if __name__ == '__main__':
    success = test_reactivacion()
    print(f"\nResultado final: {'PASÓ' if success else 'FALLÓ'}")
    sys.exit(0 if success else 1)</content>
<parameter name="filePath">/home/argenis/Escritorio/MiProyecto/sistemaRobotica/test_simple_reactivacion.py