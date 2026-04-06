"""
Tests para el modelo Tutor y TutorService alineados al modelo vigente.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from registry.forms import TutorForm
from registry.models import (
    Estado,
    Evento,
    Grupo,
    Institucion,
    Municipio,
    Parroquia,
    Tutor,
    TutorInstitucion,
)
from registry.services import TutorService


class TutorBaseTestCase(TestCase):
    def setUp(self):
        self.estado, _ = Estado.objects.get_or_create(
            nombre="Test Estado",
            defaults={"codigo": "TE"},
        )
        self.municipio, _ = Municipio.objects.get_or_create(
            estado=self.estado,
            nombre="Test Municipio",
        )
        self.parroquia, _ = Parroquia.objects.get_or_create(
            municipio=self.municipio,
            nombre="Test Parroquia",
        )

        self.institucion = Institucion.objects.create(
            nombre="Institución Test",
            codigo="INST-TUTOR-001",
            email="inst.tutor@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            estatus="aprobado",
        )

        self.usuario = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def crear_tutor(self, **overrides):
        datos = {
            "nacionalidad": "V",
            "nombres": "Juan",
            "apellidos": "Perez",
            "sexo": "M",
            "cedula": "12345678",
            "telefono_codigo": "0412",
            "telefono": "1234567",
            "email": "juan@example.com",
            "profesion": "Ingeniero",
            "experiencia": "5 anos de experiencia",
        }
        datos.update(overrides)
        return Tutor.objects.create(**datos)

    def crear_grupo(self, **overrides):
        datos = {
            "nombre": "Grupo Test",
            "criterio": "proyecto",
            "nombre_proyecto": "Robotica Escolar",
            "usuario_creador": self.usuario,
            "institucion": self.institucion,
        }
        datos.update(overrides)
        return Grupo.objects.create(**datos)


class TutorModelTest(TutorBaseTestCase):
    def test_crear_tutor_datos_validos(self):
        tutor = self.crear_tutor()

        self.assertEqual(tutor.get_nombre_completo(), "Juan Perez")
        self.assertEqual(str(tutor), "Juan Perez (12345678)")
        self.assertEqual(tutor.telefono, "1234567")

    def test_creacion_directa_permite_cedulas_repetidas(self):
        self.crear_tutor()
        self.crear_tutor(email="otro@example.com")

        self.assertEqual(Tutor.objects.filter(cedula="12345678").count(), 2)

    def test_uuid_autogenerado(self):
        tutor = self.crear_tutor()

        self.assertIsNotNone(tutor.id)
        self.assertEqual(type(tutor.id).__name__, "UUID")


class TutorFormValidationTest(TutorBaseTestCase):
    def get_valid_form_data(self):
        return {
            "tipo_vinculacion": "institucional",
            "institucion": self.institucion.id,
            "estado": "",
            "rol": "colaborador",
            "nacionalidad": "V",
            "nombres": "Juan",
            "apellidos": "Perez",
            "sexo": "M",
            "cedula": "12345678",
            "telefono_codigo": "0412",
            "telefono": "1234567",
            "email": "juan.form@example.com",
            "profesion": "Ingeniero",
            "experiencia": "Experiencia relevante",
        }

    def test_form_rechaza_telefono_con_letras(self):
        data = self.get_valid_form_data()
        data["telefono"] = "12AB567"

        form = TutorForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("telefono", form.errors)
        self.assertIn("solo dígitos", form.errors["telefono"][0])

    def test_form_acepta_telefono_numerico_de_siete_digitos(self):
        form = TutorForm(data=self.get_valid_form_data())

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data["telefono"], "1234567")


class TutorCreateViewTemplateTest(TutorBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.usuario.userprofile.user_type = "institucional"
        self.usuario.userprofile.institution = self.institucion
        self.usuario.userprofile.estado = self.estado
        self.usuario.userprofile.save()

    def test_crear_tutor_renderiza_input_telefono_reforzado(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("crear_tutor"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="id_telefono"', content)
        self.assertIn('inputmode="numeric"', content)
        self.assertIn('pattern="[0-9]{7}"', content)


class TutorServiceTest(TutorBaseTestCase):
    def test_registrar_tutor_valido_crea_vinculacion_activa(self):
        datos = {
            "nombres": "Juan",
            "apellidos": "Perez",
            "cedula": "V12345678",
            "telefono_codigo": "0412",
            "telefono": "1234567",
            "email": "juan@example.com",
            "profesion": "Ingeniero",
            "experiencia": "5 anos",
        }

        tutor = TutorService.registrar_tutor(
            institucion=self.institucion,
            datos_tutor=datos,
            usuario_solicitante=self.usuario,
        )

        self.assertIsNotNone(tutor.id)
        self.assertEqual(tutor.cedula, "12345678")
        self.assertTrue(
            TutorInstitucion.objects.filter(
                tutor=tutor,
                institucion=self.institucion,
                status="activo",
            ).exists()
        )

    def test_registrar_tutor_existente_reutiliza_tutor(self):
        tutor_existente = self.crear_tutor()

        datos = {
            "nombres": "Juan",
            "apellidos": "Perez",
            "cedula": "12345678",
            "telefono_codigo": "0412",
            "telefono": "1234567",
            "email": "juan@example.com",
        }

        tutor = TutorService.registrar_tutor(
            institucion=self.institucion,
            datos_tutor=datos,
            usuario_solicitante=self.usuario,
        )

        self.assertEqual(tutor.id, tutor_existente.id)
        self.assertEqual(Tutor.objects.count(), 1)
        self.assertEqual(TutorInstitucion.objects.count(), 1)

    def test_registrar_tutor_campos_obligatorios_incompletos_falla(self):
        datos = {
            "nombres": "Juan",
            "cedula": "12345678",
            "email": "juan@example.com",
        }

        with self.assertRaises(KeyError):
            TutorService.registrar_tutor(
                institucion=self.institucion,
                datos_tutor=datos,
            )

    def test_asignar_tutor_a_grupo(self):
        tutor = self.crear_tutor()
        TutorService.vincular_tutor_institucion(tutor, self.institucion, usuario=self.usuario)
        grupo = self.crear_grupo()

        TutorService.asignar_tutor_a_grupo(tutor, grupo, self.usuario)

        self.assertEqual(grupo.tutores.count(), 1)
        self.assertIn(tutor, grupo.tutores.all())

    def test_asignar_tutor_sin_vinculacion_activa_error(self):
        tutor = self.crear_tutor()
        grupo = self.crear_grupo()

        with self.assertRaises(ValidationError):
            TutorService.asignar_tutor_a_grupo(tutor, grupo, self.usuario)

    def test_validar_grupo_listo_para_evento(self):
        tutor = self.crear_tutor()
        TutorService.vincular_tutor_institucion(tutor, self.institucion, usuario=self.usuario)

        grupo_sin_tutor = self.crear_grupo(nombre="Grupo Sin Tutor")
        grupo_con_tutor = self.crear_grupo(nombre="Grupo Con Tutor")
        grupo_con_tutor.tutores.add(tutor)

        self.assertFalse(TutorService.validar_grupo_listo_para_evento(grupo_sin_tutor))
        self.assertTrue(TutorService.validar_grupo_listo_para_evento(grupo_con_tutor))

    def test_cambiar_estado_tutor(self):
        tutor = self.crear_tutor()
        TutorService.vincular_tutor_institucion(tutor, self.institucion, usuario=self.usuario)

        vinculacion = TutorService.cambiar_estado_tutor(
            tutor,
            self.institucion,
            "inactivo",
            self.usuario,
        )
        self.assertEqual(vinculacion.status, "inactivo")

        vinculacion = TutorService.cambiar_estado_tutor(
            tutor,
            self.institucion,
            "activo",
            self.usuario,
        )
        self.assertEqual(vinculacion.status, "activo")

    def test_cambiar_estado_invalido(self):
        tutor = self.crear_tutor()
        TutorService.vincular_tutor_institucion(tutor, self.institucion, usuario=self.usuario)

        with self.assertRaises(ValidationError):
            TutorService.cambiar_estado_tutor(
                tutor,
                self.institucion,
                "estado_invalido",
                self.usuario,
            )

    def test_remover_ultimo_tutor_grupo_con_evento(self):
        tutor = self.crear_tutor()
        TutorService.vincular_tutor_institucion(tutor, self.institucion, usuario=self.usuario)

        evento = Evento.objects.create(
            nombre="Evento Test",
            tipo="Competencia",
            fecha="2026-03-01",
            tipo_evento="institucional",
            institucion=self.institucion,
        )

        grupo = self.crear_grupo(evento=evento)
        grupo.tutores.add(tutor)

        with self.assertRaises(ValidationError) as context:
            TutorService.remover_tutor_de_grupo(tutor, grupo, self.usuario)

        self.assertIn("vinculado a un evento", str(context.exception))
