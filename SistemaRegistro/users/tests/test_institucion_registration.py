"""
Tests exhaustivos para el registro de instituciones.
Valida todos los escenarios críticos identificados en el análisis.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from registry.models import Institucion, Estado, Municipio, Parroquia
from users.forms import InstitucionRegistrationForm
from users.services.institution_service import InstitutionService
import logging

logger = logging.getLogger(__name__)


class InstitucionRegistrationFormTests(TestCase):
    """Tests del formulario de registro de instituciones"""

    @classmethod
    def setUpTestData(cls):
        """Configurar datos de prueba"""
        # Crear estado, municipio, parroquia (usar get_or_create porque las migraciones ya cargan datos)
        cls.estado, _ = Estado.objects.get_or_create(
            nombre="Miranda", defaults={"codigo": "08"}
        )
        cls.municipio, _ = Municipio.objects.get_or_create(
            nombre="Baruta", estado=cls.estado
        )
        cls.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Baruta", municipio=cls.municipio
        )

    def get_valid_form_data(self, tipo="educativa"):
        """Retorna datos válidos para el formulario"""
        return {
            "tipo_institucion": tipo,
            "nombre": "Instituto Prueba",
            "email": "instituto@example.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Calle principal 123",
            "naturaleza": "publica" if tipo in ["educativa", "otra"] else "",
            "subcategoria": "primaria" if tipo == "educativa" else "",
            "rif_letra": "J",
            "rif_numero": "123456789",
            "codigo_area": "0212",
            "numero_telefono": "5551234",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "codigo_mppe": "ME123456" if tipo == "educativa" else "",
        }

    # ============================================================
    # TEST 1: REGISTRO EXITOSO - INSTITUCIÓN EDUCATIVA
    # ============================================================
    def test_registro_institucion_educativa_exitoso(self):
        """Flujo completo: institución educativa con RIF válido"""
        data = self.get_valid_form_data(tipo="educativa")
        form = InstitucionRegistrationForm(data)

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data["tipo_institucion"], "educativa")
        self.assertEqual(form.cleaned_data["naturaleza"], "publica")
        self.assertIsNotNone(form.cleaned_data.get("rif_numero"))

    # ============================================================
    # TEST 2: REGISTRO EXITOSO - PERSONA PARTICULAR
    # ============================================================
    def test_registro_particular_exitoso(self):
        """Flujo completo: persona natural con validaciones específicas"""
        data = {
            "tipo_institucion": "particular",
            "particular_nombres": "Juan",
            "particular_apellidos": "Pérez",
            "particular_nacionalidad": "V",
            "particular_cedula": "12345678",
            "email": "juan@example.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Calle prueba 456",
            "codigo_area": "0414",
            "numero_telefono": "5551234",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }
        form = InstitucionRegistrationForm(data)

        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data["tipo_institucion"], "particular")
        self.assertEqual(form.cleaned_data["particular_nombres"], "Juan")
        self.assertIsNone(form.cleaned_data.get("rif"))

    # ============================================================
    # TEST 3: VALIDACIÓN - EMAIL DUPLICADO
    # ============================================================
    def test_email_duplicado_rechazado(self):
        """Validación: email ya registrado"""
        # Crear institución existente
        Institucion.objects.create(
            nombre="Instituto Existente",
            email="duplicado@example.com",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            tipo_institucion="educativa",
            rif="J-12345678",
            telefono="02125551234",
        )

        # Intentar crear otra con mismo email
        data = self.get_valid_form_data()
        data["email"] = "duplicado@example.com"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Ya existe una institución registrada con este correo", str(form.errors)
        )

    # ============================================================
    # TEST 4: VALIDACIÓN - RIF + NOMBRE + UBICACIÓN DUPLICADO
    # ============================================================
    def test_rif_nombre_ubicacion_duplicado_rechazado(self):
        """Validación: RIF + nombre + ubicación exacta ya existe"""
        # Crear institución existente
        Institucion.objects.create(
            nombre="Instituto Principal",
            email="principal@example.com",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            tipo_institucion="educativa",
            rif="J-12345678",
            telefono="02125551234",
        )

        # Intentar crear otra con mismo RIF, nombre, ubicación
        data = self.get_valid_form_data()
        data["nombre"] = "Instituto Principal"
        data["rif_numero"] = "123456789"
        data["email"] = "otro@example.com"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Ya existe una institución registrada", str(form.non_field_errors())
        )

    # ============================================================
    # TEST 5: VALIDACIÓN - CÉDULA PARTICULAR DUPLICADA
    # ============================================================
    def test_cedula_particular_unica(self):
        """Validación: cédula ya registrada para persona natural"""
        # Crear institución particular existente
        Institucion.objects.create(
            nombre="Juan Pérez",
            email="juan1@example.com",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            tipo_institucion="particular",
            particular_nombres="Juan",
            particular_apellidos="Pérez",
            particular_cedula="12345678",
            particular_nacionalidad="V",
            telefono="04145551234",
        )

        # Intentar crear otra con cédula duplicada
        data = {
            "tipo_institucion": "particular",
            "particular_nombres": "Juan",
            "particular_apellidos": "García",
            "particular_nacionalidad": "V",
            "particular_cedula": "12345678",
            "email": "juang@example.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Otra calle 789",
            "codigo_area": "0416",
            "numero_telefono": "5551234",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("ya registrada", str(form.errors))

    # ============================================================
    # TEST 6: VALIDACIÓN - PASSWORD DÉBIL (Sin mayúscula)
    # ============================================================
    def test_password_sin_mayuscula_rechazado(self):
        """Validación: password sin mayúscula (nueva validación fuerte)"""
        data = self.get_valid_form_data()
        data["password"] = "securepass123!"
        data["confirm_password"] = "securepass123!"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("mayúscula", str(form.errors))

    # ============================================================
    # TEST 7: VALIDACIÓN - PASSWORD DÉBIL (Sin número)
    # ============================================================
    def test_password_sin_numero_rechazado(self):
        """Validación: password sin número (nueva validación fuerte)"""
        data = self.get_valid_form_data()
        data["password"] = "SecurePassWord!"
        data["confirm_password"] = "SecurePassWord!"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("número", str(form.errors))

    # ============================================================
    # TEST 8: VALIDACIÓN - PASSWORD DÉBIL (Sin carácter especial)
    # ============================================================
    def test_password_sin_especial_rechazado(self):
        """Validación: password sin carácter especial (nueva validación fuerte)"""
        data = self.get_valid_form_data()
        data["password"] = "SecurePass123"
        data["confirm_password"] = "SecurePass123"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("especial", str(form.errors))

    # ============================================================
    # TEST 9: VALIDACIÓN - PASSWORD DÉBIL (Menos de 8 caracteres)
    # ============================================================
    def test_password_corto_rechazado(self):
        """Validación: password con menos de 8 caracteres"""
        data = self.get_valid_form_data()
        data["password"] = "Sec12!"
        data["confirm_password"] = "Sec12!"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("Mínimo 8", str(form.errors))

    # ============================================================
    # TEST 10: VALIDACIÓN - PASSWORDS NO COINCIDEN
    # ============================================================
    def test_passwords_no_coinciden_rechazado(self):
        """Validación: confirmación de password no coincide"""
        data = self.get_valid_form_data()
        data["password"] = "SecurePass123!"
        data["confirm_password"] = "DifferentPass123!"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("no coinciden", str(form.errors))

    # ============================================================
    # TEST 11: VALIDACIÓN - TELÉFONO SOLO ACEPTA DÍGITOS
    # ============================================================
    def test_numero_telefono_con_letras_rechazado(self):
        """Validación: el número telefónico no debe aceptar letras."""
        data = self.get_valid_form_data()
        data["numero_telefono"] = "12AB567"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("solo dígitos", str(form.errors))

    # ============================================================
    # TEST 12: VALIDACIÓN - TELÉFONO SE NORMALIZA DESDE FORMATO SEGURO
    # ============================================================
    def test_numero_telefono_con_separadores_rechazado(self):
        """Validación: el teléfono debe llegar como 7 dígitos estrictos."""
        data = self.get_valid_form_data()
        data["numero_telefono"] = "555-1234"
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("numero_telefono", form.errors)

    # ============================================================
    # TEST 11: VALIDACIÓN - CASCADA UBICACIÓN (Municipio no en Estado)
    # ============================================================
    def test_municipio_no_pertenece_estado_rechazado(self):
        """Validación: municipio no pertenece al estado seleccionado"""
        # Crear otro estado y municipio
        otro_estado, _ = Estado.objects.get_or_create(
            nombre="Aragua", defaults={"codigo": "07"}
        )
        otro_municipio, _ = Municipio.objects.get_or_create(
            nombre="SanJaviera", estado=otro_estado
        )

        data = self.get_valid_form_data()
        data["estado"] = self.estado.id  # Estado: Miranda
        data["municipio"] = otro_municipio.id  # Municipio de Aragua
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("no pertenece", str(form.errors))

    # ============================================================
    # TEST 12: VALIDACIÓN - CASCADA UBICACIÓN (Parroquia no en Municipio)
    # ============================================================
    def test_parroquia_no_pertenece_municipio_rechazado(self):
        """Validación: parroquia no pertenece al municipio seleccionado"""
        # Crear otro municipio y parroquia
        otro_municipio, _ = Municipio.objects.get_or_create(
            nombre="Chacao", estado=self.estado
        )
        otra_parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Chacao", municipio=otro_municipio
        )

        data = self.get_valid_form_data()
        data["municipio"] = self.municipio.id  # Municipio: Baruta
        data["parroquia"] = otra_parroquia.id  # Parroquia de Chacao
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("no pertenece", str(form.errors))

    # ============================================================
    # TEST 13: VALIDACIÓN - FORMATO RIF CONSISTENTE (9 dígitos)
    # ============================================================
    def test_formato_rif_9_digitos_guardado_consistente(self):
        """Validación: RIF con 9 dígitos se guarda en formato consistente"""
        data = self.get_valid_form_data()
        data["rif_numero"] = "123456789"  # 9 dígitos
        form = InstitucionRegistrationForm(data)

        self.assertTrue(form.is_valid(), msg=form.errors)
        instance = form.save(commit=False)
        # Debe ser J-12345678-9 (8 + guion + 1)
        self.assertIn("-", instance.rif)
        self.assertTrue(instance.rif.startswith("J-"))

    # ============================================================
    # TEST 14: VALIDACIÓN - FORMATO RIF CONSISTENTE (10 dígitos)
    # ============================================================
    def test_formato_rif_10_digitos_guardado_consistente(self):
        """Validación: RIF con 10 dígitos se guarda en formato consistente"""
        data = self.get_valid_form_data()
        data["rif_numero"] = "1234567890"  # 10 dígitos
        form = InstitucionRegistrationForm(data)

        self.assertTrue(form.is_valid(), msg=form.errors)
        instance = form.save(commit=False)
        # Debe ser J-12345678-90 (8 + guion + 2)
        rif_parts = instance.rif.split("-")
        self.assertEqual(len(rif_parts), 3)
        self.assertEqual(rif_parts[0], "J")
        self.assertEqual(len(rif_parts[1]), 8)
        self.assertEqual(len(rif_parts[2]), 2)

    # ============================================================
    # TEST 15: VALIDACIÓN - TELÉFONO 7 DÍGITOS
    # ============================================================
    def test_telefono_7_digitos_requerido(self):
        """Validación: teléfono debe tener exactamente 7 dígitos"""
        data = self.get_valid_form_data()
        data["numero_telefono"] = "555123"  # 6 dígitos
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("numero_telefono", form.errors)

    # ============================================================
    # TEST 16: VALIDACIÓN - CAMPOS PERSONA NATURAL REQUERIDOS
    # ============================================================
    def test_particular_campos_requeridos(self):
        """Validación: persona natural debe tener nombres, apellidos, nacionalidad, cédula"""
        data = {
            "tipo_institucion": "particular",
            "particular_nombres": "",  # Falta
            "particular_apellidos": "Pérez",
            "particular_nacionalidad": "V",
            "particular_cedula": "12345678",
            "email": "test@example.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Calle 123",
            "codigo_area": "0414",
            "numero_telefono": "5551234",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }
        form = InstitucionRegistrationForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn("particular_nombres", form.errors)

    # ============================================================
    # TEST 17: GUARDADO CORRECTO DE CÉDULA LIMPIA
    # ============================================================
    def test_cedula_limpia_sin_caracteres_especiales(self):
        """Validación: cédula se guarda sin caracteres especiales"""
        data = {
            "tipo_institucion": "particular",
            "particular_nombres": "Carlos",
            "particular_apellidos": "López",
            "particular_nacionalidad": "V",
            "particular_cedula": "123.456.789",  # Con puntos
            "email": "carlos@example.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Calle 456",
            "codigo_area": "0416",
            "numero_telefono": "5552222",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }
        form = InstitucionRegistrationForm(data)

        self.assertTrue(form.is_valid(), msg=form.errors)
        instance = form.save(commit=False)
        # Debe estar limpiada
        self.assertEqual(instance.particular_cedula, "123456789")

    # ============================================================
    # TEST 18: GUARDADO CORRECTO DE TELÉFONO CONCATENADO
    # ============================================================
    def test_telefono_concatenado_correctamente(self):
        """Validación: teléfono se guarda concatenando código + número"""
        data = self.get_valid_form_data()
        data["codigo_area"] = "0212"
        data["numero_telefono"] = "5551234"
        form = InstitucionRegistrationForm(data)

        self.assertTrue(form.is_valid(), msg=form.errors)
        instance = form.save(commit=False)
        # Debe concatenarse: 0212 + 5551234 = 02125551234
        self.assertEqual(instance.telefono, "02125551234")


class InstitucionRegistrationViewTests(TestCase):
    """Tests de la vista de registro de instituciones"""

    @classmethod
    def setUpTestData(cls):
        """Configurar datos de prueba"""
        cls.estado, _ = Estado.objects.get_or_create(
            nombre="Carabobo", defaults={"codigo": "03"}
        )
        cls.municipio, _ = Municipio.objects.get_or_create(
            nombre="Valencia", estado=cls.estado
        )
        cls.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Sucre", municipio=cls.municipio
        )

    def setUp(self):
        """Setup para cada test"""
        self.client = Client()
        self.url = reverse("registrar_institucion")

    # ============================================================
    # TEST 19: GET - Página carga correctamente
    # ============================================================
    def test_get_registrar_institucion_carga_correctamente(self):
        """Vista GET: página carga con formulario"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("registroForm", response.content.decode())
        self.assertIn("tipoInstitucion", response.content.decode())
        self.assertIn('inputmode="numeric"', response.content.decode())
        self.assertIn('pattern="[0-9]{7}"', response.content.decode())

    # ============================================================
    # TEST 20: POST - Registro exitoso crea Usuario
    # ============================================================
    def test_post_registro_exitoso_crea_usuario(self):
        """Vista POST: registro exitoso crea usuario y institución"""
        data = {
            "tipo_institucion": "educativa",
            "nombre": "Nueva Escuela",
            "email": "nueva.escuela@test.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Calle Principal 100",
            "naturaleza": "publica",
            "subcategoria": "primaria",
            "rif_letra": "G",
            "rif_numero": "9876543210",
            "codigo_area": "0241",
            "numero_telefono": "5559999",
            "password": "NewPass123@",
            "confirm_password": "NewPass123@",
            "codigo_mppe": "ME999999",
        }

        # Realizar POST
        response = self.client.post(self.url, data, follow=True)

        # Verificar que se creó la institución
        self.assertTrue(
            Institucion.objects.filter(email="nueva.escuela@test.com").exists()
        )

        # Verificar que se creó el usuario
        institucion = Institucion.objects.get(email="nueva.escuela@test.com")
        self.assertIsNotNone(institucion.usuario)

    # ============================================================
    # TEST 21: POST - Error de validación retorna forma
    # ============================================================
    def test_post_error_validacion_retorna_formulario(self):
        """Vista POST: error de validación retorna formulario con datos"""
        data = {
            "tipo_institucion": "educativa",
            "nombre": "Escuela Error",
            "email": "escuela@test.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Calle 50",
            "naturaleza": "publica",
            "subcategoria": "primaria",
            "rif_letra": "J",
            "rif_numero": "123",  # Insuficiente
            "codigo_area": "0241",
            "numero_telefono": "555",  # Insuficiente
            "password": "Pass123",  # Sin especial
            "confirm_password": "Pass123",
        }

        response = self.client.post(self.url, data)

        # Debe retornar 200 (no redirect)
        self.assertEqual(response.status_code, 200)
        # Formulario en contexto
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertIn("numero_telefono", form.errors)
        self.assertIn(
            "al menos 7",
            form.errors["numero_telefono"][0],
        )


class InstitucionServiceTests(TestCase):
    """Tests del servicio de creación de instituciones"""

    @classmethod
    def setUpTestData(cls):
        """Configurar datos de prueba"""
        cls.estado, _ = Estado.objects.get_or_create(
            nombre="Lara", defaults={"codigo": "09"}
        )
        cls.municipio, _ = Municipio.objects.get_or_create(
            nombre="Iribarren", estado=cls.estado
        )
        cls.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Guarenas", municipio=cls.municipio
        )

    # ============================================================
    # TEST 22: Servicio crea institución con formato RIF correcto
    # ============================================================
    def test_servicio_crea_institucion_rif_formato_consistente(self):
        """InstitutionService: crea institución con RIF en formato consistente"""
        data = {
            "tipo_institucion": "publica",
            "nombre": "Escuela Pública Prueba",
            "email": "escuela.publica@test.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Avenida 20",
            "rif_letra": "J",
            "rif_numero": "111111111",
            "codigo_area": "0251",
            "numero_telefono": "4445555",
            "password": "ServicePass123!",
        }

        # Usar servicio
        institucion = InstitutionService.crear_institucion_con_usuario(
            data=data, es_central=True
        )

        # Verificar formato RIF
        self.assertIsNotNone(institucion.rif)
        self.assertTrue(institucion.rif.startswith("J-"))
        self.assertIn("-", institucion.rif)

    # ============================================================
    # TEST 23: Servicio rechaza duplicidad
    # ============================================================
    def test_servicio_rechaza_institucion_duplicada(self):
        """InstitutionService: lanza error si institución duplicada"""
        # Crear primera
        Institucion.objects.create(
            nombre="Original",
            email="original@test.com",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
            tipo_institucion="publica",
            rif="J-11111111",
            telefono="02514445555",
        )

        # Intentar crear duplicada
        data = {
            "tipo_institucion": "publica",
            "nombre": "Original",
            "email": "otro@test.com",
            "estado": self.estado.id,
            "municipio": self.municipio.id,
            "parroquia": self.parroquia.id,
            "direccion": "Calle 30",
            "rif_letra": "J",
            "rif_numero": "111111111",
            "codigo_area": "0251",
            "numero_telefono": "4446666",
            "password": "ServicePass123!",
        }

        with self.assertRaises(ValueError) as context:
            InstitutionService.crear_institucion_con_usuario(data=data, es_central=True)

        self.assertIn("Ya existe", str(context.exception))


# ============================================================
# UTILIDADES PARA TESTING
# ============================================================
class TestResumenExecution:
    """Resumen de tests ejecutados"""

    TESTS_TOTAL = 23
    TESTS_CRITICOS = 15

    @staticmethod
    def report():
        return f"""
        ╔════════════════════════════════════════════════╗
        ║   SUITE DE TESTS - REGISTRO INSTITUCIONES    ║
        ║   Total de Tests: {TestResumenExecution.TESTS_TOTAL}                       ║
        ║   Tests Críticos: {TestResumenExecution.TESTS_CRITICOS}                      ║
        ╚════════════════════════════════════════════════╝

        ✓ VALIDACIONES IMPLEMENTADAS:
          1. Email único
          2. RIF + Nombre + Ubicación única
          3. Cédula única (personas naturales)
          4. Password fuerte (mayús + número + especial + 8 chars)
          5. Cascada de ubicación (municipio en estado, parroquia en municipio)
          6. Formato RIF consistente
          7. Teléfono 7 dígitos
          8. Campos personales (particulares)
        """
