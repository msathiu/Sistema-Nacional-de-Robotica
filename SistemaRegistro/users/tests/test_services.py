from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from registry.models import Participante, Institucion, Estado, Municipio, Parroquia, Evento, Grupo, EstadoEvento
from users.services.participante_service import ParticipanteService
from users.services.institution_service import InstitutionService
from users.services.evento_service import EventoService
from users.services.report_service import ReportService
from users.services.grupo_service import GrupoService
from datetime import date, timedelta


class ServiceIntegrationTests(TestCase):
    def setUp(self):
        # Crear ubicación completa con campos obligatorios
        self.estado = Estado.objects.create(nombre="Test Estado", codigo="TEST")
        self.municipio = Municipio.objects.create(nombre="Test Municipio", estado=self.estado)
        self.parroquia = Parroquia.objects.create(nombre="Test Parroquia", municipio=self.municipio)
        
        # Crear institución con campos obligatorios (usando IDs explícitos)
        self.institucion = Institucion.objects.create(
            nombre="Test Inst",
            email="inst@test.com",
            estado_id=self.estado.id,
            municipio_id=self.municipio.id,
            parroquia_id=self.parroquia.id,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Dirección de prueba"
        )
        
        self.admin_user = User.objects.create_superuser(username="admin", password="password", email="admin@test.com")

    def test_participante_service_creation(self):
        cleaned_data = {
            "nombres": "Juan",
            "apellidos": "Perez",
            "nacionalidad": "V",
            "cedula_personal": "12345678",
            "email": "juan@test.com",
            "fecha_nacimiento": date(2000, 1, 1),
            "sexo": "M",
            "estado": self.estado,
            "municipio": self.municipio,
            "parroquia": self.parroquia,
            "direccion": "Direccion Test",
            "numero_telefono": "1234567",
        }
        
        participante = ParticipanteService.crear_participante_con_usuario(
            cleaned_data=cleaned_data,
            institucion=self.institucion,
            registrado_por=self.admin_user
        )
        
        self.assertEqual(participante.nombres, "Juan")
        self.assertEqual(participante.user.username, "V-12345678")
        self.assertTrue(participante.vinculaciones.filter(institucion=self.institucion).exists())

    def test_participante_reusa_usuario_huerfano_sin_ficha(self):
        """Usuario Django participante existente sin fila Participante: se crea solo la ficha."""
        orphan = User.objects.create_user(
            username="V-55555555",
            password="secret123",
            email="orphan@test.com",
        )
        prof = orphan.userprofile
        prof.user_type = "participante"
        prof.save(update_fields=["user_type"])

        cleaned_data = {
            "nombres": "Ana",
            "apellidos": "Huérfana",
            "nacionalidad": "V",
            "cedula_personal": "55555555",
            "email": "orphan@test.com",
            "fecha_nacimiento": date(2002, 2, 2),
            "sexo": "F",
            "estado": self.estado,
            "municipio": self.municipio,
            "parroquia": self.parroquia,
            "direccion": "Dir",
            "numero_telefono": "1234567",
            "codigo_area": "0412",
        }
        participante = ParticipanteService.crear_participante_con_usuario(
            cleaned_data=cleaned_data,
            institucion=self.institucion,
            registrado_por=self.admin_user,
        )
        self.assertEqual(participante.user_id, orphan.id)
        self.assertEqual(participante.cedula, "55555555")

    def test_institution_service_creation(self):
        data = {
            "nombre": "Nueva Inst",
            "email": "nueva@test.com",
            "telefono": "04121234567",
            "direccion": "Calle Test",
            "tipo_institucion": "publica",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "password": "password123"
        }
        
        inst = InstitutionService.crear_institucion_con_usuario(
            data=data,
            es_central=True
        )
        
        self.assertEqual(inst.nombre, "Nueva Inst")
        self.assertEqual(inst.usuario.username, inst.codigo)
        self.assertEqual(inst.usuario.userprofile.user_type, "institucional")

    def test_participante_vinculacion_regional_central(self):
        # Crear participante sin instituion directa
        cleaned_data = {
            "nombres": "Miguel",
            "apellidos": "Lopez",
            "nacionalidad": "V",
            "cedula_personal": "98765432",
            "email": "miguel@test.com",
            "fecha_nacimiento": date(2005, 5, 5),
            "sexo": "M",
            "estado": self.estado,
            "municipio": self.municipio,
            "parroquia": self.parroquia,
            "direccion": "Direccion test",
            "numero_telefono": "7654321",
            "tipo_vinculacion": "regional",
            "vinculacion_estado": self.estado,
        }

        participante = ParticipanteService.crear_participante_con_usuario(
            cleaned_data=cleaned_data,
            institucion=None,
            registrado_por=self.admin_user,
            user_type_registrador="fed_regional",
            tipo_vinculacion="regional",
            estado_vinculacion=self.estado
        )

        self.assertTrue(participante.creado_por_federacion)
        vinculacion = participante.vinculaciones.filter(tipo_vinculacion="regional", status="activo").first()
        self.assertIsNotNone(vinculacion)
        self.assertEqual(vinculacion.estado, self.estado)

        # Re vincular a central y comprobar que se crea la segunda vinculacion
        participante_central = ParticipanteService.vincular_participante(
            participante=participante,
            tipo_vinculacion="central",
            institucion=None,
            estado=None,
            usuario=self.admin_user
        )
        self.assertEqual(participante_central.tipo_vinculacion, "central")

        # Desvincular regional
        desvincular = ParticipanteService.desvincular_participante(
            participante=participante,
            tipo_vinculacion="regional",
            estado=self.estado,
            usuario=self.admin_user
        )
        self.assertEqual(desvincular.status, "inactivo")

        # Reactivar regional
        react = ParticipanteService.vincular_participante(
            participante=participante,
            tipo_vinculacion="regional",
            estado=self.estado,
            usuario=self.admin_user
        )
        self.assertEqual(react.status, "activo")

    def test_evento_service_creation(self):
        perfil = self.admin_user.userprofile
        data = {
            "nombre": "Evento Test",
            "categoria": "Robótica",
            "fecha": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "descripcion": "Test Desc",
            "estado": self.estado.id,
            "tipo_evento": "institucional",
            "audiencia": "publica",
            "requisitos": "Traer robot"
        }
        
        evento = EventoService.crear_evento(
            user=self.admin_user,
            perfil=perfil,
            data=data
        )
        
        self.assertEqual(evento.nombre, "Evento Test")
        self.assertEqual(evento.estado_evento, EstadoEvento.ABIERTO)

    def test_grupo_service_creation(self):
        grupo = GrupoService.crear_grupo(
            usuario=self.admin_user,
            nombre_grupo="Equipo Alfa"
        )
        
        self.assertEqual(grupo.nombre, "Equipo Alfa")
        self.assertEqual(grupo.usuario_creador, self.admin_user)

    def test_report_service_dashboard_metrics(self):
        # Crear algunos datos
        Participante.objects.create(
            nombres="P1", 
            apellidos="A1", 
            cedula="111", 
            email="p1@t.com", 
            sexo="M", 
            fecha_nacimiento=date(2010, 1, 1),
            estado_id=self.estado.id,
            municipio_id=self.municipio.id,
            parroquia_id=self.parroquia.id,
            direccion="Direccion de prueba",
            numero_telefono="1111111"
        )
        
        metrics = ReportService.get_dashboard_stats(user_type="fed_central")
        
        self.assertGreaterEqual(metrics["total_participantes"], 1)
        self.assertIn("Test Estado", metrics["mapa_data"])

    def test_report_service_institutional_stats_timezone(self):
        """
        Verifica que timezone.now() funciona correctamente para filtrado de fechas
        en get_institutional_stats, especialmente para proximos_eventos.
        """
        # Crear evento futuro público que debería aparecer en proximos_eventos
        # Nota: es_publico=True es requerido por el constraint evento_organizador_valido
        evento_futuro = Evento.objects.create(
            nombre="Evento Futuro Test",
            fecha=timezone.now().date() + timedelta(days=5),
            estado_evento=EstadoEvento.ABIERTO,
            tipo_evento="institucional",
            audiencia="publica",
            es_publico=True,  # Requerido por constraint para eventos institucionales públicos
            activo=True,
            cancelado=False,
            estado_id=self.estado.id,
            municipio_id=self.municipio.id,
            parroquia_id=self.parroquia.id,
        )
        
        # Crear evento pasado que NO debería aparecer
        Evento.objects.create(
            nombre="Evento Pasado Test",
            fecha=timezone.now().date() - timedelta(days=5),
            estado_evento=EstadoEvento.ABIERTO,
            tipo_evento="institucional",
            audiencia="publica",
            es_publico=True,
            activo=True,
            cancelado=False,
            estado_id=self.estado.id,
            municipio_id=self.municipio.id,
            parroquia_id=self.parroquia.id,
        )
        
        # Llamar al servicio
        stats = ReportService.get_institutional_stats(
            user=self.admin_user,
            institution=self.institucion
        )
        
        # Verificar que proximos_eventos existe y contiene el evento futuro
        self.assertIn("proximos_eventos", stats)
        proximos = list(stats["proximos_eventos"])
        
        # El evento futuro debe estar en proximos_eventos
        self.assertEqual(len(proximos), 1)
        self.assertEqual(proximos[0].id, evento_futuro.id)
        self.assertEqual(proximos[0].nombre, "Evento Futuro Test")
