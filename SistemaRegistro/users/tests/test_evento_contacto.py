from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from registry.models import Estado, Evento, Institucion, Municipio, Parroquia

from users.forms import EventoContactDataForm
from users.services.evento_service import EventoService


class EventoContactValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Estado Evento Contacto", codigo="EC")
        cls.municipio = Municipio.objects.create(
            nombre="Municipio Evento Contacto",
            estado=cls.estado,
        )
        cls.parroquia = Parroquia.objects.create(
            nombre="Parroquia Evento Contacto",
            municipio=cls.municipio,
        )
        cls.institucion = Institucion.objects.create(
            nombre="Institucion Evento Contacto",
            email="evento-contacto@example.com",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            estatus="aprobado",
            activa=True,
            tipo_institucion="educativa",
            direccion="Av. Principal",
        )
        cls.user = User.objects.create_user(
            username="institucional_evento",
            password="testpass123",
        )
        cls.user.userprofile.user_type = "institucional"
        cls.user.userprofile.institution = cls.institucion
        cls.user.userprofile.estado = cls.estado
        cls.user.userprofile.save()

    def test_evento_contact_form_rechaza_telefono_con_letras(self):
        form = EventoContactDataForm(
            data={
                "telefono_codigo": "0412",
                "telefono_numero": "12AB567",
                "email_contacto": "evento@test.com",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("telefono_numero", form.errors)
        self.assertIn("solo dígitos", form.errors["telefono_numero"][0])

    def test_evento_contact_form_rechaza_codigo_sin_numero(self):
        form = EventoContactDataForm(
            data={
                "telefono_codigo": "0412",
                "telefono_numero": "",
                "email_contacto": "evento@test.com",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("telefono_numero", form.errors)
        self.assertIn(
            "Debe indicar el número de teléfono cuando se selecciona el código de área.",
            form.errors["telefono_numero"],
        )

    def test_evento_contact_form_rechaza_numero_sin_codigo(self):
        form = EventoContactDataForm(
            data={
                "telefono_codigo": "",
                "telefono_numero": "1234567",
                "email_contacto": "evento@test.com",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("telefono_codigo", form.errors)
        self.assertIn(
            "Debe indicar el código de área cuando se ingresa un teléfono de contacto.",
            form.errors["telefono_codigo"],
        )

    def test_evento_contact_form_requiere_telefono_o_email(self):
        form = EventoContactDataForm(
            data={
                "telefono_codigo": "",
                "telefono_numero": "",
                "email_contacto": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "Debe proporcionar al menos un teléfono o un correo de contacto.",
            form.errors["__all__"],
        )

    def test_evento_service_rechaza_telefono_con_letras(self):
        with self.assertRaisesMessage(
            ValueError,
            "El teléfono de contacto debe contener solo dígitos.",
        ):
            EventoService.crear_evento(
                user=self.user,
                perfil=self.user.userprofile,
                data={
                    "nombre": "Evento Teléfono Inválido",
                    "categoria": "Competencia",
                    "fecha": (date.today() + timedelta(days=10)).isoformat(),
                    "descripcion": "Prueba",
                    "modalidad": "presencial",
                    "tipo_evento": "institucional",
                    "estado": self.estado.id,
                    "municipio": self.municipio.id,
                    "parroquia": self.parroquia.id,
                    "direccion": "Sede Principal",
                    "audiencia": "publica",
                    "telefono_codigo": "0412",
                    "telefono_numero": "12AB567",
                    "email_contacto": "evento@test.com",
                },
            )

    def test_crear_evento_template_renderiza_input_telefono_reforzado(self):
        client = Client()
        client.force_login(self.user)

        response = client.get(reverse("crear_evento"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="telefono_numero"', content)
        self.assertIn('inputmode="numeric"', content)
        self.assertIn('pattern="[0-9]{7}"', content)

    def test_post_crear_evento_invalido_no_crea_registro(self):
        client = Client()
        client.force_login(self.user)

        response = client.post(
            reverse("crear_evento"),
            data={
                "nombre": "Evento No Debe Crear",
                "categoria": "Competencia",
                "fecha": (date.today() + timedelta(days=10)).isoformat(),
                "descripcion": "Prueba",
                "modalidad": "presencial",
                "tipo_evento": "institucional",
                "estado": self.estado.id,
                "municipio": self.municipio.id,
                "parroquia": self.parroquia.id,
                "direccion": "Sede Principal",
                "audiencia": "publica",
                "telefono_codigo": "0412",
                "telefono_numero": "12AB567",
                "email_contacto": "evento@test.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Evento.objects.filter(nombre="Evento No Debe Crear").exists())
