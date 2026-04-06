from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from registry.forms import ClubForm
from registry.models import LineaInvestigacion


class ClubFormValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.linea_1 = LineaInvestigacion.objects.create(
            codigo="L001", nombre="Robótica", activa=True, orden=1
        )
        cls.linea_2 = LineaInvestigacion.objects.create(
            codigo="L002", nombre="Inteligencia Artificial", activa=True, orden=2
        )
        cls.base_data = {
            "nombre": "Club de Robótica",
            "siglas": "CR",
            "descripcion": "Un club para estudiantes interesados en tecnología.",
            "ubicacion": "Escuela Central",
            "fecha_fundacion": date(2020, 1, 1),
            "estado_vinculacion": "abierto",
            "cupo_maximo": 10,
            "requisitos": "Ser mayor de 14 años.",
            "documento_legal": "Resolución #123",
            "linea_investigacion_1": cls.linea_1.id,
            "linea_investigacion_2": "",
            "linea_investigacion_3": "",
        }

    def test_rechaza_lineas_repetidas(self):
        data = {**self.base_data, "linea_investigacion_2": self.linea_1.id}
        form = ClubForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "No puede seleccionar la misma línea de investigación más de una vez.",
            form.non_field_errors(),
        )

    def test_rechaza_fecha_fundacion_futura(self):
        fecha_futura = timezone.now().date() + timedelta(days=30)
        data = {**self.base_data, "fecha_fundacion": fecha_futura.isoformat()}
        form = ClubForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_fundacion", form.errors)
        self.assertIn(
            "La fecha de fundación no puede ser futura.", form.errors["fecha_fundacion"]
        )

    def test_sanitiza_descripcion_html(self):
        datos = {
            **self.base_data,
            "descripcion": "<p>Descripción</p><script>alert('xss')</script>",
        }
        form = ClubForm(data=datos)

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertNotIn("<script>", form.cleaned_data["descripcion"])
        self.assertIn("Descripción", form.cleaned_data["descripcion"])

    def test_rechaza_cupo_maximo_fuera_de_rango(self):
        data = {**self.base_data, "cupo_maximo": 101}
        form = ClubForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("cupo_maximo", form.errors)
        self.assertIn(
            "El cupo máximo debe ser un número entre 1 y 100.",
            form.errors["cupo_maximo"],
        )
