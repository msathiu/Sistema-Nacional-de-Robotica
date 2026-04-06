from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from registry.models import Estado, Institucion, Municipio, Parroquia


class EditarInstitucionModalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Distrito Capital", codigo="DC")
        cls.municipio = Municipio.objects.create(nombre="Libertador", estado=cls.estado)
        cls.parroquia = Parroquia.objects.create(nombre="Catedral", municipio=cls.municipio)

        cls.usuario_institucion = User.objects.create_user(
            username="RNR-TEST",
            email="original@example.com",
            password="Original123!",
        )

        cls.institucion = Institucion.objects.create(
            usuario=cls.usuario_institucion,
            nombre="Institucion Original",
            rif="J-12345678",
            email="original@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            codigo="RNR-TEST",
            direccion="Direccion Original",
            telefono_codigo="0412",
            telefono_numero="1234567",
            telefono="04121234567",
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
        )

        cls.owner_user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="Owner123!",
        )
        owner_profile = cls.owner_user.userprofile
        owner_profile.user_type = "institucional"
        owner_profile.institution = cls.institucion
        owner_profile.estado = cls.estado
        owner_profile.save()

    def test_owner_can_update_institution_modal_with_existing_field_names(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            reverse("editar_institucion_modal", args=[self.institucion.id]),
            {
                "nombre": "Institucion Actualizada",
                "email": "nuevo@example.com",
                "direccion": "Nueva Direccion",
                "rif_letra": "J",
                "rif_numero": "87654321",
                "modal_cod_area": "0414",
                "modal_num_puro": "7654321",
                "new_password": "NuevaClave123!",
                "confirm_password": "NuevaClave123!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("lista_instituciones"))

        self.institucion.refresh_from_db()
        self.usuario_institucion.refresh_from_db()

        self.assertEqual(self.institucion.nombre, "Institucion Actualizada")
        self.assertEqual(self.institucion.email, "nuevo@example.com")
        self.assertEqual(self.institucion.direccion, "Nueva Direccion")
        self.assertEqual(self.institucion.rif, "J-87654321")
        self.assertEqual(self.institucion.telefono_codigo, "0414")
        self.assertEqual(self.institucion.telefono_numero, "7654321")
        self.assertEqual(self.institucion.telefono, "04147654321")
        self.assertEqual(self.usuario_institucion.email, "nuevo@example.com")
        self.assertTrue(check_password("NuevaClave123!", self.usuario_institucion.password))

    def test_invalid_modal_payload_does_not_update_institution(self):
        self.client.force_login(self.owner_user)

        response = self.client.post(
            reverse("editar_institucion_modal", args=[self.institucion.id]),
            {
                "nombre": "Otro Nombre",
                "email": "otro@example.com",
                "direccion": "Otra Direccion",
                "rif_letra": "J",
                "rif_numero": "99999999",
                "modal_cod_area": "0412",
                "modal_num_puro": "123",
                "new_password": "ClaveSegura123!",
                "confirm_password": "Distinta123!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("lista_instituciones"))

        self.institucion.refresh_from_db()
        self.usuario_institucion.refresh_from_db()

        self.assertEqual(self.institucion.nombre, "Institucion Original")
        self.assertEqual(self.institucion.email, "original@example.com")
        self.assertEqual(self.institucion.telefono_numero, "1234567")
        self.assertTrue(check_password("Original123!", self.usuario_institucion.password))
