from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registry.models import Estado, EstadoEvento, Evento, Institucion, Municipio, Parroquia


class DetalleEventoInstitucionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Estado Evento Detalle", codigo="EVD")
        cls.municipio = Municipio.objects.create(nombre="Municipio Evento Detalle", estado=cls.estado)
        cls.parroquia = Parroquia.objects.create(nombre="Parroquia Evento Detalle", municipio=cls.municipio)

        cls.institucion = Institucion.objects.create(
            nombre="Unidad Educativa Petare",
            email="ue.petare@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Calle Principal",
        )

        cls.user_fed = User.objects.create_user(
            username="fedcentral_eventos",
            password="testpass123",
        )
        perfil_fed = cls.user_fed.userprofile
        perfil_fed.user_type = "fed_central"
        perfil_fed.estado = cls.estado
        perfil_fed.save()

        cls.user_inst = User.objects.create_user(
            username="institucional_eventos",
            password="testpass123",
        )
        perfil_inst = cls.user_inst.userprofile
        perfil_inst.user_type = "institucional"
        perfil_inst.institution = cls.institucion
        perfil_inst.estado = cls.estado
        perfil_inst.save()

        cls.evento_federacion = Evento.objects.create(
            nombre="Copa Nacional de Robótica",
            tipo="Competencia",
            tipo_evento="institucional",
            es_publico=True,
            audiencia="publica",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=15),
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            creado_por=cls.user_fed,
            institucion=None,
        )

        cls.evento_institucional = Evento.objects.create(
            nombre="Feria Escolar de Robótica",
            tipo="Feria",
            tipo_evento="institucional",
            audiencia="institucional_privado",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=10),
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            creado_por=cls.user_inst,
            institucion=cls.institucion,
        )

    def test_detalle_evento_federacion_muestra_nombre_federacion(self):
        self.client.force_login(self.user_inst)

        response = self.client.get(
            reverse("detalle_evento_gestion", args=[self.evento_federacion.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Federación Venezolana de Robótica Creativa",
        )

    def test_detalle_evento_institucional_conserva_nombre_institucion(self):
        self.client.force_login(self.user_inst)

        response = self.client.get(
            reverse("detalle_evento_gestion", args=[self.evento_institucional.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.institucion.nombre)
