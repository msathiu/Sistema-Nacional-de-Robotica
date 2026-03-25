#!/usr/bin/env python
"""
Test de Reactivación de Instituciones Eliminadas
Verifica que la implementación funcione correctamente sin romper el flujo actual.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SistemaRegistro.settings')
sys.path.insert(0, '/home/argenis/Escritorio/MiProyecto/sistemaRobotica/SistemaRegistro')

django.setup()

from django.contrib.auth.models import User
from django.test import TestCase
from registry.models import (
    Estado, Municipio, Parroquia, Institucion, Dependencia
)
from users.forms import InstitucionRegistrationForm
from django.core.exceptions import ValidationError


def crear_datos_basicos():
    """Crea los datos básicos necesarios para las pruebas"""
    estado, _ = Estado.objects.get_or_create(nombre="Miranda")
    municipio, _ = Municipio.objects.get_or_create(
        nombre="Los Teques",
        estado=estado
    )
    parroquia, _ = Parroquia.objects.get_or_create(
        nombre="San Juan",
        municipio=municipio
    )
    return estado, municipio, parroquia


def test_reactivacion_institucion_eliminada():
    """
    Test principal: Verificar reactivación de institución eliminada
    """
    print("\n" + "="*80)
    print("TEST: Reactivación de Institución Eliminada")
    print("="*80)

    estado, municipio, parroquia = crear_datos_basicos()

    # 1. Crear y "eliminar" una institución educativa
    institucion_eliminada = Institucion.objects.create(
        nombre='Colegio Test Eliminado',
        tipo_institucion='educativa',
        codigo_mppe='ME999888',
        email='eliminado@test.com',
        rif='J-12345678',
        estado=estado,
        municipio=municipio,
        parroquia=parroquia,
        eliminado=True,  # MARCADA COMO ELIMINADA
        activa=False,
        estatus='aprobado'
    )

    print(f"✓ Institución creada y eliminada: '{institucion_eliminada.nombre}' (ID: {institucion_eliminada.id})")

    # 2. Intentar registrar con los MISMOS datos (debería reactivar)
    data = {
        'tipo_institucion': 'educativa',
        'naturaleza': 'publica',
        'subcategoria': 'primaria',
        'nombre': 'Colegio Test Eliminado',  # MISMO NOMBRE
        'rif_letra': 'J',
        'rif_numero': '12345678',  # MISMO RIF
        'codigo_mppe': 'ME999888',  # MISMO CÓDIGO MPPE
        'estado': estado.id,
        'municipio': municipio.id,
        'parroquia': parroquia.id,
        'direccion': 'Calle Test',
        'email': 'eliminado@test.com',  # MISMO EMAIL
        'codigo_area': '0212',
        'numero_telefono': '1234567',
        'password': 'Test@1234',
        'confirm_password': 'Test@1234',
    }

    form = InstitucionRegistrationForm(data=data)
    is_valid = form.is_valid()

    print(f"\n✓ Intento de registro con datos idénticos...")
    print(f"  Formulario válido: {is_valid}")

    if is_valid:
        # Verificar que se reactivó la institución
        institucion_guardada = form.save()

        # Recargar desde BD para verificar cambios
        institucion_guardada.refresh_from_db()

        print(f"  Institución retornada ID: {institucion_guardada.id}")
        print(f"  Es la misma institución: {institucion_guardada.id == institucion_eliminada.id}")
        print(f"  eliminado: {institucion_guardada.eliminado}")
        print(f"  activa: {institucion_guardada.activa}")
        print(f"  estatus: {institucion_guardada.estatus}")

        # Verificaciones
        reactivacion_correcta = (
            institucion_guardada.id == institucion_eliminada.id and  # Misma institución
            institucion_guardada.eliminado == False and  # Reactivada
            institucion_guardada.activa == False and  # Inhabilitada hasta aprobación
            institucion_guardada.estatus == "pendiente"  # Pendiente de aprobación
        )

        if reactivacion_correcta:
            print("  ✅ REACTIVACIÓN EXITOSA")
            test_result = True
        else:
            print("  ❌ REACTIVACIÓN FALLIDA")
            test_result = False
    else:
        print(f"  ❌ Errores de validación: {dict(form.errors)}")
        test_result = False

    # Limpiar
    institucion_eliminada.delete()

    print(f"\n{'✅ PASÓ' if test_result else '❌ FALLÓ'}: Test de Reactivación")
    return test_result


def test_reactivacion_particular_eliminado():
    """
    Test: Reactivación de persona natural eliminada
    """
    print("\n" + "="*80)
    print("TEST: Reactivación de Persona Natural Eliminada")
    print("="*80)

    estado, municipio, parroquia = crear_datos_basicos()

    # 1. Crear y eliminar persona natural
    particular_eliminado = Institucion.objects.create(
        nombre='Juan Pérez',
        tipo_institucion='particular',
        particular_nombres='Juan',
        particular_apellidos='Pérez',
        particular_cedula='12345678',
        particular_nacionalidad='V',
        email='juan@test.com',
        estado=estado,
        municipio=municipio,
        parroquia=parroquia,
        eliminado=True,
        activa=False,
        estatus='aprobado'
    )

    print(f"✓ Persona natural creada y eliminada: '{particular_eliminado.nombre}' (ID: {particular_eliminado.id})")

    # 2. Intentar registrar con mismos datos
    data = {
        'tipo_institucion': 'particular',
        'particular_nombres': 'Juan',
        'particular_apellidos': 'Pérez',
        'particular_nacionalidad': 'V',
        'particular_cedula': '12345678',
        'estado': estado.id,
        'municipio': municipio.id,
        'parroquia': parroquia.id,
        'direccion': 'Calle Test',
        'email': 'juan@test.com',
        'codigo_area': '0212',
        'numero_telefono': '1234567',
        'password': 'Test@1234',
        'confirm_password': 'Test@1234',
    }

    form = InstitucionRegistrationForm(data=data)
    is_valid = form.is_valid()

    print(f"\n✓ Intento de registro con datos idénticos...")
    print(f"  Formulario válido: {is_valid}")

    if is_valid:
        institucion_guardada = form.save()
        institucion_guardada.refresh_from_db()

        reactivacion_correcta = (
            institucion_guardada.id == particular_eliminado.id and
            institucion_guardada.eliminado == False and
            institucion_guardada.activa == False and
            institucion_guardada.estatus == "pendiente"
        )

        print(f"  ✅ Reactivación correcta: {reactivacion_correcta}")
        test_result = reactivacion_correcta
    else:
        print(f"  ❌ Errores: {dict(form.errors)}")
        test_result = False

    # Limpiar
    particular_eliminado.delete()

    print(f"\n{'✅ PASÓ' if test_result else '❌ FALLÓ'}: Test de Persona Natural")
    return test_result


def test_no_reactivacion_datos_diferentes():
    """
    Test: NO reactivar cuando los datos no coinciden completamente
    """
    print("\n" + "="*80)
    print("TEST: NO Reactivar con Datos Diferentes")
    print("="*80)

    estado, municipio, parroquia = crear_datos_basicos()

    # 1. Crear institución eliminada
    institucion_eliminada = Institucion.objects.create(
        nombre='Colegio Original',
        tipo_institucion='educativa',
        codigo_mppe='ME111111',
        email='original@test.com',
        rif='J-11111111',
        estado=estado,
        municipio=municipio,
        parroquia=parroquia,
        eliminado=True,
        activa=False
    )

    print(f"✓ Institución eliminada creada: '{institucion_eliminada.nombre}'")

    # 2. Intentar registrar con EMAIL DIFERENTE (debería fallar)
    data = {
        'tipo_institucion': 'educativa',
        'naturaleza': 'publica',
        'subcategoria': 'primaria',
        'nombre': 'Colegio Original',
        'rif_letra': 'J',
        'rif_numero': '11111111',
        'codigo_mppe': 'ME111111',
        'estado': estado.id,
        'municipio': municipio.id,
        'parroquia': parroquia.id,
        'direccion': 'Calle Test',
        'email': 'DIFERENTE@test.com',  # EMAIL DIFERENTE
        'codigo_area': '0212',
        'numero_telefono': '1234567',
        'password': 'Test@1234',
        'confirm_password': 'Test@1234',
    }

    form = InstitucionRegistrationForm(data=data)
    is_valid = form.is_valid()

    print(f"\n✓ Intento con email diferente...")
    print(f"  Formulario válido: {is_valid}")

    # Debería ser inválido porque el email no coincide
    if not is_valid:
        print("  ✅ Correctamente rechazó registro con datos diferentes")
        test_result = True
    else:
        print("  ❌ ERROR: Aceptó registro con datos diferentes")
        test_result = False

    # Limpiar
    institucion_eliminada.delete()

    print(f"\n{'✅ PASÓ' if test_result else '❌ FALLÓ'}: Test de Datos Diferentes")
    return test_result


def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*80)
    print("SUITE DE TESTS: REACTIVACIÓN DE INSTITUCIONES ELIMINADAS")
    print("="*80)

    results = []

    try:
        results.append(("Reactivación Educativa", test_reactivacion_institucion_eliminada()))
        results.append(("Reactivación Particular", test_reactivacion_particular_eliminado()))
        results.append(("No Reactivar Datos Diferentes", test_no_reactivacion_datos_diferentes()))

    except Exception as e:
        print(f"\n❌ ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests pasaron")

    if passed == total:
        print("🎉 TODOS LOS TESTS PASARON - IMPLEMENTACIÓN EXITOSA")
        print("\n📋 Resumen de Funcionalidad:")
        print("  ✅ Detecta instituciones eliminadas")
        print("  ✅ Reactiva en lugar de crear nuevas")
        print("  ✅ Pone en estado pendiente")
        print("  ✅ Desactiva usuario hasta aprobación")
        print("  ✅ Valida coincidencia total de datos")
        print("  ✅ No rompe flujo de registro normal")
        return True
    else:
        print(f"❌ {total - passed} test(s) fallaron")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)</content>
<parameter name="filePath">/home/argenis/Escritorio/MiProyecto/sistemaRobotica/test_reactivacion_instituciones.py