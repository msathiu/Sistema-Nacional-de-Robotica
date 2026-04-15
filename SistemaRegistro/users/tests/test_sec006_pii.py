import json
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from registry.models import (
    Estado,
    Institucion,
    Municipio,
    Parroquia,
    Participante,
    ParticipanteInstitucion,
    Tutor,
    TutorInstitucion,
)


class PiiEnumerationMitigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Estado PII", codigo="PI")
        cls.municipio = Municipio.objects.create(
            nombre="Municipio PII", estado=cls.estado
        )
        cls.parroquia = Parroquia.objects.create(
            nombre="Parroquia PII", municipio=cls.municipio
        )

        cls.institucion_a = Institucion.objects.create(
            nombre="Institucion A",
            email="insta@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Direccion A",
        )
        cls.institucion_b = Institucion.objects.create(
            nombre="Institucion B",
            email="instb@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Direccion B",
        )

        cls.institucional = User.objects.create_user(
            username="institucional_pii",
            password="testpass123",
        )
        cls.institucional.userprofile.user_type = "institucional"
        cls.institucional.userprofile.institution = cls.institucion_a
        cls.institucional.userprofile.estado = cls.estado
        cls.institucional.userprofile.save()

        cls.fed_central = User.objects.create_user(
            username="central_pii",
            password="testpass123",
        )
        cls.fed_central.userprofile.user_type = "fed_central"
        cls.fed_central.userprofile.save()

        cls.participante = Participante.objects.create(
            nombres="Ana",
            apellidos="Lopez",
            fecha_nacimiento=date(2010, 1, 1),
            sexo="F",
            nacionalidad="V",
            cedula="12345678",
            cedula_escolar="87654321",
            email="ana@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            direccion="Av. Principal",
            codigo_area="0412",
            numero_telefono="1234567",
            grado_escolar="NO",
        )
        ParticipanteInstitucion.objects.create(
            participante=cls.participante,
            institucion=cls.institucion_a,
            tipo_vinculacion="institucional",
            status="activo",
            registrado_por=cls.institucional,
        )
        ParticipanteInstitucion.objects.create(
            participante=cls.participante,
            institucion=cls.institucion_b,
            tipo_vinculacion="institucional",
            status="activo",
            registrado_por=cls.fed_central,
        )

        cls.tutor = Tutor.objects.create(
            nacionalidad="V",
            nombres="Carlos",
            apellidos="Tutor",
            sexo="M",
            cedula="22334455",
            telefono_codigo="0412",
            telefono="7654321",
            email="carlos.tutor@example.com",
        )
        TutorInstitucion.objects.create(
            tutor=cls.tutor,
            institucion=cls.institucion_b,
            tipo_vinculacion="institucional",
            rol="colaborador",
            status="activo",
        )

    def test_api_buscar_participante_requires_login(self):
        response = self.client.get(
            reverse("api_buscar_participante", args=["12345678"])
        )
        self.assertEqual(response.status_code, 302)

    def test_api_buscar_participante_returns_minimal_data_for_visible_participant(self):
        self.client.force_login(self.institucional)
        response = self.client.get(
            reverse("api_buscar_participante", args=["12345678"])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["encontrado"])
        self.assertEqual(payload["tipo"], "participante")
        self.assertEqual(payload["nombre"], "Ana")
        self.assertNotIn("email", payload)
        self.assertNotIn("telefono", payload)
        self.assertNotIn("institucion", payload)

    def test_api_buscar_participante_does_not_reveal_tutor_outside_scope(self):
        self.client.force_login(self.institucional)
        response = self.client.get(
            reverse("api_buscar_participante", args=["22334455"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"encontrado": False})

    def test_verificar_participante_duplicado_masks_identifiers_for_institucional(self):
        self.client.force_login(self.institucional)
        response = self.client.post(
            reverse("verificar_participante_duplicado"),
            data=json.dumps({"cedula_personal": "12345678"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["existe"])
        self.assertEqual(payload["datos"]["cedula"], "V-****5678")
        self.assertEqual(payload["datos"]["cedula_escolar"], "E-****4321")
        self.assertEqual(payload["total_instituciones"], 2)
        self.assertEqual(payload["instituciones_vinculadas"], [])
