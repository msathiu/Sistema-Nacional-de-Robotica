import json
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from registry.models import (
    Estado,
    Evento,
    Grupo,
    Institucion,
    Municipio,
    Parroquia,
    Participante,
)


class UserViewErrorLeakTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Estado Error Leak", codigo="EL")
        cls.municipio = Municipio.objects.create(
            nombre="Municipio Error Leak", estado=cls.estado
        )
        cls.parroquia = Parroquia.objects.create(
            nombre="Parroquia Error Leak",
            municipio=cls.municipio,
        )

        cls.institucion = Institucion.objects.create(
            nombre="Institucion Segura",
            email="institucion@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Av. Principal",
        )

        cls.central_user = User.objects.create_user(
            username="central",
            password="testpass123",
        )
        cls.central_user.userprofile.user_type = "fed_central"
        cls.central_user.userprofile.save()

        cls.institucional_user = User.objects.create_user(
            username="institucional",
            password="testpass123",
        )
        cls.institucional_user.userprofile.user_type = "institucional"
        cls.institucional_user.userprofile.institution = cls.institucion
        cls.institucional_user.userprofile.estado = cls.estado
        cls.institucional_user.userprofile.save()

        cls.participante = Participante.objects.create(
            nombres="Ana",
            apellidos="Perez",
            fecha_nacimiento=date(2010, 1, 1),
            sexo="F",
            nacionalidad="V",
            cedula="12345678",
            email="ana@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            direccion="Calle 1",
            codigo_area="0412",
            numero_telefono="1234567",
            grado_escolar="NO",
        )

        cls.grupo = Grupo.objects.create(
            nombre="Equipo Seguro",
            criterio="proyecto",
            nombre_proyecto="Proyecto Uno",
            usuario_creador=cls.institucional_user,
            institucion=cls.institucion,
        )

        cls.evento = Evento.objects.create(
            nombre="Evento Seguro",
            tipo="Taller",
            fecha=date.today() + timedelta(days=30),
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            direccion="Auditorio",
            tipo_evento="institucional",
            institucion=cls.institucion,
            estado_evento="borrador",
            creado_por=cls.institucional_user,
        )

    def test_verificar_participante_duplicado_no_filtra_excepcion_real(self):
        self.client.force_login(self.institucional_user)

        with patch(
            "users.views.Participante.objects.filter",
            side_effect=Exception("database exploded"),
        ):
            response = self.client.post(
                reverse("verificar_participante_duplicado"),
                data=json.dumps({"cedula_personal": "12345678"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"],
            "Ocurrió un error interno al verificar el participante.",
        )

    def test_vincular_participante_existente_no_filtra_excepcion_real(self):
        self.client.force_login(self.institucional_user)

        with patch(
            "users.views.ParticipanteInstitucion.objects.filter",
            side_effect=Exception("constraint details"),
        ):
            response = self.client.post(
                reverse("vincular_participante_existente"),
                data=json.dumps({"participante_id": str(self.participante.id)}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(
            payload["error"],
            "Ocurrió un error interno al vincular el participante.",
        )

    def test_enviar_evento_revision_no_filtra_excepcion_real(self):
        self.client.force_login(self.institucional_user)

        with patch(
            "users.views._get_evento_institucional",
            side_effect=Exception("internal transition error"),
        ):
            response = self.client.post(f"/eventos/enviar-revision/{self.evento.id}/")

        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(
            payload["error"],
            "Ocurrió un error interno al enviar el evento a revisión.",
        )

    def test_api_participantes_grupo_no_filtra_excepcion_real(self):
        self.client.force_login(self.central_user)

        with patch(
            "users.views.get_object_or_404",
            side_effect=Exception("raw group error"),
        ):
            response = self.client.get(
                reverse("api_participantes_grupo", args=[self.grupo.id]),
            )

        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(
            payload["error"],
            "Ocurrió un error interno al consultar los participantes del grupo.",
        )

    def test_detalle_institucion_api_no_filtra_excepcion_real(self):
        self.client.force_login(self.central_user)

        with patch(
            "users.views.Institucion.objects.select_related",
            side_effect=Exception("stack trace here"),
        ):
            response = self.client.get(
                reverse("detalle_institucion_api", args=[self.institucion.id]),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"],
            "Ocurrió un error interno al obtener el detalle de la institución.",
        )

    def test_aprobar_institucion_no_filtra_permission_denied(self):
        self.client.force_login(self.central_user)
        self.institucion.estatus = "pendiente"
        self.institucion.save(update_fields=["estatus"])

        with patch(
            "users.views.InstitutionService.aprobar_primera_vez",
            side_effect=PermissionDenied("raw permission text"),
        ):
            response = self.client.post(
                reverse("aprobar_institucion", args=[self.institucion.id]),
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["message"],
            "No tienes permisos para aprobar esta institución.",
        )

    def test_desactivar_institucion_no_filtra_excepcion_real(self):
        self.client.force_login(self.central_user)

        with patch(
            "users.views.InstitutionService.toggle_status",
            side_effect=Exception("database details"),
        ):
            response = self.client.post(
                reverse("desactivar_institucion", args=[self.institucion.id]),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["message"], "Ocurrió un error interno.")
