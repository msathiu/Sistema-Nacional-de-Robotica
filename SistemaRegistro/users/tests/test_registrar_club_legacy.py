from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RegistrarClubLegacyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.institucional_user = User.objects.create_user(
            username="institucional-club",
            password="testpass123",
            email="inst@example.com",
        )
        perfil_inst = cls.institucional_user.userprofile
        perfil_inst.user_type = "institucional"
        perfil_inst.save()

        cls.fed_central_user = User.objects.create_user(
            username="central-club",
            password="testpass123",
            email="central@example.com",
        )
        perfil_central = cls.fed_central_user.userprofile
        perfil_central.user_type = "fed_central"
        perfil_central.save()

        cls.participante_user = User.objects.create_user(
            username="participante-club",
            password="testpass123",
            email="part@example.com",
        )
        perfil_part = cls.participante_user.userprofile
        perfil_part.user_type = "participante"
        perfil_part.save()

    def test_registrar_club_requires_login(self):
        response = self.client.get(reverse("registrar_club"))
        self.assertEqual(response.status_code, 302)

    def test_institucional_is_redirected_to_official_club_flow(self):
        self.client.force_login(self.institucional_user)
        response = self.client.get(reverse("registrar_club"))
        self.assertRedirects(response, reverse("crear_club"))

    def test_fed_central_is_redirected_to_official_club_flow(self):
        self.client.force_login(self.fed_central_user)
        response = self.client.get(reverse("registrar_club"))
        self.assertRedirects(response, reverse("crear_club"))

    def test_participante_cannot_access_legacy_club_registration(self):
        self.client.force_login(self.participante_user)
        response = self.client.get(reverse("registrar_club"), follow=True)
        self.assertRedirects(response, reverse("dashboard"))
