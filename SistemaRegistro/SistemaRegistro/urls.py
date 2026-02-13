from django.contrib import admin
from django.urls import path, include
from registry.views import cargar_municipios, cargar_parroquias

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('registry/', include('registry.urls')),
    # AJAX endpoints para el admin
    path('ajax/cargar-municipios/', cargar_municipios, name='ajax_cargar_municipios_admin'),
    path('ajax/cargar-parroquias/', cargar_parroquias, name='ajax_cargar_parroquias_admin'),
]