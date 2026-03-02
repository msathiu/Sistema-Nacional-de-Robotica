"""
Tests para el modelo Tutor y TutorService.

Cobertura:
- Creación de tutor con datos válidos
- Validación de cédula única
- Asignación de tutor a grupo
- Validación de grupo listo para evento
- Cambio de estado de tutor
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import Tutor, Grupo, Institucion, Estado, Municipio, Parroquia
from .services import TutorService


class TutorModelTest(TestCase):
    """Tests para el modelo Tutor."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        # Crear ubicación
        self.estado = Estado.objects.create(nombre='Test Estado', codigo='TE')
        self.municipio = Municipio.objects.create(
            estado=self.estado, nombre='Test Municipio'
        )
        self.parroquia = Parroquia.objects.create(
            municipio=self.municipio, nombre='Test Parroquia'
        )
        
        # Crear institución
        self.institucion = Institucion.objects.create(
            nombre='Institución Test',
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            estatus='aprobado'
        )
        
        # Crear usuario
        self.usuario = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_crear_tutor_datos_validos(self):
        """Test: Crear tutor con datos válidos."""
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            profesion='Ingeniero',
            experiencia='5 años de experiencia',
            status='activo'
        )
        
        self.assertEqual(str(tutor), 'Juan Pérez - V12345678')
        self.assertEqual(tutor.get_nombre_completo(), 'Juan Pérez')
        self.assertEqual(tutor.status, 'activo')
    
    def test_cedula_unica(self):
        """Test: No permitir cédula duplicada."""
        Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        # Intentar crear otro tutor con la misma cédula
        with self.assertRaises(Exception):  # IntegrityError
            Tutor.objects.create(
                institucion=self.institucion,
                nombres='María',
                apellidos='García',
                cedula='V12345678',  # Cédula duplicada
                telefono='0424-7654321',
                email='maria@example.com',
                status='activo'
            )
    
    def test_uuid_autogenerado(self):
        """Test: El ID se genera automáticamente como UUID."""
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        self.assertIsNotNone(tutor.id)
        self.assertEqual(type(tutor.id).__name__, 'UUID')


class TutorServiceTest(TestCase):
    """Tests para TutorService."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        # Crear ubicación
        self.estado = Estado.objects.create(nombre='Test Estado', codigo='TE')
        self.municipio = Municipio.objects.create(
            estado=self.estado, nombre='Test Municipio'
        )
        self.parroquia = Parroquia.objects.create(
            municipio=self.municipio, nombre='Test Parroquia'
        )
        
        # Crear institución
        self.institucion = Institucion.objects.create(
            nombre='Institución Test',
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            estatus='aprobado'
        )
        
        # Crear usuario
        self.usuario = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_registrar_tutor_valido(self):
        """Test: Registrar tutor con datos válidos."""
        datos = {
            'nombres': 'Juan',
            'apellidos': 'Pérez',
            'cedula': 'V12345678',
            'telefono': '0414-1234567',
            'email': 'juan@example.com',
            'profesion': 'Ingeniero',
            'experiencia': '5 años',
            'status': 'activo'
        }
        
        tutor = TutorService.registrar_tutor(
            institucion=self.institucion,
            datos_tutor=datos,
            usuario_solicitante=self.usuario
        )
        
        self.assertIsNotNone(tutor.id)
        self.assertEqual(tutor.nombres, 'Juan')
        self.assertEqual(tutor.cedula, 'V12345678')
    
    def test_registrar_tutor_cedula_duplicada(self):
        """Test: Error al registrar tutor con cédula duplicada."""
        # Crear primer tutor
        Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        # Intentar crear segundo tutor con misma cédula
        datos = {
            'nombres': 'María',
            'apellidos': 'García',
            'cedula': 'V12345678',  # Duplicada
            'telefono': '0424-7654321',
            'email': 'maria@example.com',
            'status': 'activo'
        }
        
        with self.assertRaises(ValidationError) as context:
            TutorService.registrar_tutor(
                institucion=self.institucion,
                datos_tutor=datos
            )
        
        self.assertIn('V12345678', str(context.exception))
    
    def test_registrar_tutor_campos_obligatorios(self):
        """Test: Error si faltan campos obligatorios."""
        datos = {
            'nombres': 'Juan',
            # Falta apellidos
            'cedula': 'V12345678',
            'telefono': '0414-1234567',
            'email': 'juan@example.com',
        }
        
        with self.assertRaises(ValidationError) as context:
            TutorService.registrar_tutor(
                institucion=self.institucion,
                datos_tutor=datos
            )
        
        self.assertIn('apellidos', str(context.exception))
    
    def test_asignar_tutor_a_grupo(self):
        """Test: Asignar tutor a grupo."""
        # Crear tutor
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        # Crear grupo
        grupo = Grupo.objects.create(
            nombre='Grupo Test',
            usuario_creador=self.usuario
        )
        
        # Asignar tutor
        TutorService.asignar_tutor_a_grupo(tutor, grupo, self.usuario)
        
        # Verificar asignación
        self.assertEqual(grupo.tutores.count(), 1)
        self.assertIn(tutor, grupo.tutores.all())
    
    def test_asignar_tutor_inactivo_error(self):
        """Test: Error al asignar tutor inactivo."""
        # Crear tutor inactivo
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='inactivo'
        )
        
        # Crear grupo
        grupo = Grupo.objects.create(
            nombre='Grupo Test',
            usuario_creador=self.usuario
        )
        
        # Intentar asignar tutor inactivo
        with self.assertRaises(ValidationError):
            TutorService.asignar_tutor_a_grupo(tutor, grupo, self.usuario)
    
    def test_validar_grupo_listo_para_evento(self):
        """Test: Validar si grupo está listo para evento."""
        # Crear tutor
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        # Crear grupo sin tutor
        grupo_sin_tutor = Grupo.objects.create(
            nombre='Grupo Sin Tutor',
            usuario_creador=self.usuario
        )
        
        # Crear grupo con tutor
        grupo_con_tutor = Grupo.objects.create(
            nombre='Grupo Con Tutor',
            usuario_creador=self.usuario
        )
        grupo_con_tutor.tutores.add(tutor)
        
        # Validar
        self.assertFalse(
            TutorService.validar_grupo_listo_para_evento(grupo_sin_tutor)
        )
        self.assertTrue(
            TutorService.validar_grupo_listo_para_evento(grupo_con_tutor)
        )
    
    def test_cambiar_estado_tutor(self):
        """Test: Cambiar estado de tutor."""
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        # Cambiar a inactivo
        tutor = TutorService.cambiar_estado_tutor(tutor, 'inactivo', self.usuario)
        self.assertEqual(tutor.status, 'inactivo')
        
        # Cambiar a activo
        tutor = TutorService.cambiar_estado_tutor(tutor, 'activo', self.usuario)
        self.assertEqual(tutor.status, 'activo')
    
    def test_cambiar_estado_invalido(self):
        """Test: Error al cambiar a estado inválido."""
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        with self.assertRaises(ValidationError):
            TutorService.cambiar_estado_tutor(tutor, 'estado_invalido', self.usuario)
    
    def test_remover_ultimo_tutor_grupo_con_evento(self):
        """Test: Error al remover último tutor de grupo vinculado a evento."""
        from .models import Evento
        
        # Crear tutor
        tutor = Tutor.objects.create(
            institucion=self.institucion,
            nombres='Juan',
            apellidos='Pérez',
            cedula='V12345678',
            telefono='0414-1234567',
            email='juan@example.com',
            status='activo'
        )
        
        # Crear evento
        evento = Evento.objects.create(
            nombre='Evento Test',
            tipo='competencia',
            fecha='2026-03-01',
            tipo_evento='institucional',
            institucion=self.institucion
        )
        
        # Crear grupo con tutor y evento
        grupo = Grupo.objects.create(
            nombre='Grupo Test',
            usuario_creador=self.usuario,
            evento=evento
        )
        grupo.tutores.add(tutor)
        
        # Intentar remover el único tutor
        with self.assertRaises(ValidationError) as context:
            TutorService.remover_tutor_de_grupo(tutor, grupo, self.usuario)
        
        self.assertIn('vinculado a un evento', str(context.exception))


class GrupoTutorValidationTest(TestCase):
    """Tests para la validación de Grupo con tutores."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        # Crear ubicación
        self.estado = Estado.objects.create(nombre='Test Estado', codigo='TE')
        self.municipio = Municipio.objects.create(
            estado=self.estado, nombre='Test Municipio'
        )
        self.parroquia = Parroquia.objects.create(
            municipio=self.municipio, nombre='Test Parroquia'
        )
        
        # Crear institución
        self.institucion = Institucion.objects.create(
            nombre='Institución Test',
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            estatus='aprobado'
        )
        
        # Crear usuario
        self.usuario = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_grupo_clean_sin_tutor_con_evento(self):
        """Test: Validación clean() detecta grupo sin tutor vinculado a evento."""
        from .models import Evento
        
        # Crear evento
        evento = Evento.objects.create(
            nombre='Evento Test',
            tipo='competencia',
            fecha='2026-03-01',
            tipo_evento='institucional',
            institucion=self.institucion
        )
        
        # Crear grupo
        grupo = Grupo.objects.create(
            nombre='Grupo Test',
            usuario_creador=self.usuario
        )
        
        # Asignar evento (esto debería fallar en clean pero no en save directo)
        grupo.evento = evento
        
        # La validación clean() debería fallar
        with self.assertRaises(ValidationError):
            grupo.clean()
