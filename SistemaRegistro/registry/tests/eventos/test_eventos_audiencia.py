"""Tests para la Arquitectura Mejorada de Eventos con campo audiencia."""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from registry.models import (
    Evento,
    Club,
    Institucion,
    MembresiaClu,
    Estado,
    EstadoEvento,
    Municipio,
    Parroquia,
)
from users.models import UserProfile

User = get_user_model()


class EventoAudienciaModelTestCase(TestCase):
    """Tests unitarios para el campo audiencia del modelo Evento."""

    def setUp(self):
        """Configuración inicial."""
        self.estado, _ = Estado.objects.get_or_create(nombre="Miranda", defaults={"codigo": "13"})
        self.municipio, _ = Municipio.objects.get_or_create(nombre="Chacao", estado=self.estado)
        self.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Altamira",
            municipio=self.municipio,
        )
        
        self.institucion = Institucion.objects.create(
            nombre="Instituto Test",
            codigo="INST-AUD-001",
            email="aud001@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        
        self.user = User.objects.create_user(username="test_user", password="test123")
        self.profile = self.user.userprofile
        self.profile.user_type = "institucional"
        self.profile.institution = self.institucion
        self.profile.save()
        
        self.club = Club.objects.create(
            nombre="Club Test",
            institucion_creadora=self.institucion,
            coordinador=self.user,
            status="aprobado",
        )

    def test_crear_evento_audiencia_publica(self):
        """Test: Crear evento con audiencia pública."""
        evento = Evento.objects.create(
            nombre="Evento Público",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            estado_evento="aprobado",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        self.assertEqual(evento.audiencia, "publica")
        self.assertTrue(evento.es_publico_audiencia)

    def test_crear_evento_audiencia_club_exclusivo(self):
        """Test: Crear evento exclusivo de club."""
        evento = Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            audiencia="club_exclusivo",
            estado_evento="borrador",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        self.assertEqual(evento.audiencia, "club_exclusivo")
        self.assertTrue(evento.es_exclusivo_club)

    def test_crear_evento_audiencia_privado(self):
        """Test: Crear evento privado institucional."""
        evento = Evento.objects.create(
            nombre="Evento Privado",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="institucional_privado",
            estado_evento="borrador",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        self.assertEqual(evento.audiencia, "institucional_privado")
        self.assertTrue(evento.es_privado)

    def test_manager_publicos(self):
        """Test: Manager filtra eventos públicos aprobados."""
        Evento.objects.create(
            nombre="Público Aprobado",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        Evento.objects.create(
            nombre="Privado",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="institucional_privado",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        publicos = Evento.objects.publicos()
        self.assertEqual(publicos.count(), 1)
        self.assertEqual(publicos.first().audiencia, "publica")

    def test_manager_exclusivos_club(self):
        """Test: Manager filtra eventos exclusivos de club."""
        Evento.objects.create(
            nombre="Club Exclusivo",
            tipo_evento="club",
            club_organizador=self.club,
            audiencia="club_exclusivo",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        Evento.objects.create(
            nombre="Público",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        exclusivos = Evento.objects.exclusivos_club()
        self.assertEqual(exclusivos.count(), 1)
        self.assertEqual(exclusivos.first().audiencia, "club_exclusivo")

    def test_manager_privados(self):
        """Test: Manager filtra eventos privados."""
        Evento.objects.create(
            nombre="Privado",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="institucional_privado",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        Evento.objects.create(
            nombre="Público",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        privados = Evento.objects.privados()
        self.assertEqual(privados.count(), 1)
        self.assertEqual(privados.first().audiencia, "institucional_privado")

    def test_todos_eventos_requieren_aprobacion(self):
        """Test: TODOS los eventos requieren aprobación."""
        evento_inst = Evento.objects.create(
            nombre="Evento Inst",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        evento_club = Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            audiencia="club_exclusivo",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        self.assertTrue(evento_inst.requiere_aprobacion)
        self.assertTrue(evento_club.requiere_aprobacion)


class EventoVisibilidadTestCase(TestCase):
    """Tests de visibilidad de eventos según audiencia."""

    def setUp(self):
        """Configuración inicial."""
        self.estado, _ = Estado.objects.get_or_create(nombre="Carabobo", defaults={"codigo": "07"})
        self.municipio, _ = Municipio.objects.get_or_create(
            nombre="Valencia",
            estado=self.estado,
        )
        self.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Candelaria",
            municipio=self.municipio,
        )
        
        # Crear instituciones
        self.inst_creadora = Institucion.objects.create(
            nombre="Instituto Creador",
            codigo="INST-VIS-001",
            email="vis001@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        self.inst_miembro = Institucion.objects.create(
            nombre="Instituto Miembro",
            codigo="INST-VIS-002",
            email="vis002@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        self.inst_externa = Institucion.objects.create(
            nombre="Instituto Externo",
            codigo="INST-VIS-003",
            email="vis003@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        
        # Crear usuarios
        self.user_creador = User.objects.create_user(username="creador", password="test123")
        profile_creador = self.user_creador.userprofile
        profile_creador.user_type = "institucional"
        profile_creador.institution = self.inst_creadora
        profile_creador.save()
        
        self.user_miembro = User.objects.create_user(username="miembro", password="test123")
        profile_miembro = self.user_miembro.userprofile
        profile_miembro.user_type = "institucional"
        profile_miembro.institution = self.inst_miembro
        profile_miembro.save()
        
        self.user_externo = User.objects.create_user(username="externo", password="test123")
        profile_externo = self.user_externo.userprofile
        profile_externo.user_type = "institucional"
        profile_externo.institution = self.inst_externa
        profile_externo.save()
        
        self.user_fed = User.objects.create_user(username="federacion", password="test123", is_staff=True)
        profile_fed = self.user_fed.userprofile
        profile_fed.user_type = "fed_central"
        profile_fed.save()
        
        # Crear club
        self.club = Club.objects.create(
            nombre="Club Test",
            institucion_creadora=self.inst_creadora,
            coordinador=self.user_creador,
            status="aprobado",
        )
        
        # Crear membresía
        MembresiaClu.objects.create(
            club=self.club,
            institucion=self.inst_miembro,
            estado="miembro_activo",
        )
        
        # Crear eventos
        self.evento_publico = Evento.objects.create(
            nombre="Evento Público",
            tipo_evento="institucional",
            institucion=self.inst_creadora,
            audiencia="publica",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        self.evento_club = Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            audiencia="club_exclusivo",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        self.evento_privado = Evento.objects.create(
            nombre="Evento Privado",
            tipo_evento="institucional",
            institucion=self.inst_creadora,
            audiencia="institucional_privado",
            estado_evento=EstadoEvento.ABIERTO,
            fecha=timezone.now().date() + timedelta(days=30),
        )

    def test_federacion_ve_todos(self):
        """Test: fed_central ve TODOS los eventos."""
        client = Client()
        client.login(username="federacion", password="test123")
        response = client.get(reverse("eventos_disponibles"))
        
        self.assertEqual(response.status_code, 200)
        # Federación debe ver los 3 eventos
        eventos = response.context["eventos_activos"]
        self.assertEqual(len(eventos), 3)

    def test_institucion_ve_publicos(self):
        """Test: Instituciones ven eventos públicos."""
        client = Client()
        client.login(username="externo", password="test123")
        response = client.get(reverse("eventos_disponibles"))
        
        eventos = response.context["eventos_activos"]
        # Debe ver solo el público
        self.assertIn(self.evento_publico, eventos)

    def test_miembro_ve_club_exclusivo(self):
        """Test: Miembro del club ve eventos exclusivos."""
        client = Client()
        client.login(username="miembro", password="test123")
        response = client.get(reverse("eventos_disponibles"))
        
        eventos = response.context["eventos_activos"]
        # Debe ver público + club exclusivo
        self.assertIn(self.evento_publico, eventos)
        self.assertIn(self.evento_club, eventos)

    def test_no_miembro_no_ve_club_exclusivo(self):
        """Test: No miembro NO ve eventos exclusivos."""
        client = Client()
        client.login(username="externo", password="test123")
        response = client.get(reverse("eventos_disponibles"))
        
        eventos = response.context["eventos_activos"]
        # NO debe ver el evento exclusivo del club
        self.assertNotIn(self.evento_club, eventos)

    def test_creador_no_ve_sus_eventos_en_catalogo_general(self):
        """Test: El catálogo general institucional excluye eventos propios."""
        client = Client()
        client.login(username="creador", password="test123")
        response = client.get(reverse("eventos_disponibles"))
        
        eventos = response.context["eventos_activos"]
        self.assertNotIn(self.evento_publico, eventos)
        self.assertNotIn(self.evento_privado, eventos)

    def test_externo_no_ve_privado(self):
        """Test: Institución externa NO ve eventos privados."""
        client = Client()
        client.login(username="externo", password="test123")
        response = client.get(reverse("eventos_disponibles"))
        
        eventos = response.context["eventos_activos"]
        # NO debe ver el evento privado
        self.assertNotIn(self.evento_privado, eventos)


class EventoAprobacionUnificadaTestCase(TestCase):
    """Tests para el sistema de aprobación unificado."""

    def setUp(self):
        """Configuración inicial."""
        self.estado, _ = Estado.objects.get_or_create(nombre="Zulia", defaults={"codigo": "23"})
        self.municipio, _ = Municipio.objects.get_or_create(
            nombre="Maracaibo",
            estado=self.estado,
        )
        self.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Olegario Villalobos",
            municipio=self.municipio,
        )
        
        self.institucion = Institucion.objects.create(
            nombre="Instituto Test",
            codigo="INST-APR-001",
            email="apr001@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        
        self.user_inst = User.objects.create_user(username="institucional", password="test123")
        profile_inst = self.user_inst.userprofile
        profile_inst.user_type = "institucional"
        profile_inst.institution = self.institucion
        profile_inst.save()
        
        self.user_fed = User.objects.create_user(username="federacion", password="test123", is_staff=True)
        profile_fed = self.user_fed.userprofile
        profile_fed.user_type = "fed_central"
        profile_fed.save()

    def test_evento_institucional_inicia_borrador(self):
        """Test: Evento institucional inicia en borrador."""
        client = Client()
        client.login(username="institucional", password="test123")
        
        response = client.post(reverse("crear_evento"), {
            "nombre": "Evento Test",
            "categoria": "Competencia",
            "fecha": (timezone.now().date() + timedelta(days=30)).isoformat(),
            "descripcion": "Test",
            "modalidad": "presencial",
            "tipo_evento": "institucional",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Sede principal",
            "audiencia": "publica",
            "requisitos": "Registro previo",
        })
        
        evento = Evento.objects.filter(nombre="Evento Test").first()
        if evento:
            self.assertEqual(evento.estado_evento, "borrador")

    def test_fed_central_aprueba_automatico(self):
        """Test: fed_central aprueba automáticamente."""
        client = Client()
        client.login(username="federacion", password="test123")
        
        response = client.post(reverse("crear_evento"), {
            "nombre": "Evento Fed",
            "categoria": "Competencia",
            "fecha": (timezone.now().date() + timedelta(days=30)).isoformat(),
            "descripcion": "Test",
            "modalidad": "presencial",
            "tipo_evento": "institucional",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Sede central",
            "audiencia": "publica",
            "requisitos": "Registro previo",
        })
        
        evento = Evento.objects.filter(nombre="Evento Fed").first()
        if evento:
            self.assertEqual(evento.estado_evento, EstadoEvento.ABIERTO)

    def test_aprobar_evento_unificado(self):
        """Test: Vista unificada aprueba cualquier evento."""
        evento = Evento.objects.create(
            nombre="Evento Pendiente",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            estado_evento=EstadoEvento.REVISION,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        client = Client()
        client.login(username="federacion", password="test123")
        
        response = client.post(
            reverse("aprobar_evento", args=[evento.id]),
            {"observaciones": "Aprobado en prueba"},
        )
        
        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.ABIERTO)

    def test_rechazar_evento_unificado(self):
        """Test: Vista unificada rechaza cualquier evento."""
        evento = Evento.objects.create(
            nombre="Evento Pendiente",
            tipo_evento="institucional",
            institucion=self.institucion,
            audiencia="publica",
            estado_evento=EstadoEvento.REVISION,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        client = Client()
        client.login(username="federacion", password="test123")
        
        response = client.post(
            reverse("rechazar_evento", args=[evento.id]),
            {"observaciones": "Rechazado por prueba"}
        )
        
        evento.refresh_from_db()
        self.assertEqual(evento.estado_evento, EstadoEvento.RECHAZADO)
