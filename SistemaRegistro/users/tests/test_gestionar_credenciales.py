from django.contrib.auth.models import User
from django.test import TestCase

from users.forms import InstitucionCredentialAdminForm


class InstitucionCredentialAdminFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.target_user = User.objects.create_user(
            username="institucion-user",
            email="inst@example.com",
            password="Original123!",
        )

    def test_rejects_mismatched_password_confirmation(self):
        form = InstitucionCredentialAdminForm(
            data={
                "password": "NuevaClave123!",
                "confirm_password": "Distinta123!",
            },
            target_user=self.target_user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("confirm_password", form.errors)

    def test_rejects_weak_password_using_django_validators(self):
        form = InstitucionCredentialAdminForm(
            data={
                "password": "debil",
                "confirm_password": "debil",
            },
            target_user=self.target_user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_accepts_strong_password(self):
        form = InstitucionCredentialAdminForm(
            data={
                "password": "NuevaClave123!",
                "confirm_password": "NuevaClave123!",
            },
            target_user=self.target_user,
        )

        self.assertTrue(form.is_valid(), msg=form.errors)
