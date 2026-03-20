from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from registry.models import Estado, Grupo, Institucion, Municipio, Parroquia


User = get_user_model()


class GruposPermisosFederacionTestCase(TestCase):
    def setUp(self):
        self.estado, _ = Estado.objects.get_or_create(
            nombre="Distrito Capital",
            defaults={"codigo": "01"},
        )
        self.municipio, _ = Municipio.objects.get_or_create(
            nombre="Libertador",
            estado=self.estado,
        )
        self.parroquia, _ = Parroquia.objects.get_or_create(
            nombre="Catedral",
            municipio=self.municipio,
        )

        self.institucion = Institucion.objects.create(
            nombre="Institucion Creadora",
            codigo="INST-GRP-001",
            email="inst1@example.com",
            tipo_institucion="publica",
            estado=self.estado,
            municipio=self.municipio,
            parroquia=self.parroquia,
        )

        self.usuario_institucional = User.objects.create_user(
            username="institucional1",
            password="test12345",
        )
        perfil_institucional = self.usuario_institucional.userprofile
        perfil_institucional.user_type = "institucional"
        perfil_institucional.institution = self.institucion
        perfil_institucional.save()

        self.usuario_fed = User.objects.create_user(
            username="fedcentral1",
            password="test12345",
        )
        perfil_fed = self.usuario_fed.userprofile
        perfil_fed.user_type = "fed_central"
        perfil_fed.save()

        self.grupo = Grupo.objects.create(
            nombre="Equipo Alpha",
            criterio="proyecto",
            nombre_proyecto="Robotica Escolar",
            usuario_creador=self.usuario_institucional,
            institucion=self.institucion,
            estado_grupo="editable",
            activo=True,
        )

    def test_fed_central_lista_grupos_sin_acciones_de_edicion(self):
        self.client.force_login(self.usuario_fed)

        response = self.client.get(reverse("mis_grupos"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["mostrar_institucion"])
        self.assertEqual(len(response.context["grupos"]), 1)
        grupo = response.context["grupos"][0]
        self.assertEqual(grupo["id"], self.grupo.id)
        self.assertEqual(grupo["institucion_nombre"], self.institucion.nombre_publico)
        self.assertFalse(grupo["puede_editar"])
        self.assertFalse(grupo["puede_eliminar"])

    def test_fed_central_puede_ver_detalle_de_grupo_institucional(self):
        self.client.force_login(self.usuario_fed)

        response = self.client.get(reverse("ver_grupo", args=[self.grupo.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["grupo"].id, self.grupo.id)
        self.assertFalse(response.context["puede_editar"])
        self.assertFalse(response.context["puede_eliminar"])
        self.assertEqual(response.context["dashboard_url"], "dashboard")

    def test_institucion_creadora_mantiene_permiso_de_edicion(self):
        self.client.force_login(self.usuario_institucional)

        response = self.client.get(reverse("mis_grupos"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["mostrar_institucion"])
        grupo = response.context["grupos"][0]
        self.assertTrue(grupo["puede_editar"])
        self.assertTrue(grupo["puede_eliminar"])
