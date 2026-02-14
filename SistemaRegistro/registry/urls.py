from django.urls import path

from . import views
from . import views_institucional

urlpatterns = [
    path("", views.registro_publico, name="registro_publico"),
    path("success/", views.registro_success, name="registro_success"),
    path("load-municipios/", views.load_municipios, name="load_municipios"),
    path("ajax/municipios/", views.cargar_municipios, name="ajax_cargar_municipios"),
    path("ajax/parroquias/", views.cargar_parroquias, name="ajax_cargar_parroquias"),
    # Gestión de Grupos
    path("grupos/", views_institucional.grupos_institucion, name="grupos_institucion"),
    path("grupos/crear/", views_institucional.crear_grupo, name="crear_grupo"),
    path("grupos/<int:grupo_id>/", views_institucional.ver_grupo, name="ver_grupo"),
    path(
        "grupos/<int:grupo_id>/editar/",
        views_institucional.editar_grupo,
        name="editar_grupo",
    ),
    path(
        "grupos/<int:grupo_id>/eliminar/",
        views_institucional.eliminar_grupo,
        name="eliminar_grupo",
    ),
    # Eventos
    path(
        "eventos/disponibles/",
        views_institucional.eventos_disponibles_institucion,
        name="eventos_disponibles_institucion",
    ),
    path(
        "eventos/<int:evento_id>/inscribir/",
        views_institucional.inscribir_grupo_evento,
        name="inscribir_grupo_evento",
    ),
    # Clubes
    path("clubes/", views_institucional.clubes_lista, name="clubes_lista"),
    path("clubes/crear/", views_institucional.crear_club, name="crear_club"),
    path(
        "clubes/<int:club_id>/postular/",
        views_institucional.postular_club,
        name="postular_club",
    ),
    # API
    path(
        "api/buscar-participante/",
        views_institucional.buscar_participante,
        name="buscar_participante",
    ),
]
