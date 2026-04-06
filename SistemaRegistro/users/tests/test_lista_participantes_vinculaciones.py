"""
Tests para validar la vista lista_participantes con múltiples vinculaciones.
"""

from datetime import date

from django.contrib.auth.models import User
from django.test import Client, TestCase
from registry.models import (
    Estado,
    Institucion,
    Municipio,
    Participante,
    ParticipanteInstitucion,
)

from users.models import UserProfile


class ListaParticipantesVinculacionesTest(TestCase):
    """Test para validar que lista_participantes muestra correctamente las vinculaciones."""

    @classmethod
    def setUpTestData(cls):
        # Usar un estado existente o crear uno único
        cls.estado, _ = Estado.objects.get_or_create(
            nombre="Distrito Capital", defaults={"codigo": "DC"}
        )

        # Crear un municipio
        try:
            cls.municipio = Municipio.objects.get(nombre="Caracas")
        except Municipio.DoesNotExist:
            cls.municipio = Municipio.objects.create(
                nombre="Caracas", estado=cls.estado, codigo="01"
            )

        # Crear dos instituciones
        cls.institucion1 = Institucion.objects.create(
            nombre="Instituto 1",
            codigo="INST1",
            tipo_institucion="publica",
            estado=cls.estado,
            municipio=cls.municipio,
        )
        cls.institucion2 = Institucion.objects.create(
            nombre="Instituto 2",
            codigo="INST2",
            tipo_institucion="publica",
            estado=cls.estado,
            municipio=cls.municipio,
        )

        # Crear un participante
        cls.participante = Participante.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            cedula="12345678",
            sexo="M",
            fecha_nacimiento=date(2008, 1, 1),
            estado=cls.estado,
        )

        # Crear dos vinculaciones del mismo participante
        cls.vinculacion1 = ParticipanteInstitucion.objects.create(
            participante=cls.participante,
            institucion=cls.institucion1,
            tipo_vinculacion="institucional",
            status="activo",
        )
        cls.vinculacion2 = ParticipanteInstitucion.objects.create(
            participante=cls.participante,
            institucion=cls.institucion2,
            tipo_vinculacion="institucional",
            status="activo",
        )

    def setUp(self):
        self.client = Client()

    def test_fed_central_ve_todas_vinculaciones(self):
        """Test: fed_central debe ver todas las vinculaciones del participante."""
        # Crear usuario fed_central
        user = User.objects.create_user(username="fed_user", password="testpass")
        profile = UserProfile.objects.create(user=user, user_type="fed_central")

        self.client.login(username="fed_user", password="testpass")
        response = self.client.get("/participantes/")

        # Verificar que la respuesta es 200
        self.assertEqual(response.status_code, 200)

        # Verificar que el participante aparece
        self.assertContains(response, "Juan Pérez")

        # Verificar que tiene acceso a todas_vinculaciones
        participantes = response.context.get("participantes")
        self.assertIsNotNone(participantes)

        # El participante debe estar en la lista
        p = next((p for p in participantes if p.cedula == "12345678"), None)
        self.assertIsNotNone(p)

        # Debe tener 2 vinculaciones
        self.assertEqual(len(p.todas_vinculaciones), 2)
        print(f"✅ fed_central ve {len(p.todas_vinculaciones)} vinculaciones")

    def test_institucional_ve_solo_su_vinculacion(self):
        """Test: usuario institucional debe ver solo su vinculación."""
        # Crear usuario institucional vinculado a institucion1
        user = User.objects.create_user(username="inst_user", password="testpass")
        profile = UserProfile.objects.create(
            user=user,
            user_type="institucional",
            institution=self.institucion1,
        )

        self.client.login(username="inst_user", password="testpass")
        response = self.client.get("/participantes/")

        # Verificar que la respuesta es 200
        self.assertEqual(response.status_code, 200)

        # El participante debe estar en la lista (porque tiene vinculación con su institución)
        self.assertContains(response, "Juan Pérez")

        # Obtener participante
        participantes = response.context.get("participantes")
        p = next((p for p in participantes if p.cedula == "12345678"), None)
        self.assertIsNotNone(p)

        # Debe tener SOLO 1 vinculación (la suya)
        self.assertEqual(len(p.todas_vinculaciones), 1)
        self.assertEqual(p.todas_vinculaciones[0].institucion_id, self.institucion1.id)

        # El campo institucion debe ser su institución
        self.assertEqual(p.institucion.id, self.institucion1.id)
        print("✅ institucional ve solo 1 vinculación (la suya)")
