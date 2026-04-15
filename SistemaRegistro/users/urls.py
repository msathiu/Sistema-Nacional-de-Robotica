from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    # --- Autenticación y Home ---
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.custom_login, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    # --- Gestión de Contraseñas (CORRIGE EL ERROR NoReverseMatch) ---
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="users/password_change.html", success_url="/perfil/"
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # --- Dashboards (Accesos Principales) ---
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "participante/dashboard/",
        views.dashboard_participante,
        name="dashboard_participante",
    ),
    path(
        "institucion/dashboard/",
        views.dashboard_institucional,
        name="dashboard_institucional",
    ),
    # --- Gestión de Instituciones (Padrón Nacional) ---
    path("instituciones/", views.lista_instituciones, name="lista_instituciones"),
    path(
        "instituciones/registrar/",
        views.registrar_institucion,
        name="registrar_institucion",
    ),
    path(
        "instituciones/<int:institucion_id>/crear-usuario/",
        views.crear_usuario_institucional,
        name="crear_usuario_institucional",
    ),
    path(
        "instituciones/aprobar/<int:institucion_id>/",
        views.aprobar_institucion,
        name="aprobar_institucion",
    ),
    path(
        "instituciones/desactivar/<int:institucion_id>/",
        views.desactivar_institucion,
        name="desactivar_institucion",
    ),
    path(
        "instituciones/editar/<int:institucion_id>/",
        views.editar_institucion_modal,
        name="editar_institucion_modal",
    ),
    path(
        "instituciones/eliminar/<int:institucion_id>/",
        views.eliminar_institucion,
        name="eliminar_institucion",
    ),
    path(
        "instituciones/detalle/<int:institucion_id>/",
        views.detalle_institucion_api,
        name="detalle_institucion_api",
    ),
    # --- Participantes ---
    path("participantes/", views.lista_participantes, name="lista_participantes"),
    path("participantes/crear/", views.crear_participante, name="crear_participante"),
    path(
        "verificar-participante/",
        views.verificar_participante_duplicado,
        name="verificar_participante_duplicado",
    ),
    path(
        "participantes/vincular/",
        views.vincular_participante_existente,
        name="vincular_participante_existente",
    ),
    path(
        "participante/<uuid:pk>/", views.participante_detail, name="participante_detail"
    ),
    path(
        "participante/editar/<uuid:pk>/",
        views.participante_edit,
        name="participante_edit",
    ),
    path(
        "participantes/<uuid:pk>/editar/",
        views.editar_participante,
        name="editar_participante",
    ),
    path(
        "participante/eliminar/<uuid:pk>/",
        views.participante_delete,
        name="participante_delete",
    ),
    path(
        "participantes/<uuid:pk>/cambiar-estado/",
        views.cambiar_estado_participante,
        name="cambiar_estado_participante",
    ),
    path(
        "api/participante/<str:cedula>/",
        views.api_buscar_participante,
        name="api_buscar_participante",
    ),
    # --- Analítica y Reportes ---
    path(
        "dashboard/analitica/",
        views.estadisticas_por_estado,
        name="estadisticas_por_estado",
    ),
    path("dashboard/mapa/", views.mapa_interactivo, name="mapa_interactivo"),
    path("api/mapa/datos/", views.api_mapa_datos, name="api_mapa_datos"),
    path("api/mapa/resumen/", views.api_mapa_resumen, name="api_mapa_resumen"),
    path(
        "exportar/participantes/",
        views.exportar_participantes_excel,
        name="exportar_participantes_excel",
    ),
    path(
        "exportar/excel/",
        RedirectView.as_view(
            pattern_name="exportar_participantes_excel", permanent=False
        ),
    ),
    path("sistema/logs/", views.ver_logs_sistema, name="ver_logs_sistema"),
    # --- Gestión de Eventos (Módulo Eventos 2026) ---
    path("eventos/", views.eventos_disponibles, name="eventos_disponibles"),
    path(
        "eventos/mis-eventos/",
        views.seguimiento_eventos_institucion,
        name="mis_eventos",
    ),
    path(
        "eventos/administracion/",
        views.gestionar_eventos_institucion,
        name="admin_eventos",
    ),
    path("eventos/crear/", views.crear_evento, name="crear_evento"),
    path(
        "eventos/enviar-revision/<int:evento_id>/",
        views.enviar_evento_revision,
        name="enviar_evento_revision",
    ),
    path(
        "eventos/<int:evento_id>/detalle/",
        views.detalle_evento,
        name="detalle_evento",
    ),
    path(
        "eventos/<int:evento_id>/detalle-gestion/",
        views.detalle_evento_gestion,
        name="detalle_evento_gestion_admin",
    ),
    path(
        "eventos/<int:evento_id>/detalle-institucion/",
        views.detalle_evento_institucion,
        name="detalle_evento_gestion",
    ),
    path(
        "eventos/inscribir/<int:evento_id>/",
        views.inscribir_grupo_evento,
        name="inscribir_grupo_evento",
    ),
    path(
        "eventos/cancelar-inscripcion/<int:inscripcion_id>/",
        views.cancelar_inscripcion_grupo,
        name="cancelar_inscripcion_grupo",
    ),
    path(
        "eventos/cancelar-inscripcion-admin/<int:inscripcion_id>/",
        views.cancelar_inscripcion_grupo_admin,
        name="cancelar_inscripcion_grupo_admin",
    ),
    path("eventos/editar/<int:evento_id>/", views.editar_evento, name="editar_evento"),
    path("eventos/<int:evento_id>/asistencia/",   views.registro_asistencia,  name="registro_asistencia"),
    path(
        "eventos/cambiar-estado/<int:evento_id>/",
        views.cambiar_estado_evento,
        name="cambiar_estado_evento",
    ),
    path(
        "eventos/gestionar-estado/<int:evento_id>/",
        views.gestionar_estado_evento,
        name="gestionar_estado_evento",
    ),
    path(
        "eventos/<int:evento_id>/aprobar/",
        views.aprobar_evento,
        name="aprobar_evento",
    ),
    path(
        "eventos/<int:evento_id>/rechazar/",
        views.rechazar_evento,
        name="rechazar_evento",
    ),
    path(
        "eventos/cancelar/<int:evento_id>/",
        views.cancelar_evento,
        name="cancelar_evento",
    ),
    path(
        "eventos/eliminar/<int:evento_id>/",
        views.eliminar_evento,
        name="eliminar_evento",
    ),
    path(
        "eventos/<int:evento_id>/inscribirse/",
        views.inscripcion_evento_url,
        name="inscribirse_evento",
    ),
    # --- Grupos y Clubes ---
    path("grupos/agregar/", views.agregar_grupo, name="agregar_grupo"),
    path("mis-grupos/", views.mis_grupos, name="mis_grupos"),
    path("registrar-club/", views.registrar_club, name="registrar_club"),
    path(
        "obtener-datos-persona/",
        views.obtener_datos_persona,
        name="obtener_datos_persona",
    ),
    # --- Perfil y Utilidades ---
    path("perfil/", views.mi_perfil, name="mi_perfil"),
    path(
        "perfil/configuracion/", views.mi_perfil_federacion, name="mi_perfil_federacion"
    ),
    path(
        "institucion/perfil/",
        views.mi_perfil_institucional,
        name="mi_perfil_institucional",
    ),
    # AJAX y Datos Dinámicos
    path("ajax/municipios/", views.ajax_municipios, name="ajax_municipios"),
    path("ajax/dependencias/", views.ajax_dependencias, name="ajax_dependencias"),
    path("ajax/parroquias/", views.ajax_parroquias, name="ajax_parroquias"),
    path("buscar-usuarios/", views.buscar_usuarios, name="buscar_usuarios"),
    path(
        "create-institutional-user/",
        views.create_institutional_user,
        name="create_institutional_user",
    ),
    # --- Gestión de Sedes (Administradores Regionales) ---
    path("sedes/registrar/", views.registrar_sede, name="registrar_sede"),
    path("sedes/nueva/", views.registrar_sede, name="registrar_sede_fvrn"),
    path("sedes/gestionar/", views.gestionar_usuarios_sedes, name="gestionar_sedes"),
    path("sedes/editar/<int:user_id>/", views.editar_sede_regional, name="editar_sede_regional"),
    path("sedes/eliminar/<int:user_id>/", views.eliminar_sede, name="eliminar_sede"),
    path(
        "eventos/<int:evento_id>/detalle-inscripcion/",
        views.detalle_evento_inscripcion,
        name="detalle_evento_inscripcion",
    ),
    # API endpoints
    path(
        "api/grupos/<int:grupo_id>/participantes/",
        views.api_participantes_grupo,
        name="api_participantes_grupo",
    ),
    path(
        "api/form-config/<str:tipo>/",
        views.form_config_api,
        name="form_config_api",
    ),
    # --- HTMX endpoints ---
    path("htmx/toggle-submenu/", views.toggle_submenu, name="toggle_submenu"),
]
