from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from registry.models import (
    AsistenciaEvento,
    CalificacionClub,
    Club,
    ClubEvento,
    ClubLineaInvestigacion,
    ClubTutor,
    Estado,
    Evento,
    Grupo,
    InscripcionGrupoEvento,
    Institucion,
    LineaInvestigacion,
    Municipio,
    Parroquia,
    Participante,
    ParticipanteGrupo,
    Tutor,
)


class UniqueConstraintModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado, _ = Estado.objects.get_or_create(
            nombre="Zulia Test", defaults={"codigo": "ZULTEST"}
        )
        cls.municipio, _ = Municipio.objects.get_or_create(
            estado=cls.estado, nombre="Maracaibo Test"
        )
        cls.parroquia, _ = Parroquia.objects.get_or_create(
            municipio=cls.municipio, nombre="La Limpia Test"
        )
        cls.user, _ = User.objects.get_or_create(
            username="testuser", defaults={"email": "testuser@example.com"}
        )
        cls.user.set_password("pass")
        cls.user.save(update_fields=["password"])
        cls.institucion = Institucion.objects.create(
            nombre="Instituto Uno",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            email="inst1@example.com",
        )
        cls.participante = Participante.objects.create(
            nacionalidad="V",
            cedula="12345678",
            nombres="Juan",
            apellidos="Pérez",
            fecha_nacimiento=date(2008, 1, 1),
            sexo="M",
            email="juan@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            direccion="Calle 1",
            codigo_area="0424",
            numero_telefono="1234567",
            titulo_universitario="",
            campo1="",
            nombre_representante="María Pérez",
            cedula_representante="8765432",
            codigo_area_representante="0424",
            numero_telefono_representante="7654321",
            email_representante="maria@example.com",
        )
        cls.grupo = Grupo.objects.create(
            nombre="Grupo A",
            criterio="proyecto",
            usuario_creador=cls.user,
            nombre_proyecto="Proyecto X",
        )
        cls.evento = Evento.objects.create(
            nombre="Evento Uno",
            tipo="Taller",
            fecha=date.today(),
            estado_evento="borrador",
            tipo_evento="institucional",
            audiencia="publica",
            es_publico=True,
        )
        cls.club = Club.objects.create(
            nombre="Club Uno",
            descripcion="Descripción del club.",
            ubicacion="Caracas",
        )
        cls.linea = LineaInvestigacion.objects.create(
            codigo="LIN-001", nombre="Línea 1"
        )
        cls.tutor = Tutor.objects.create(
            nacionalidad="V",
            nombres="Laura",
            apellidos="Torres",
            sexo="F",
            cedula="87654321",
            email="laura@example.com",
        )

    def assert_unique_constraint(self, model_cls, **data):
        model_cls.objects.get_or_create(**data)
        duplicate = model_cls(**data)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError):
            duplicate.save()

    def test_municipio_unique_constraint(self):
        self.assert_unique_constraint(
            Municipio,
            estado=self.estado,
            nombre="Maracaibo Test",
        )

    def test_parroquia_unique_constraint(self):
        self.assert_unique_constraint(
            Parroquia,
            municipio=self.municipio,
            nombre="La Limpia Test",
        )

    def test_participante_grupo_unique_constraint(self):
        self.assert_unique_constraint(
            ParticipanteGrupo,
            participante=self.participante,
            grupo=self.grupo,
        )

    def test_asistencia_evento_unique_constraint(self):
        self.assert_unique_constraint(
            AsistenciaEvento,
            evento=self.evento,
            participante=self.participante,
            grupo=self.grupo,
        )

    def test_inscripcion_grupo_evento_unique_constraint(self):
        self.assert_unique_constraint(
            InscripcionGrupoEvento,
            evento=self.evento,
            grupo=self.grupo,
        )

    def test_club_evento_unique_constraint(self):
        self.assert_unique_constraint(
            ClubEvento,
            club=self.club,
            evento=self.evento,
        )

    def test_calificacion_club_unique_constraint(self):
        self.assert_unique_constraint(
            CalificacionClub,
            club=self.club,
            institucion=self.institucion,
            puntuacion=4,
        )

    def test_club_linea_investigacion_unique_constraint(self):
        self.assert_unique_constraint(
            ClubLineaInvestigacion,
            club=self.club,
            linea=self.linea,
        )

    def test_club_tutor_unique_constraint(self):
        self.assert_unique_constraint(
            ClubTutor,
            club=self.club,
            tutor=self.tutor,
            rol="responsable",
        )
