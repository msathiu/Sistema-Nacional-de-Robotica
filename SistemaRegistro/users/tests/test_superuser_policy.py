from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from users.context_processors import sidebar_menu
from users.decorators import fed_central_required
from users.selectors import JurisdictionSelector


class SuperuserPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="testpass123",
            email="admin@example.com",
        )
        cls.superuser.userprofile.user_type = "superuser"
        cls.superuser.userprofile.save()

        cls.fed_central = User.objects.create_user(
            username="central",
            password="testpass123",
            email="central@example.com",
        )
        cls.fed_central.userprofile.user_type = "fed_central"
        cls.fed_central.userprofile.save()

    def _build_request(self, user, path="/instituciones/"):
        request = self.factory.get(path)
        request.user = user
        request.session = self.client.session
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def test_superuser_is_not_considered_rector_in_shared_selector(self):
        self.assertFalse(JurisdictionSelector.es_rector(self.superuser.userprofile))
        self.assertFalse(JurisdictionSelector.es_federacion(self.superuser.userprofile))

    def test_fed_central_is_still_considered_rector(self):
        self.assertTrue(JurisdictionSelector.es_rector(self.fed_central.userprofile))
        self.assertTrue(JurisdictionSelector.es_federacion(self.fed_central.userprofile))

    def test_fed_central_required_blocks_superuser(self):
        @fed_central_required
        def protected_view(request):
            return HttpResponse("ok")

        response = protected_view(self._build_request(self.superuser))
        self.assertEqual(response.status_code, 302)

    def test_sidebar_menu_does_not_expose_central_menu_to_superuser(self):
        request = self._build_request(self.superuser)
        request.resolver_match = None

        context = sidebar_menu(request)

        self.assertEqual(context["sidebar_header_title"], "Panel Institucional")

    def test_dashboard_redirects_superuser_to_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
