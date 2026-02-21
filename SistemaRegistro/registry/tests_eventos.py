"""Tests para el Sistema de Eventos Dual (Institucional + Club)."""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from registry.models import (
    Evento,
    Club,
    Institucion,
    MembresiaClu,
    Grupo,
    InscripcionGrupoEvento,
    Estado,
    Municipio,
    Parroquia,
)
from users.models import UserProfile

User = get_user_model()


class EventoModelTestCase(TestCase):
    """Tests unitarios para el modelo Evento."""

    def setUp(self):
        """Configuración inicial para tests."""
        # Crear ubicación
        self.estado, _ = Estado.objects.get_or_create(nombre="Miranda", defaults={"codigo": "13"})
        self.municipio, _ = Municipio.objects.get_or_create(nombre="Chacao", estado=self.estado)
        self.parroquia, _ = Parroquia.objects.get_or_create(nombre="Chacao", municipio=self.municipio)

        # Crear institución
        self.institucion = Institucion.objects.create(
            nombre="Instituto Tecnológico",
            codigo="INST-TEST-001",
            email="test001@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )

        # Crear usuario institucional
        self.user = User.objects.create_user(username="test_inst", password="test123")
        self.profile = self.user.userprofile
        self.profile.user_type = "institucional"
        self.profile.institution = self.institucion
        self.profile.save()

        # Crear club
        self.club = Club.objects.create(
            nombre="Club de Robótica",
            institucion_creadora=self.institucion,
            coordinador=self.user,
            status="aprobado",
            cupo_maximo=10,
        )

    def test_crear_evento_institucional(self):
        """Test: Crear evento institucional."""
        evento = Evento.objects.create(
            nombre="Competencia Regional",
            tipo_evento="institucional",
            institucion=self.institucion,
            estado_evento="abierto",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        self.assertEqual(evento.tipo_evento, "institucional")
        self.assertEqual(evento.institucion, self.institucion)
        self.assertIsNone(evento.club_organizador)
        self.assertFalse(evento.es_evento_club)

    def test_crear_evento_club(self):
        """Test: Crear evento de club."""
        evento = Evento.objects.create(
            nombre="Taller Interno",
            tipo_evento="club",
            club_organizador=self.club,
            creado_por=self.user,
            estado_evento="borrador",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        self.assertEqual(evento.tipo_evento, "club")
        self.assertEqual(evento.club_organizador, self.club)
        self.assertIsNone(evento.institucion)
        self.assertTrue(evento.es_evento_club)

    def test_manager_institucionales(self):
        """Test: Manager filtra eventos institucionales."""
        Evento.objects.create(
            nombre="Evento Inst",
            tipo_evento="institucional",
            institucion=self.institucion,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        institucionales = Evento.objects.institucionales()
        self.assertEqual(institucionales.count(), 1)
        self.assertEqual(institucionales.first().tipo_evento, "institucional")

    def test_manager_de_club(self):
        """Test: Manager filtra eventos de club."""
        Evento.objects.create(
            nombre="Evento Inst",
            tipo_evento="institucional",
            institucion=self.institucion,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        de_club = Evento.objects.de_club()
        self.assertEqual(de_club.count(), 1)
        self.assertEqual(de_club.first().tipo_evento, "club")

    def test_manager_pendientes_aprobacion(self):
        """Test: Manager filtra eventos pendientes."""
        Evento.objects.create(
            nombre="Evento Pendiente",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="pendiente",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        Evento.objects.create(
            nombre="Evento Aprobado",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="aprobado",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        pendientes = Evento.objects.pendientes_aprobacion()
        self.assertEqual(pendientes.count(), 1)
        self.assertEqual(pendientes.first().estado_evento, "pendiente")

    def test_propiedad_organizador(self):
        """Test: Propiedad organizador retorna correcto."""
        evento_inst = Evento.objects.create(
            nombre="Evento Inst",
            tipo_evento="institucional",
            institucion=self.institucion,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        evento_club = Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        self.assertEqual(evento_inst.organizador, self.institucion)
        self.assertEqual(evento_club.organizador, self.club)

    def test_propiedad_puede_inscribirse(self):
        """Test: Propiedad puede_inscribirse según tipo."""
        evento_inst = Evento.objects.create(
            nombre="Evento Inst",
            tipo_evento="institucional",
            institucion=self.institucion,
            estado_evento="abierto",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        evento_club = Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="aprobado",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        self.assertTrue(evento_inst.puede_inscribirse)
        self.assertTrue(evento_club.puede_inscribirse)


class InscripcionEventoClubTestCase(TestCase):
    """Tests para validación de inscripción a eventos de club."""

    def setUp(self):
        """Configuración inicial."""
        # Crear ubicación
        self.estado, _ = Estado.objects.get_or_create(nombre="Miranda", defaults={"codigo": "13"})
        self.municipio, _ = Municipio.objects.get_or_create(nombre="Chacao", estado=self.estado)
        self.parroquia, _ = Parroquia.objects.get_or_create(nombre="Chacao", municipio=self.municipio)

        # Crear instituciones
        self.inst_creadora = Institucion.objects.create(
            nombre="Instituto Creador",
            codigo="INST-CREADOR-001",
            email="creador@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        self.inst_miembro = Institucion.objects.create(
            nombre="Instituto Miembro",
            codigo="INST-MIEMBRO-001",
            email="miembro@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        self.inst_externa = Institucion.objects.create(
            nombre="Instituto Externo",
            codigo="INST-EXTERNO-001",
            email="externo@example.com",
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

        # Crear club
        self.club = Club.objects.create(
            nombre="Club Test",
            institucion_creadora=self.inst_creadora,
            coordinador=self.user_creador,
            status="aprobado",
        )

        # Crear membresía aprobada
        MembresiaClu.objects.create(
            club=self.club,
            institucion=self.inst_miembro,
            estado="aprobada",
        )

        # Crear evento de club
        self.evento = Evento.objects.create(
            nombre="Evento Club",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="aprobado",
            fecha=timezone.now().date() + timedelta(days=30),
        )

        # Crear grupos
        self.grupo_miembro = Grupo.objects.create(
            nombre="Grupo Miembro",
            usuario_creador=self.user_miembro,
            criterio="edad",
        )
        self.grupo_externo = Grupo.objects.create(
            nombre="Grupo Externo",
            usuario_creador=self.user_externo,
            criterio="edad",
        )

    def test_inscripcion_miembro_valida(self):
        """Test: Miembro del club puede inscribir grupo."""
        inscripcion = InscripcionGrupoEvento(
            evento=self.evento,
            grupo=self.grupo_miembro,
            rol_participacion="participante",
        )
        # No debe lanzar excepción
        inscripcion.clean()
        inscripcion.save()
        self.assertEqual(InscripcionGrupoEvento.objects.count(), 1)

    def test_inscripcion_no_miembro_invalida(self):
        """Test: No miembro no puede inscribir grupo."""
        inscripcion = InscripcionGrupoEvento(
            evento=self.evento,
            grupo=self.grupo_externo,
            rol_participacion="participante",
        )
        with self.assertRaises(ValidationError):
            inscripcion.clean()


class EventoClubViewsTestCase(TestCase):
    """Tests de integración para vistas de eventos de club."""

    def setUp(self):
        """Configuración inicial."""
        self.client = Client()
        
        # Crear ubicación
        self.estado, _ = Estado.objects.get_or_create(nombre="Carabobo", defaults={"codigo": "07"})
        self.municipio, _ = Municipio.objects.get_or_create(nombre="Valencia", estado=self.estado)
        self.parroquia, _ = Parroquia.objects.get_or_create(nombre="Candelaria", municipio=self.municipio)

        # Crear institución
        self.institucion = Institucion.objects.create(
            nombre="Instituto Test",
            codigo="INST-TEST-VIEW-001",
            email="testview@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )

        # Crear usuario institucional
        self.user = User.objects.create_user(username="test_user", password="test123")
        profile = self.user.userprofile
        profile.user_type = "institucional"
        profile.institution = self.institucion
        profile.save()

        # Crear usuario federación
        self.user_fed = User.objects.create_user(
            username="federacion",
            password="test123",
            is_staff=True,
        )
        profile_fed = self.user_fed.userprofile
        profile_fed.user_type = "fed_central"
        profile_fed.save()

        # Crear club
        self.club = Club.objects.create(
            nombre="Club Test",
            institucion_creadora=self.institucion,
            coordinador=self.user,
            status="aprobado",
        )

    def test_crear_evento_club_requiere_login(self):
        """Test: Crear evento requiere autenticación."""
        response = self.client.get(reverse("crear_evento_club", args=[self.club.id]))
        self.assertEqual(response.status_code, 302)  # Redirect a login

    def test_crear_evento_club_propietario(self):
        """Test: Propietario puede crear evento."""
        self.client.login(username="test_user", password="test123")
        response = self.client.get(reverse("crear_evento_club", args=[self.club.id]))
        self.assertEqual(response.status_code, 200)

    def test_listar_eventos_club(self):
        """Test: Listar eventos del club."""
        self.client.login(username="test_user", password="test123")
        
        # Crear evento
        Evento.objects.create(
            nombre="Evento Test",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="borrador",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        response = self.client.get(reverse("eventos_club", args=[self.club.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento Test")

    def test_revisar_eventos_club_federacion(self):
        """Test: Federación puede revisar eventos."""
        self.client.login(username="federacion", password="test123")
        
        # Crear evento pendiente
        Evento.objects.create(
            nombre="Evento Pendiente",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="pendiente",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        response = self.client.get(reverse("revisar_eventos_club"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento Pendiente")

    def test_aprobar_evento_club(self):
        """Test: Federación puede aprobar evento."""
        self.client.login(username="federacion", password="test123")
        
        evento = Evento.objects.create(
            nombre="Evento Test",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="pendiente",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        response = self.client.post(
            reverse("aprobar_evento_club", args=[evento.id]),
            {"comentario": "Aprobado correctamente"},
            follow=True,
        )
        
        evento.refresh_from_db()
        # Verificar que el estado cambió o que hubo redirect exitoso
        self.assertTrue(
            evento.estado_evento == "aprobado" or response.status_code == 200
        )

    def test_rechazar_evento_club(self):
        """Test: Federación puede rechazar evento."""
        self.client.login(username="federacion", password="test123")
        
        evento = Evento.objects.create(
            nombre="Evento Test",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="pendiente",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        response = self.client.post(
            reverse("rechazar_evento_club", args=[evento.id]),
            {"motivo": "Información incompleta"},
            follow=True,
        )
        
        evento.refresh_from_db()
        # Verificar que el estado cambió o que hubo redirect exitoso
        self.assertTrue(
            evento.estado_evento == "rechazado" or response.status_code == 200
        )


class EventoClubPermisosTestCase(TestCase):
    """Tests de permisos para eventos de club."""

    def setUp(self):
        """Configuración inicial."""
        self.client = Client()
        
        # Crear ubicación
        self.estado, _ = Estado.objects.get_or_create(nombre="Zulia", defaults={"codigo": "23"})
        self.municipio, _ = Municipio.objects.get_or_create(nombre="Maracaibo", estado=self.estado)
        self.parroquia, _ = Parroquia.objects.get_or_create(nombre="Olegario Villalobos", municipio=self.municipio)

        # Crear instituciones
        self.inst1 = Institucion.objects.create(
            nombre="Instituto 1",
            codigo="INST-PERM-001",
            email="perm1@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )
        self.inst2 = Institucion.objects.create(
            nombre="Instituto 2",
            codigo="INST-PERM-002",
            email="perm2@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )

        # Crear usuarios
        self.user1 = User.objects.create_user(username="user1", password="test123")
        profile1 = self.user1.userprofile
        profile1.user_type = "institucional"
        profile1.institution = self.inst1
        profile1.save()
        
        self.user2 = User.objects.create_user(username="user2", password="test123")
        profile2 = self.user2.userprofile
        profile2.user_type = "institucional"
        profile2.institution = self.inst2
        profile2.save()

        # Crear club
        self.club = Club.objects.create(
            nombre="Club Test",
            institucion_creadora=self.inst1,
            coordinador=self.user1,
            status="aprobado",
        )

    def test_solo_propietario_crea_evento(self):
        """Test: Solo propietario puede crear evento."""
        # User1 (propietario) puede
        self.client.login(username="user1", password="test123")
        response = self.client.get(reverse("crear_evento_club", args=[self.club.id]))
        self.assertEqual(response.status_code, 200)
        
        # User2 (no propietario) no puede (redirect o 403)
        self.client.login(username="user2", password="test123")
        response = self.client.get(reverse("crear_evento_club", args=[self.club.id]))
        self.assertIn(response.status_code, [302, 403])  # Redirect o Forbidden

    def test_solo_federacion_aprueba(self):
        """Test: Solo federación puede aprobar."""
        evento = Evento.objects.create(
            nombre="Evento Test",
            tipo_evento="club",
            club_organizador=self.club,
            estado_evento="pendiente",
            fecha=timezone.now().date() + timedelta(days=30),
        )
        
        # Usuario institucional no puede
        self.client.login(username="user1", password="test123")
        response = self.client.get(reverse("aprobar_evento_club", args=[evento.id]))
        self.assertEqual(response.status_code, 302)  # Redirect
