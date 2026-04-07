from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from registry.models import (
    Estado,
    Grupo,
    Institucion,
    Municipio,
    Parroquia,
    Participante,
    ParticipanteInstitucion,
)

from users.forms import ParticipanteRegistrationForm


class ParticipanteRoleFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Prueba Estado", codigo="PR")
        cls.municipio = Municipio.objects.create(
            nombre="Prueba Municipio", estado=cls.estado
        )
        cls.parroquia = Parroquia.objects.create(
            nombre="Prueba Parroquia", municipio=cls.municipio
        )
        cls.institucion = Institucion.objects.create(
            nombre="Institucion Prueba",
            email="instprueba@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Calle Prueba 123",
        )

        cls.base_data = {
            "nombres": "Pedro",
            "apellidos": "Martinez",
            "fecha_nacimiento": date(2000, 1, 1),  # 26 años - mayor de edad
            "sexo": "M",
            "nacionalidad": "V",
            "codigo_area": "0414",
            "numero_telefono": "1234567",
            "direccion": "Av. Ejemplo 123",
            "estado": cls.estado.id,
            "municipio": cls.municipio.id,
            "parroquia": cls.parroquia.id,
            "grado_escolar": "NO",
            "email": "pedro.martinez@example.com",
            "cedula_personal": "12345678",
            # Campos de representante vacíos (no requeridos para mayores de edad)
            "nombre_representante": "",
            "nacionalidad_representante": "V",
            "cedula_representante": "",
            "codigo_area_representante": "",
            "numero_telefono_representante": "",
            "email_representante": "",
        }

    def test_form_role_fed_central_shows_vinculacion_fields(self):
        form = ParticipanteRegistrationForm(
            data={
                **self.base_data,
                "tipo_vinculacion": "institucional",
                "vinculacion_institucion": self.institucion.id,
            },
            user_role="fed_central",
        )

        self.assertFalse(
            isinstance(form.fields["tipo_vinculacion"].widget, forms.HiddenInput)
        )
        self.assertFalse(
            isinstance(form.fields["vinculacion_institucion"].widget, forms.HiddenInput)
        )
        self.assertFalse(
            isinstance(form.fields["vinculacion_estado"].widget, forms.HiddenInput)
        )
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_form_role_institucional_hides_vinculacion_fields(self):
        form = ParticipanteRegistrationForm(
            data={
                **self.base_data,
                "tipo_vinculacion": "central",
                "vinculacion_institucion": self.institucion.id,
            },
            user_role="institucional",
            user_institution=self.institucion,
        )

        self.assertTrue(
            isinstance(form.fields["tipo_vinculacion"].widget, forms.HiddenInput)
        )
        self.assertTrue(
            isinstance(form.fields["vinculacion_institucion"].widget, forms.HiddenInput)
        )
        self.assertTrue(
            isinstance(form.fields["vinculacion_estado"].widget, forms.HiddenInput)
        )

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data["tipo_vinculacion"], "institucional")
        self.assertEqual(form.cleaned_data["vinculacion_institucion"], self.institucion)

    def test_form_rechaza_municipio_que_no_pertenece_al_estado(self):
        estado_2 = Estado.objects.create(nombre="Estado Otro", codigo="EO")
        municipio_2 = Municipio.objects.create(nombre="Otro Municipio", estado=estado_2)
        parroquia_2 = Parroquia.objects.create(
            nombre="Otra Parroquia", municipio=municipio_2
        )

        datos = {
            **self.base_data,
            "estado": self.estado.id,
            "municipio": municipio_2.id,
            "parroquia": parroquia_2.id,
            "tipo_vinculacion": "institucional",
            "vinculacion_institucion": self.institucion.id,
        }

        form = ParticipanteRegistrationForm(
            data=datos,
            user_role="fed_central",
        )

        self.assertFalse(form.is_valid())
        self.assertIn("municipio", form.errors)
        self.assertIn(
            "no pertenece al estado",
            form.errors["municipio"][0],
        )

    def test_form_role_fed_regional_hides_all_vinculacion(self):
        form = ParticipanteRegistrationForm(
            data={**self.base_data, "tipo_vinculacion": "regional"},
            user_role="fed_regional",
        )

        self.assertTrue(
            isinstance(form.fields["tipo_vinculacion"].widget, forms.HiddenInput)
        )
        self.assertTrue(
            isinstance(form.fields["vinculacion_institucion"].widget, forms.HiddenInput)
        )
        self.assertTrue(
            isinstance(form.fields["vinculacion_estado"].widget, forms.HiddenInput)
        )

        self.assertTrue(form.is_valid(), msg=form.errors)


#
# Nota: la vista `detalle_participante` (página) fue reemplazada por el modal
# "Expediente Completo" en `lista_participantes.html`. Se eliminó el test que
# validaba esa página.


class ParticipanteAccessControlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado_1 = Estado.objects.create(nombre="Estado Uno", codigo="E1")
        cls.estado_2 = Estado.objects.create(nombre="Estado Dos", codigo="E2")

        cls.municipio_1 = Municipio.objects.create(
            nombre="Municipio Uno", estado=cls.estado_1
        )
        cls.municipio_2 = Municipio.objects.create(
            nombre="Municipio Dos", estado=cls.estado_2
        )

        cls.parroquia_1 = Parroquia.objects.create(
            nombre="Parroquia Uno", municipio=cls.municipio_1
        )
        cls.parroquia_2 = Parroquia.objects.create(
            nombre="Parroquia Dos", municipio=cls.municipio_2
        )

        cls.institucion_1 = Institucion.objects.create(
            nombre="Institucion Uno",
            email="inst1@example.com",
            estado=cls.estado_1,
            municipio=cls.municipio_1,
            parroquia=cls.parroquia_1,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Direccion 1",
        )
        cls.institucion_2 = Institucion.objects.create(
            nombre="Institucion Dos",
            email="inst2@example.com",
            estado=cls.estado_2,
            municipio=cls.municipio_2,
            parroquia=cls.parroquia_2,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Direccion 2",
        )

        cls.inst_user = User.objects.create_user(
            username="institucional", password="testpass123"
        )
        cls.inst_profile = cls.inst_user.userprofile
        cls.inst_profile.user_type = "institucional"
        cls.inst_profile.institution = cls.institucion_1
        cls.inst_profile.estado = cls.estado_1
        cls.inst_profile.save()

        cls.other_inst_user = User.objects.create_user(
            username="institucional2", password="testpass123"
        )
        cls.other_inst_profile = cls.other_inst_user.userprofile
        cls.other_inst_profile.user_type = "institucional"
        cls.other_inst_profile.institution = cls.institucion_2
        cls.other_inst_profile.estado = cls.estado_2
        cls.other_inst_profile.save()

        cls.participant_user = User.objects.create_user(
            username="participante", password="testpass123"
        )
        cls.participant_profile = cls.participant_user.userprofile
        cls.participant_profile.user_type = "participante"
        cls.participant_profile.save()

        cls.participante_inst_1 = Participante.objects.create(
            user=cls.participant_user,
            nombres="Ana",
            apellidos="Perez",
            fecha_nacimiento=date(2000, 1, 1),
            sexo="F",
            nacionalidad="V",
            cedula="11111111",
            email="ana@example.com",
            estado=cls.estado_1,
            municipio=cls.municipio_1,
            parroquia=cls.parroquia_1,
            direccion="Direccion A",
            codigo_area="0412",
            numero_telefono="1234567",
            grado_escolar="NO",
        )
        cls.participante_inst_2 = Participante.objects.create(
            nombres="Luis",
            apellidos="Gomez",
            fecha_nacimiento=date(2001, 2, 2),
            sexo="M",
            nacionalidad="V",
            cedula="22222222",
            email="luis@example.com",
            estado=cls.estado_2,
            municipio=cls.municipio_2,
            parroquia=cls.parroquia_2,
            direccion="Direccion B",
            codigo_area="0412",
            numero_telefono="7654321",
            grado_escolar="NO",
        )

        ParticipanteInstitucion.objects.create(
            participante=cls.participante_inst_1,
            institucion=cls.institucion_1,
            tipo_vinculacion="institucional",
            status="activo",
            registrado_por=cls.inst_user,
        )
        ParticipanteInstitucion.objects.create(
            participante=cls.participante_inst_2,
            institucion=cls.institucion_2,
            tipo_vinculacion="institucional",
            status="activo",
            registrado_por=cls.other_inst_user,
        )

    def test_participante_detail_requires_login(self):
        response = self.client.get(
            reverse("participante_detail", args=[self.participante_inst_1.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_institucional_cannot_open_other_institution_participant_detail(self):
        self.client.force_login(self.inst_user)
        response = self.client.get(
            reverse("participante_detail", args=[self.participante_inst_2.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_institucional_cannot_edit_other_institution_participant_full_view(self):
        self.client.force_login(self.inst_user)
        response = self.client.get(
            reverse("editar_participante", args=[self.participante_inst_2.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_participant_can_open_own_legacy_detail(self):
        self.client.force_login(self.participant_user)
        response = self.client.get(
            reverse("participante_detail", args=[self.participante_inst_1.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_participante_delete_requires_post(self):
        central = User.objects.create_user(username="fedc_post_chk", password="testpass123")
        cp = central.userprofile
        cp.user_type = "fed_central"
        cp.save()
        self.client.force_login(central)
        response = self.client.get(
            reverse("participante_delete", args=[self.participante_inst_1.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_institucional_cannot_delete_other_institution_participant(self):
        self.client.force_login(self.inst_user)
        response = self.client.post(
            reverse("participante_delete", args=[self.participante_inst_2.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_institucional_cannot_delete_participant_without_permission(self):
        self.client.force_login(self.inst_user)
        response = self.client.post(
            reverse("participante_delete", args=[self.participante_inst_1.pk]),
            follow=True,
        )
        self.assertRedirects(response, reverse("lista_participantes"))
        self.assertTrue(
            Participante.objects.filter(pk=self.participante_inst_1.pk).exists()
        )

    def test_fed_central_cannot_delete_participant_in_active_grupo(self):
        central = User.objects.create_user(username="fedc_grupo", password="testpass123")
        cp = central.userprofile
        cp.user_type = "fed_central"
        cp.save()
        grupo = Grupo.objects.create(
            nombre="Equipo Test Bloqueo",
            usuario_creador=central,
            criterio="proyecto",
            activo=True,
        )
        grupo.participantes.add(self.participante_inst_1)

        self.client.force_login(central)
        response = self.client.post(
            reverse("participante_delete", args=[self.participante_inst_1.pk]),
            follow=True,
        )
        self.assertRedirects(response, reverse("lista_participantes"))
        self.assertTrue(
            Participante.objects.filter(pk=self.participante_inst_1.pk).exists()
        )

    def test_institucional_can_edit_own_participant(self):
        self.client.force_login(self.inst_user)

        response = self.client.post(
            reverse("editar_participante", args=[self.participante_inst_1.pk]),
            data={
                "nombres": "Ana Maria",
                "apellidos": self.participante_inst_1.apellidos,
                "fecha_nacimiento": self.participante_inst_1.fecha_nacimiento.isoformat(),
                "sexo": self.participante_inst_1.sexo,
                "nacionalidad": self.participante_inst_1.nacionalidad,
                "cedula_personal": self.participante_inst_1.cedula,
                "cedula_escolar_input": "",
                "condicion_tea": "False",
                "tipo_vinculacion": "institucional",
                "vinculacion_institucion": self.institucion_1.pk,
                "vinculacion_estado": "",
                "codigo_area": self.participante_inst_1.codigo_area,
                "numero_telefono": self.participante_inst_1.numero_telefono,
                "estado": self.participante_inst_1.estado_id,
                "municipio": self.participante_inst_1.municipio_id,
                "parroquia": self.participante_inst_1.parroquia_id,
                "direccion": self.participante_inst_1.direccion,
                "grado_escolar": self.participante_inst_1.grado_escolar,
                "titulo_universitario": "",
                "campo1": "",
                "nombre_representante": "",
                "nacionalidad_representante": "V",
                "cedula_representante": "",
                "codigo_area_representante": "",
                "numero_telefono_representante": "",
                "email_representante": "",
                "email": "ana.actualizada@example.com",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("lista_participantes"))
        self.participante_inst_1.refresh_from_db()
        self.assertEqual(self.participante_inst_1.nombres, "Ana Maria")
        self.assertEqual(self.participante_inst_1.email, "ana.actualizada@example.com")
        self.assertEqual(
            self.participante_inst_1.user.email, "ana.actualizada@example.com"
        )

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(
            any("actualizados" in message for message in messages),
            msg=messages,
        )
