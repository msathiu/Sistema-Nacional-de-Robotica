from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django import forms

from registry.models import Estado, Municipio, Parroquia, Institucion
from users.forms import ParticipanteRegistrationForm
from users.services.participante_service import ParticipanteService


class ParticipanteRoleFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Prueba Estado", codigo="PR")
        cls.municipio = Municipio.objects.create(nombre="Prueba Municipio", estado=cls.estado)
        cls.parroquia = Parroquia.objects.create(nombre="Prueba Parroquia", municipio=cls.municipio)
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
            data={**self.base_data, "tipo_vinculacion": "institucional", "vinculacion_institucion": self.institucion.id},
            user_role="fed_central",
        )

        self.assertFalse(isinstance(form.fields["tipo_vinculacion"].widget, forms.HiddenInput))
        self.assertFalse(isinstance(form.fields["vinculacion_institucion"].widget, forms.HiddenInput))
        self.assertFalse(isinstance(form.fields["vinculacion_estado"].widget, forms.HiddenInput))
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_form_role_institucional_hides_vinculacion_fields(self):
        form = ParticipanteRegistrationForm(
            data={**self.base_data, "tipo_vinculacion": "central", "vinculacion_institucion": self.institucion.id},
            user_role="institucional",
            user_institution=self.institucion,
        )

        self.assertTrue(isinstance(form.fields["tipo_vinculacion"].widget, forms.HiddenInput))
        self.assertTrue(isinstance(form.fields["vinculacion_institucion"].widget, forms.HiddenInput))
        self.assertTrue(isinstance(form.fields["vinculacion_estado"].widget, forms.HiddenInput))

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data["tipo_vinculacion"], "institucional")
        self.assertEqual(form.cleaned_data["vinculacion_institucion"], self.institucion)

    def test_form_role_fed_regional_hides_all_vinculacion(self):
        form = ParticipanteRegistrationForm(
            data={**self.base_data, "tipo_vinculacion": "regional"},
            user_role="fed_regional",
        )

        self.assertTrue(isinstance(form.fields["tipo_vinculacion"].widget, forms.HiddenInput))
        self.assertTrue(isinstance(form.fields["vinculacion_institucion"].widget, forms.HiddenInput))
        self.assertTrue(isinstance(form.fields["vinculacion_estado"].widget, forms.HiddenInput))

        self.assertTrue(form.is_valid(), msg=form.errors)


#
# Nota: la vista `detalle_participante` (página) fue reemplazada por el modal
# "Expediente Completo" en `lista_participantes.html`. Se eliminó el test que
# validaba esa página.
