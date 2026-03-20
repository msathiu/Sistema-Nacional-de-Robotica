from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from registry.models import Estado, EstadoEvento, Evento, Institucion, Municipio, Parroquia


User = get_user_model()


class EventoWorkflowTestCase(TestCase):
    """Pruebas del flujo vigente de estados de Evento."""

    def setUp(self):
        self.client = Client()
        self.estado, _ = Estado.objects.get_or_create(
            nombre="Lara",
            defaults={"codigo": "13"},
        )
        self.municipio, _ = Municipio.objects.get_or_create(
            nombre="Iribarren",
            estado=self.estado,
        )
        self.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Concepción",
            municipio=self.municipio,
        )

        self.institucion = Institucion.objects.create(
            nombre="Institución Workflow",
            codigo="INST-WF-001",
            email="workflow@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )

        self.user_institucional = User.objects.create_user(
            username="inst_workflow",
            password="test123",
        )
        perfil_inst = self.user_institucional.userprofile
        perfil_inst.user_type = "institucional"
        perfil_inst.institution = self.institucion
        perfil_inst.save()

        self.user_fed = User.objects.create_user(
            username="fed_workflow",
            password="test123",
            is_staff=True,
        )
        perfil_fed = self.user_fed.userprofile
        perfil_fed.user_type = "fed_central"
        perfil_fed.save()

    def _crear_evento_borrador(self):
        return Evento.objects.create(
            nombre="Evento Workflow",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            estado_evento=EstadoEvento.BORRADOR,
            fecha=timezone.now().date() + timedelta(days=10),
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            creado_por=self.user_institucional,
        )

    def test_flujo_borrador_revision_abierto(self):
        evento = self._crear_evento_borrador()

        self.assertTrue(evento.solicitar_revision())
        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.REVISION)

        self.assertTrue(evento.aprobar(self.user_fed, "Validado por ente rector"))
        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.ABIERTO)
        self.assertEqual(evento.aprobado_por, self.user_fed)
        self.assertTrue(evento.es_publico)
        self.assertEqual(evento.audiencia, "publica")

    def test_flujo_abierto_pausado_reabierto_desde_vista(self):
        evento = self._crear_evento_borrador()
        evento.estado_evento = EstadoEvento.ABIERTO
        evento.es_publico = True
        evento.save(update_fields=["estado_evento", "es_publico"])

        self.client.login(username="fed_workflow", password="test123")
        nueva_fecha = (timezone.now().date() + timedelta(days=20)).isoformat()

        pausa = self.client.post(
            reverse("gestionar_estado_evento", args=[evento.id]),
            {
                "estado_evento": EstadoEvento.PAUSADO,
                "observacion": "Reprogramado por causa mayor",
                "nueva_fecha": nueva_fecha,
            },
        )
        self.assertEqual(pausa.status_code, 302)

        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.PAUSADO)
        self.assertEqual(evento.observacion_estado, "Reprogramado por causa mayor")
        self.assertEqual(evento.fecha.isoformat(), nueva_fecha)

        reapertura = self.client.post(
            reverse("gestionar_estado_evento", args=[evento.id]),
            {
                "estado_evento": EstadoEvento.ABIERTO,
                "observacion": "Fecha confirmada nuevamente",
                "nueva_fecha": nueva_fecha,
            },
        )
        self.assertEqual(reapertura.status_code, 302)

        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.ABIERTO)
        self.assertEqual(evento.observacion_estado, "Fecha confirmada nuevamente")

    def test_flujo_abierto_cancelado_por_institucion_propietaria(self):
        evento = self._crear_evento_borrador()
        evento.estado_evento = EstadoEvento.ABIERTO
        evento.save(update_fields=["estado_evento"])

        self.assertTrue(evento.puede_cancelar(self.user_institucional))
        self.assertTrue(evento.cancelar("Cancelado por la institución organizadora"))

        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.CANCELADO)
        self.assertTrue(evento.cancelado)
        self.assertFalse(evento.activo)
        self.assertEqual(evento.motivo_cancelacion, "Cancelado por la institución organizadora")

    def test_flujo_pausado_cancelado_por_federacion(self):
        evento = self._crear_evento_borrador()
        evento.estado_evento = EstadoEvento.ABIERTO
        evento.save(update_fields=["estado_evento"])
        evento.pausar("Pausa preventiva")

        self.assertTrue(evento.puede_cancelar(self.user_fed))
        self.assertTrue(evento.cancelar("Cancelado definitivamente por ente rector"))

        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.CANCELADO)
        self.assertEqual(evento.motivo_cancelacion, "Cancelado definitivamente por ente rector")

    def test_institucion_no_puede_pausar_evento(self):
        evento = self._crear_evento_borrador()
        evento.estado_evento = EstadoEvento.ABIERTO
        evento.save(update_fields=["estado_evento"])

        self.assertFalse(evento.puede_pausar(self.user_institucional))
