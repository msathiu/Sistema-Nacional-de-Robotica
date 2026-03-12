from django.urls import path
from django.views.generic import RedirectView

from . import views, views_institucional, views_reportes, views_avanzadas, views_eventos, views_tutores, views_admin_eventos, views_grupos

urlpatterns = [
    path("", views.registro_publico, name="registro_publico"),
    path("success/", views.registro_success, name="registro_success"),
    path("load-municipios/", views.load_municipios, name="load_municipios"),
    path("ajax/municipios/", views.cargar_municipios, name="ajax_cargar_municipios"),
    path("ajax/parroquias/", views.cargar_parroquias, name="ajax_cargar_parroquias"),
    # Gestión de Grupos/Equipos
    path("grupos/", views_grupos.mis_grupos, name="mis_grupos"),
    path("grupos/crear/", views_grupos.crear_equipo, name="crear_grupo"),
    path("grupos/<int:grupo_id>/", views_grupos.ver_equipo, name="ver_grupo"),
    path(
        "grupos/<int:grupo_id>/editar/",
        views_grupos.editar_equipo,
        name="editar_grupo",
    ),
    path(
        "grupos/<int:grupo_id>/eliminar/",
        views_grupos.eliminar_equipo,
        name="eliminar_grupo",
    ),
    # APIs para búsqueda de tutor y participantes
    path(
        "api/buscar-tutor/",
        views_grupos.api_buscar_tutor,
        name="api_buscar_tutor",
    ),
    path(
        "api/buscar-participante-equipo/",
        views_grupos.api_buscar_participante_equipo,
        name="api_buscar_participante_equipo",
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
    # Clubes - Vistas para instituciones
    path("clubes/", views_institucional.clubes_lista, name="clubes_lista"),
    path("clubes/directorio/", views_institucional.directorio_clubes_aprobados, name="directorio_clubes_aprobados"),
    path("clubes/<int:club_id>/detalle/", views_institucional.detalle_club, name="detalle_club"),
    path("clubes/crear/", views_institucional.crear_club, name="crear_club"),
    path(
        "clubes/<int:club_id>/editar/",
        views_institucional.editar_club,
        name="editar_club",
    ),
    path(
        "clubes/<int:club_id>/enviar-revision/",
        views_institucional.enviar_club_revision,
        name="enviar_club_revision",
    ),
    path(
        "clubes/<int:club_id>/postular/",
        views_institucional.postular_club,
        name="postular_club",
    ),
    path(
        "clubes/<int:club_id>/eliminar/",
        views_institucional.eliminar_club,
        name="eliminar_club",
    ),
    # Clubes - Vistas Admin/Federación para revisar clubes
    path(
        "admin/clubes/revisar/",
        views_institucional.revisar_clubes,
        name="revisar_clubes",
    ),
    path(
        "admin/clubes/<int:club_id>/aprobar/",
        views_institucional.aprobar_club,
        name="aprobar_club",
    ),
    path(
        "admin/clubes/<int:club_id>/rechazar/",
        views_institucional.rechazar_club,
        name="rechazar_club",
    ),
    path(
        "admin/clubes/<int:club_id>/tomar-revision/",
        views_institucional.tomar_en_revision_club,
        name="tomar_en_revision_club",
    ),
    path(
        "admin/clubes/solicitudes-eliminacion/",
        views_institucional.revisar_solicitudes_eliminacion,
        name="revisar_solicitudes_eliminacion",
    ),
    path(
        "admin/clubes/solicitudes-eliminacion/<int:solicitud_id>/aprobar/",
        views_institucional.aprobar_eliminacion_club,
        name="aprobar_eliminacion_club",
    ),
    path(
        "admin/clubes/solicitudes-eliminacion/<int:solicitud_id>/rechazar/",
        views_institucional.rechazar_eliminacion_club,
        name="rechazar_eliminacion_club",
    ),
    # Membresías - Vistas Admin/Federación para revisar membresías
    path(
        "admin/membresias/revisar/",
        views_institucional.revisar_membresias,
        name="revisar_membresias",
    ),
    path(
        "admin/membresias/<int:membresia_id>/aprobar/",
        views_institucional.aprobar_membresia,
        name="aprobar_membresia",
    ),
    path(
        "admin/membresias/<int:membresia_id>/rechazar/",
        views_institucional.rechazar_membresia,
        name="rechazar_membresia",
    ),
    # Notificaciones
    path(
        "notificaciones/",
        views_institucional.mis_notificaciones,
        name="mis_notificaciones",
    ),
    path(
        "notificaciones/<int:notificacion_id>/marcar-leida/",
        views_institucional.marcar_notificacion_leida,
        name="marcar_notificacion_leida",
    ),
    path(
        "notificaciones/marcar-todas-leidas/",
        views_institucional.marcar_todas_leidas,
        name="marcar_todas_leidas",
    ),
    # Historial y Comentarios
    path(
        "clubes/<int:club_id>/historial/",
        views_institucional.ver_historial_club,
        name="ver_historial_club",
    ),
    path(
        "clubes/<int:club_id>/comentarios/",
        views_institucional.ver_comentarios_club,
        name="ver_comentarios_club",
    ),
    path(
        "clubes/<int:club_id>/comentarios/agregar/",
        views_institucional.agregar_comentario_club,
        name="agregar_comentario_club",
    ),
    # Gestión de Membresías - Instituciones
    path(
        "clubes/<int:club_id>/membresias/gestionar/",
        views_institucional.gestionar_membresias_club,
        name="gestionar_membresias_club",
    ),
    path(
        "membresias/mis-clubes/",
        views_institucional.mis_membresias,
        name="mis_membresias",
    ),
    path(
        "membresias/<int:membresia_id>/detalle/",
        views_institucional.detalle_membresia,
        name="detalle_membresia",
    ),
    path(
        "membresias/<int:membresia_id>/aprobar/",
        views_institucional.aprobar_membresia_club,
        name="aprobar_membresia_club",
    ),
    path(
        "membresias/<int:membresia_id>/rechazar/",
        views_institucional.rechazar_membresia_club,
        name="rechazar_membresia_club",
    ),
    path(
        "membresias/<int:membresia_id>/salir/",
        views_institucional.salir_club,
        name="salir_club",
    ),
    # Búsqueda y Reportes
    path(
        "clubes/buscar/",
        views_reportes.buscar_clubes,
        name="buscar_clubes",
    ),
    path(
        "admin/clubes/dashboard-metricas/",
        views_reportes.dashboard_metricas_clubes,
        name="dashboard_metricas_clubes",
    ),
    path(
        "admin/clubes/exportar/csv/",
        views_reportes.exportar_clubes_csv,
        name="exportar_clubes_csv",
    ),
    path(
        "admin/clubes/exportar/json/",
        views_reportes.exportar_clubes_json,
        name="exportar_clubes_json",
    ),
    # Fase 4: Calificaciones
    path(
        "clubes/<int:club_id>/calificar/",
        views_avanzadas.calificar_club,
        name="calificar_club",
    ),
    # Fase 4: Vinculación con Eventos
    path(
        "clubes/<int:club_id>/vincular-evento/",
        views_avanzadas.vincular_club_evento,
        name="vincular_club_evento",
    ),
    path(
        "clubes/eventos/<int:vinculacion_id>/desvincular/",
        views_avanzadas.desvincular_club_evento,
        name="desvincular_club_evento",
    ),
    # Fase 4: Restauración de Clubes
    path(
        "admin/clubes/eliminados/",
        views_avanzadas.clubes_eliminados,
        name="clubes_eliminados",
    ),
    path(
        "admin/clubes/<int:club_id>/restaurar/",
        views_avanzadas.restaurar_club,
        name="restaurar_club",
    ),
    path(
        "admin/clubes/<int:club_id>/eliminar-permanente/",
        views_avanzadas.eliminar_permanente_club,
        name="eliminar_permanente_club",
    ),
    # API
    path(
        "api/buscar-participante/",
        views_institucional.buscar_participante,
        name="buscar_participante",
    ),
    # Eventos de Club
    path(
        "clubes/<int:club_id>/eventos/",
        views_eventos.listar_eventos_club,
        name="eventos_club",
    ),
    path(
        "clubes/<int:club_id>/eventos/crear/",
        views_eventos.crear_evento_club,
        name="crear_evento_club",
    ),
    path(
        "eventos-club/<int:evento_id>/detalle/",
        views_eventos.detalle_evento_club,
        name="detalle_evento_club",
    ),
    path(
        "eventos-club/<int:evento_id>/enviar-revision/",
        views_eventos.enviar_evento_revision,
        name="enviar_evento_revision",
    ),
    path(
        "eventos-club/<int:evento_id>/inscribir-grupo/",
        views_eventos.inscribir_grupo_evento_club,
        name="inscribir_grupo_evento_club",
    ),
    # Eventos - Admin/Federación (Vista Unificada)
    path(
        "admin/eventos/todos/",
        views_admin_eventos.admin_todos_eventos,
        name="admin_todos_eventos",
    ),
    path(
        "admin/eventos/<int:evento_id>/aprobar/",
        views_admin_eventos.aprobar_evento,
        name="aprobar_evento",
    ),
    path(
        "admin/eventos/<int:evento_id>/rechazar/",
        views_admin_eventos.rechazar_evento,
        name="rechazar_evento",
    ),
    # Gestión de Tutores
    path(
        "tutores/",
        views_tutores.lista_tutores,
        name="lista_tutores",
    ),
    path(
        "tutores/verificar-cedula/",
        views_tutores.verificar_tutor_cedula,
        name="verificar_tutor_cedula",
    ),
    path(
        "tutores/crear/",
        views_tutores.crear_tutor,
        name="crear_tutor",
    ),
    path(
        "tutores/<uuid:tutor_id>/",
        views_tutores.detalle_tutor,
        name="detalle_tutor",
    ),
    path(
        "tutores/<uuid:tutor_id>/editar/",
        views_tutores.editar_tutor,
        name="editar_tutor",
    ),
    path(
        "tutores/<uuid:tutor_id>/cambiar-estado/",
        views_tutores.cambiar_estado_tutor,
        name="cambiar_estado_tutor",
    ),
    path(
        "grupos/<int:grupo_id>/asignar-tutor/",
        views_tutores.asignar_tutor_grupo,
        name="asignar_tutor_grupo",
    ),
    path(
        "grupos/<int:grupo_id>/remover-tutor/<uuid:tutor_id>/",
        views_tutores.remover_tutor_grupo,
        name="remover_tutor_grupo",
    ),
]
