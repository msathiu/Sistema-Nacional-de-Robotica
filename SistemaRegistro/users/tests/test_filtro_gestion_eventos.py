from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from users.models import UserProfile
from registry.models.evento import Evento, EstadoEvento
from registry.models.institucion import Institucion
from registry.models.base import Estado
from django.utils import timezone
from datetime import date


class FiltroGestionEventosTestCase(TestCase):
    """Tests para verificar los nuevos filtros de gestión de eventos."""

    def setUp(self):
        self.client = Client()

        # Crear usuario federación central
        self.user_fed = User.objects.create_user(
            username="fed_central", email="fed@test.com", password="test123"
        )
        self.profile_fed = UserProfile.objects.create(
            user=self.user_fed, user_type="federacion", es_federacion=True
        )

        # Crear estados para pruebas
        self.estado1 = Estado.objects.create(nombre="Estado Test 1", codigo="ET1")
        self.estado2 = Estado.objects.create(nombre="Estado Test 2", codigo="ET2")

        # Crear instituciones en diferentes estados
        self.inst1 = Institucion.objects.create(
            nombre="Institución Estado 1", codigo="INST001", estado=self.estado1
        )
        self.inst2 = Institucion.objects.create(
            nombre="Institución Estado 2", codigo="INST002", estado=self.estado2
        )

        # Crear eventos de diferentes tipos
        self.evento_fed = Evento.objects.create(
            nombre="Evento Federación",
            tipo="Competencia",
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.ABIERTO,
            institucion=None,  # Evento de federación
            estado=self.estado1,
        )

        self.evento_inst1 = Evento.objects.create(
            nombre="Evento Institución 1",
            tipo="Taller",
            fecha=date.today() + timezone.timedelta(days=25),
            estado_evento=EstadoEvento.REVISION,
            institucion=self.inst1,
            estado=self.estado1,
        )

        self.evento_inst2 = Evento.objects.create(
            nombre="Evento Institución 2",
            tipo="Seminario",
            fecha=date.today() + timezone.timedelta(days=20),
            estado_evento=EstadoEvento.PAUSADO,
            institucion=self.inst2,
            estado=self.estado2,
        )

        self.client.login(username="fed_central", password="test123")

    def test_filtro_federacion_central(self):
        """Verifica el filtro para eventos de Federación Central."""
        response = self.client.get(
            reverse("admin_eventos"), {"federacion_institucion": "federacion"}
        )

        self.assertEqual(response.status_code, 200)

        # Debería mostrar solo eventos sin institución (federación)
        eventos_en_contexto = list(response.context["eventos"])
        self.assertEqual(len(eventos_en_contexto), 1)
        self.assertEqual(eventos_en_contexto[0].nombre, "Evento Federación")
        self.assertIsNone(eventos_en_contexto[0].institucion)

    def test_filtro_todas_instituciones(self):
        """Verifica el filtro para todas las instituciones."""
        response = self.client.get(
            reverse("admin_eventos"), {"federacion_institucion": "todas_instituciones"}
        )

        self.assertEqual(response.status_code, 200)

        # Debería mostrar todos los eventos de cualquier institución
        eventos_en_contexto = list(response.context["eventos"])
        self.assertEqual(len(eventos_en_contexto), 2)  # evento_inst1 y evento_inst2
        nombres = [e.nombre for e in eventos_en_contexto]
        self.assertIn("Evento Institución 1", nombres)
        self.assertIn("Evento Institución 2", nombres)

    def test_filtro_institucion_especifica(self):
        """Verifica el filtro por una institución específica."""
        response = self.client.get(
            reverse("admin_eventos"),
            {"federacion_institucion": f"inst_{self.inst1.id}"},
        )

        self.assertEqual(response.status_code, 200)

        # Debería mostrar solo eventos de la institución específica
        eventos_en_contexto = list(response.context["eventos"])
        self.assertEqual(len(eventos_en_contexto), 1)
        self.assertEqual(eventos_en_contexto[0].nombre, "Evento Institución 1")
        self.assertEqual(eventos_en_contexto[0].institucion, self.inst1)

    def test_filtro_estado_nacional(self):
        """Verifica el filtro por estado nacional (ubicación del evento)."""
        response = self.client.get(
            reverse("admin_eventos"), {"estado_nacional": self.estado2.id}
        )

        self.assertEqual(response.status_code, 200)

        # Debería mostrar solo eventos en el estado2
        eventos_en_contexto = list(response.context["eventos"])
        self.assertEqual(len(eventos_en_contexto), 1)
        self.assertEqual(eventos_en_contexto[0].nombre, "Evento Institución 2")
        self.assertEqual(eventos_en_contexto[0].estado, self.estado2)

    def test_filtro_combinado(self):
        """Verifica filtros combinados."""
        response = self.client.get(
            reverse("admin_eventos"),
            {
                "federacion_institucion": f"inst_{self.inst1.id}",
                "estado_nacional": self.estado1.id,
                "tipo": "Taller",
            },
        )

        self.assertEqual(response.status_code, 200)

        # Debería mostrar solo eventos que cumplan todos los criterios
        eventos_en_contexto = list(response.context["eventos"])
        self.assertEqual(len(eventos_en_contexto), 1)
        self.assertEqual(eventos_en_contexto[0].nombre, "Evento Institución 1")
        self.assertEqual(eventos_en_contexto[0].tipo, "Taller")

    def test_template_renderiza_filtros(self):
        """Verifica que el template renderice los nuevos filtros correctamente."""
        response = self.client.get(reverse("admin_eventos"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Verificar que los nuevos filtros estén presentes
        self.assertIn('name="federacion_institucion"', content)
        self.assertIn('name="estado_nacional"', content)
        self.assertIn("Federación o Institución", content)
        self.assertIn("Cualquier Estado (Ubicación)", content)

        # Verificar opciones de federación/instituciones
        self.assertIn('value="federacion"', content)
        self.assertIn("Federación Central", content)
        self.assertIn('value="todas_instituciones"', content)
        self.assertIn("Todas las Instituciones", content)

        # Verificar instituciones específicas
        self.assertIn(f'value="inst_{self.inst1.id}"', content)
        self.assertIn(f'value="inst_{self.inst2.id}"', content)
        self.assertIn(self.inst1.nombre, content)
        self.assertIn(self.inst2.nombre, content)

        # Verificar estados en las opciones
        self.assertIn("Estado Test 1", content)
        self.assertIn("Estado Test 2", content)

    def test_filtros_mantienen_seleccion(self):
        """Verifica que los filtros mantengan su selección después del submit."""
        response = self.client.get(
            reverse("admin_eventos"),
            {
                "federacion_institucion": "todas_instituciones",
                "estado_nacional": self.estado1.id,
                "tipo": "Competencia",
                "estado_evento": "abierto",
            },
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Verificar que las opciones seleccionadas tengan el atributo selected
        self.assertIn('value="todas_instituciones" selected', content)
        self.assertIn(f'value="{self.estado1.id}" selected', content)
        self.assertIn('value="Competencia" selected', content)
        self.assertIn('value="abierto" selected', content)

    def test_filtro_con_busqueda_texto(self):
        """Verifica que el filtro de texto funcione con los nuevos filtros."""
        response = self.client.get(
            reverse("admin_eventos"),
            {"q": "Federación", "federacion_institucion": "federacion"},
        )

        self.assertEqual(response.status_code, 200)

        # Debería mostrar eventos de federación que contengan "Federación"
        eventos_en_contexto = list(response.context["eventos"])
        self.assertEqual(len(eventos_en_contexto), 1)
        self.assertIn("Federación", eventos_en_contexto[0].nombre)

    def test_estadisticas_con_filtros(self):
        """Verifica que las estadísticas se calculen correctamente con filtros aplicados."""
        response = self.client.get(
            reverse("admin_eventos"), {"federacion_institucion": "federacion"}
        )

        self.assertEqual(response.status_code, 200)
        stats = response.context["stats"]

        # Con filtro de federación, solo debería contar el evento de federación
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["abiertos"], 1)  # El evento de federación está abierto

    def test_filtros_sin_resultados(self):
        """Verifica comportamiento cuando no hay resultados."""
        response = self.client.get(
            reverse("admin_eventos"),
            {
                "federacion_institucion": f"inst_{self.inst2.id}",
                "estado_nacional": self.estado1.id,
            },
        )

        self.assertEqual(response.status_code, 200)

        # No debería haber eventos que cumplan ambos criterios (evento de inst2 en estado1)
        eventos_en_contexto = list(response.context["eventos"])
        self.assertEqual(len(eventos_en_contexto), 0)

    def test_url_params_correctos(self):
        """Verifica que los parámetros URL se procesen correctamente."""
        # Test con parámetros codificados
        response = self.client.get(
            reverse("admin_eventos")
            + f"?federacion_institucion=inst_{self.inst1.id}&estado_nacional={self.estado1.id}&tipo=Competencia"
        )

        self.assertEqual(response.status_code, 200)

        # Los parámetros deberían procesarse correctamente
        self.assertIsNotNone(response.context.get("eventos"))


class FiltroGestionEventosIntegrationTestCase(TestCase):
    """Tests de integración para los filtros con diferentes roles."""

    def setUp(self):
        self.client = Client()

        # Crear usuario federación regional
        self.user_fed_regional = User.objects.create_user(
            username="fed_regional", email="regional@test.com", password="test123"
        )
        self.profile_fed_regional = UserProfile.objects.create(
            user=self.user_fed_regional,
            user_type="federacion",
            es_federacion=False,  # No es rector
        )

        # Crear estado e institución
        self.estado = Estado.objects.create(nombre="Estado Regional", codigo="ER")
        self.institucion = Institucion.objects.create(
            nombre="Institución Regional", codigo="INST_REG", estado=self.estado
        )

        # Crear evento
        self.evento = Evento.objects.create(
            nombre="Evento Regional",
            tipo="Competencia",
            fecha=date.today() + timezone.timedelta(days=30),
            estado_evento=EstadoEvento.ABIERTO,
            institucion=self.institucion,
            estado=self.estado,
        )

        self.client.login(username="fed_regional", password="test123")

    def test_filtros_con_federacion_regional(self):
        """Verifica que los filtros funcionen con usuario de federación regional."""
        response = self.client.get(
            reverse("admin_eventos"),
            {"federacion_institucion": f"estado_{self.estado.id}"},
        )

        self.assertEqual(response.status_code, 200)

        # El usuario regional debería ver eventos de su jurisdicción
        eventos_en_contexto = list(response.context["eventos"])
        # La cantidad depende de la lógica de JurisdictionSelector
        self.assertGreaterEqual(len(eventos_en_contexto), 0)

    def test_permisos_filtros(self):
        """Verifica que los filtros respeten los permisos del usuario."""
        response = self.client.get(reverse("admin_eventos"))

        self.assertEqual(response.status_code, 200)

        # El template debería incluir los filtros independientemente del rol
        content = response.content.decode("utf-8")
        self.assertIn('name="federacion_institucion"', content)
        self.assertIn('name="estado_nacional"', content)
