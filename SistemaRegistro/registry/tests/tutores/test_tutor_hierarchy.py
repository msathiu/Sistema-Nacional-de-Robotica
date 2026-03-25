"""
Tests para la jerarquía de Tutores (Central, Regional e Institucional).
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from registry.models import (
    Estado,
    Institucion,
    Municipio,
    Parroquia,
    Tutor,
    TutorInstitucion,
)
from registry.services import TutorService


class TutorHierarchyTestCase(TestCase):
    def setUp(self):
        # Configuración de ubicación
        self.estado_zulia, _ = Estado.objects.get_or_create(nombre="Zulia", codigo="ZU")
        self.estado_miranda, _ = Estado.objects.get_or_create(nombre="Miranda", codigo="MI")
        
        self.municipio = Municipio.objects.create(estado=self.estado_zulia, nombre="Maracaibo")
        self.parroquia = Parroquia.objects.create(municipio=self.municipio, nombre="Olego")

        # Institución
        self.institucion = Institucion.objects.create(
            nombre="Escuela Zulia",
            codigo="INST-ZU-001",
            email="escuela@zulia.com",
            estado=self.estado_zulia,
            municipio=self.municipio,
            parroquia=self.parroquia,
            estatus="aprobado",
        )

        # Tutor Base
        self.tutor = Tutor.objects.create(
            nombres="Pedro",
            apellidos="Perez",
            cedula="88888888",
            email="pedro@example.com"
        )

    def test_vinculacion_central_exitosa(self):
        """Verifica que un tutor pueda ser vinculado a la Sede Central."""
        vinc, created = TutorService.vincular_tutor(
            tutor=self.tutor,
            tipo_vinculacion='central'
        )
        self.assertTrue(created)
        self.assertEqual(vinc.tipo_vinculacion, 'central')
        self.assertIsNone(vinc.institucion)
        self.assertIsNone(vinc.estado)

    def test_vinculacion_regional_exitosa(self):
        """Verifica que un tutor pueda ser vinculado a una Sede Regional."""
        vinc, created = TutorService.vincular_tutor(
            tutor=self.tutor,
            tipo_vinculacion='regional',
            estado=self.estado_zulia
        )
        self.assertTrue(created)
        self.assertEqual(vinc.tipo_vinculacion, 'regional')
        self.assertEqual(vinc.estado, self.estado_zulia)

    def test_multiples_vinculaciones_diferentes_entes(self):
        """Un tutor puede pertenecer a Central, Regional e Institucional simultáneamente."""
        # Central
        TutorService.vincular_tutor(self.tutor, tipo_vinculacion='central')
        # Regional Zulia
        TutorService.vincular_tutor(self.tutor, tipo_vinculacion='regional', estado=self.estado_zulia)
        # Institucional
        TutorService.vincular_tutor(self.tutor, tipo_vinculacion='institucional', institucion=self.institucion)

        self.assertEqual(TutorInstitucion.objects.filter(tutor=self.tutor).count(), 3)

    def test_constraint_central_unica(self):
        """No permite dos vinculaciones 'central' para el mismo tutor."""
        TutorInstitucion.objects.create(tutor=self.tutor, tipo_vinculacion='central')
        
        with self.assertRaises(IntegrityError):
            TutorInstitucion.objects.create(tutor=self.tutor, tipo_vinculacion='central')

    def test_constraint_regional_por_estado(self):
        """Permite vinculaciones regionales en diferentes estados, pero no repetidas en el mismo."""
        # Regional Zulia
        TutorInstitucion.objects.create(tutor=self.tutor, tipo_vinculacion='regional', estado=self.estado_zulia)
        
        # Permitir Miranda
        TutorInstitucion.objects.create(tutor=self.tutor, tipo_vinculacion='regional', estado=self.estado_miranda)
        
        # Fallar duplicado Zulia
        with self.assertRaises(IntegrityError):
            TutorInstitucion.objects.create(tutor=self.tutor, tipo_vinculacion='regional', estado=self.estado_zulia)

    def test_service_vincular_tutor_reactiva_inactivo(self):
        """Si la vinculación existe pero está inactiva, el servicio la reactiva."""
        vinc = TutorInstitucion.objects.create(
            tutor=self.tutor, 
            tipo_vinculacion='central',
            status='inactivo'
        )
        
        vinc_updated, created = TutorService.vincular_tutor(self.tutor, tipo_vinculacion='central')
        
        self.assertFalse(created)
        self.assertEqual(vinc_updated.id, vinc.id)
        self.assertEqual(vinc_updated.status, 'activo')

    def test_vincular_regional_sin_estado_falla(self):
        """Debe lanzar ValidationError si falta el estado en vinculación regional."""
        with self.assertRaises(ValidationError):
            TutorService.vincular_tutor(self.tutor, tipo_vinculacion='regional', estado=None)

    def test_vincular_institucional_sin_institucion_falla(self):
        """Debe lanzar ValidationError si falta la institución en vinculación institucional."""
        with self.assertRaises(ValidationError):
            TutorService.vincular_tutor(self.tutor, tipo_vinculacion='institucional', institucion=None)
