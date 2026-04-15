from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from registry.views import cargar_municipios, cargar_parroquias
from users.admin_views import admin_dashboard
from registry.admin_logs import ver_logs_sistema

# Personalizar títulos del admin
admin.site.site_header = "SNR - Sistema Nacional de Robótica"
admin.site.site_title = "SNR Admin"
admin.site.index_title = "Panel de Administración"

urlpatterns = [
    path(
        "favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)
    ),
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/logs/", ver_logs_sistema, name="admin_logs"),
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("registry/", include("registry.urls")),
    path(
        "ajax/cargar-municipios/",
        login_required(cargar_municipios),
        name="ajax_cargar_municipios_admin",
    ),
    path(
        "ajax/cargar-parroquias/",
        login_required(cargar_parroquias),
        name="ajax_cargar_parroquias_admin",
    ),
]
