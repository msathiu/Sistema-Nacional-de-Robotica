from django.urls import path

from . import views

urlpatterns = [
    path("", views.registro_publico, name="registro_publico"),
    path("success/", views.registro_success, name="registro_success"),
    path("load-municipios/", views.load_municipios, name="load_municipios"),
    path("ajax/municipios/", views.cargar_municipios, name="ajax_cargar_municipios"),
    path("ajax/parroquias/", views.cargar_parroquias, name="ajax_cargar_parroquias"),
]
