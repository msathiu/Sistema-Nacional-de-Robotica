#!/usr/bin/env python
"""
Script para ejecutar los tests de registro de instituciones de forma controlada
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SistemaRegistro.settings')
django.setup()

from django.test.utils import get_runner
from django.conf import settings

def run_tests():
    """Ejecutar los tests"""
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)
    
    # Tests a ejecutar
    test_labels = [
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_registro_institucion_educativa_exitoso',
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_registro_particular_exitoso',
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_email_duplicado_rechazado',
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_password_sin_mayuscula_rechazado',
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_password_sin_numero_rechazado',
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_password_sin_especial_rechazado',
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_municipio_no_pertenece_estado_rechazado',
        'users.tests.test_institucion_registration.InstitucionRegistrationFormTests.test_parroquia_no_pertenece_municipio_rechazado',
    ]
    
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║  EJECUTANDO TESTS CRÍTICOS - REGISTRO DE INSTITUCIONES      ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        print(f"\n❌ {failures} tests fallaron")
        sys.exit(1)
    else:
        print("\n✓ Todos los tests pasaron exitosamente")
        sys.exit(0)

if __name__ == '__main__':
    run_tests()
