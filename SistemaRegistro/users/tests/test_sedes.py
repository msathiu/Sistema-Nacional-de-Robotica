from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from registry.models import Estado
from users.models import UserProfile


class EliminarSedeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estado = Estado.objects.create(nombre="Miranda", codigo="MI")

        cls.central_user = User.objects.create_user(
            username="central",
            password="testpass123",
        )
        cls.central_profile = cls.central_user.userprofile
        cls.central_profile.user_type = "fed_central"
        cls.central_profile.save()

        cls.regional_user = User.objects.create_user(
            username="regional",
            password="testpass123",
            first_name="Ana",
            last_name="Regional",
        )
        cls.regional_profile = cls.regional_user.userprofile
        cls.regional_profile.user_type = "fed_regional"
        cls.regional_profile.estado = cls.estado
        cls.regional_profile.save()

        cls.institucional_user = User.objects.create_user(
            username="institucional",
            password="testpass123",
        )
        cls.institucional_profile = cls.institucional_user.userprofile
        cls.institucional_profile.user_type = "institucional"
        cls.institucional_profile.save()

    def test_eliminar_sede_requires_post(self):
        self.client.force_login(self.central_user)
        response = self.client.get(reverse("eliminar_sede", args=[self.regional_user.id]))
        self.assertEqual(response.status_code, 405)

    def test_institucional_cannot_delete_sede(self):
        self.client.force_login(self.institucional_user)
        response = self.client.post(reverse("eliminar_sede", args=[self.regional_user.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(id=self.regional_user.id).exists())

    def test_cannot_delete_non_regional_user(self):
        self.client.force_login(self.central_user)
        response = self.client.post(reverse("eliminar_sede", args=[self.institucional_user.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(User.objects.filter(id=self.institucional_user.id).exists())

    def test_fed_central_cannot_delete_own_account_from_sedes_screen(self):
        self.client.force_login(self.central_user)
        response = self.client.post(
            reverse("eliminar_sede", args=[self.central_user.id]),
            follow=True,
        )
        self.assertRedirects(response, reverse("gestionar_sedes"))
        self.assertTrue(User.objects.filter(id=self.central_user.id).exists())

    def test_fed_central_can_delete_regional_sede_and_audits(self):
        self.client.force_login(self.central_user)
        response = self.client.post(
            reverse("eliminar_sede", args=[self.regional_user.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse("gestionar_sedes"))
        self.assertFalse(User.objects.filter(id=self.regional_user.id).exists())
        self.assertTrue(
            LogEntry.objects.filter(
                user=self.central_user,
                object_id=str(self.regional_user.id),
            ).exists()
        )
