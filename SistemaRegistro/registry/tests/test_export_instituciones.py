import csv
from io import StringIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from users.models import UserProfile

from registry.models import Estado, Institucion, Municipio, Parroquia


class InstitucionesExportTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Zulia Test", codigo="ZULTEST")
        cls.municipio = Municipio.objects.create(
            estado=cls.estado, nombre="Maracaibo Test"
        )
        cls.parroquia = Parroquia.objects.create(
            municipio=cls.municipio, nombre="La Limpia Test"
        )

        cls.user = User.objects.create_user(username="fed_central", password="secret")
        UserProfile.objects.filter(user=cls.user).delete()
        cls.profile = UserProfile.objects.create(user=cls.user, user_type="fed_central")

        cls.educativa = Institucion.objects.create(
            nombre="Colegio Export",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            email="colegio@example.com",
            tipo_institucion="educativa",
            naturaleza="publica",
            subcategoria="Subcategoria Educativa",
            categoria="Categoría A",
            codigo_mppe="MPPE-1234",
            rif="J-12345678-9",
            telefono="0414-7654321",
        )

        cls.particular = Institucion.objects.create(
            nombre="Persona Natural Export",
            estado=cls.estado,
            municipio=cls.municipio,
            parroquia=cls.parroquia,
            email="persona@example.com",
            tipo_institucion="particular",
            naturaleza="privada",
            subcategoria="No aplica",
            categoria="No aplica",
            codigo_mppe="MPPE-0000",
            institucion_procedencia="Debería desaparecer",
            particular_nacionalidad="V",
            particular_cedula="12345678",
            telefono_codigo="0412",
            telefono_numero="1234567",
        )

    def test_export_instituciones_blanks_irrelevant_fields(self):
        self.client.force_login(self.user)
        response = self.client.get(
            f"{reverse('exportar_instituciones_excel')}?format=csv"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")

        text = response.content.decode("utf-8-sig")
        reader = csv.DictReader(StringIO(text))
        rows = list(reader)

        self.assertEqual(len(rows), 2)

        fila_particular = next(
            r for r in rows if r["Nombre"] == "Persona Natural Export"
        )
        self.assertEqual(fila_particular["RIF / Cédula"], "V-12345678")
        self.assertEqual(fila_particular["Naturaleza"], "")
        self.assertEqual(fila_particular["Subcategoría"], "")
        self.assertEqual(fila_particular["Categoría"], "")
        self.assertEqual(fila_particular["Dependencia"], "")
        self.assertEqual(fila_particular["Código MPPE"], "")
        self.assertEqual(fila_particular["Institución Procedencia"], "")
        self.assertEqual(fila_particular["Teléfono"], "0412-1234567")

        fila_educativa = next(r for r in rows if r["Nombre"] == "Colegio Export")
        self.assertEqual(fila_educativa["RIF / Cédula"], "J-12345678-9")
        self.assertEqual(fila_educativa["Código MPPE"], "MPPE-1234")
        self.assertEqual(fila_educativa["Teléfono"], "0414-7654321")
