from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Autenticación y Home ---
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # --- Gestión de Contraseñas (CORRIGE EL ERROR NoReverseMatch) ---
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url='/perfil/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),

    # --- Dashboards (Accesos Principales) ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('participante/dashboard/', views.dashboard_participante, name='dashboard_participante'),
    path('institucion/dashboard/', views.dashboard_institucional, name='dashboard_institucional'),
    
    # --- Gestión de Instituciones (Padrón Nacional) ---
    path('instituciones/', views.lista_instituciones, name='lista_instituciones'),
    path('instituciones/registrar/', views.registrar_institucion, name='registrar_institucion'),
    path('instituciones/<int:institucion_id>/crear-usuario/', views.crear_usuario_institucional, name='crear_usuario_institucional'),
    path('instituciones/aprobar/<int:institucion_id>/', views.aprobar_institucion, name='aprobar_institucion'),
    path('instituciones/desactivar/<int:institucion_id>/', views.desactivar_institucion, name='desactivar_institucion'),
    path('instituciones/editar/<int:institucion_id>/', views.editar_institucion_modal, name='editar_institucion_modal'),
    path('instituciones/eliminar/<int:institucion_id>/', views.eliminar_institucion, name='eliminar_institucion'),
    
    # --- Participantes ---
    path('participantes/', views.lista_participantes, name='lista_participantes'),
    path('participante/<int:pk>/', views.participante_detail, name='participante_detail'),
    path('participante/editar/<int:pk>/', views.participante_edit, name='participante_edit'),
    path('participante/eliminar/<int:pk>/', views.participante_delete, name='participante_delete'),
    path('api/participante/<str:cedula>/', views.api_buscar_participante, name='api_buscar_participante'),

    # --- Analítica y Reportes ---
    path('dashboard/analitica/', views.estadisticas_por_estado, name='estadisticas_por_estado'),
    path('dashboard/mapa/', views.mapa_interactivo, name='mapa_interactivo'),
    path('exportar/excel/', views.exportar_participantes_excel, name='exportar_participantes_excel'),
    path('sistema/logs/', views.ver_logs_sistema, name='ver_logs_sistema'),

    # --- Gestión de Eventos ---
    path('eventos/', views.eventos_disponibles, name='eventos_disponibles'),
    path('eventos/<int:evento_id>/inscribirse/', views.inscripcion_evento_url, name='inscribirse_evento'),
    path('institucion/eventos/crear/', views.crear_evento, name='crear_evento'),
    path('institucion/gestionar-eventos/', views.gestionar_eventos_institucion, name='gestionar_eventos_inst'),
    path('institucion/eventos/<int:evento_id>/detalle/', views.detalle_evento_institucion, name='detalle_evento_gestion'),

    # --- Grupos y Clubes ---
    path('grupos/agregar/', views.agregar_grupo, name='agregar_grupo'),
    path('mis-grupos/', views.mis_grupos, name='mis_grupos'),
    path('registrar-club/', views.registrar_club, name='registrar_club'),
    path('obtener-datos-persona/', views.obtener_datos_persona, name='obtener_datos_persona'),

    # --- Perfil y Utilidades ---
    # La vista principal 'mi_perfil' ahora decidirá si mostrar Perfil Federación o Institución
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    path('perfil/configuracion/', views.mi_perfil_federacion, name='mi_perfil_federacion'),
    path('institucion/perfil/', views.mi_perfil_institucional, name='mi_perfil_institucional'),
    
    # AJAX y Datos Dinámicos
    path('ajax/municipios/', views.ajax_municipios, name='ajax_municipios'),
    path('ajax/dependencias/', views.ajax_dependencias, name='ajax_dependencias'),
    path('ajax/parroquias/', views.load_parroquias, name='ajax_load_parroquias'),
    path('buscar-usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
    path('create-institutional-user/', views.create_institutional_user, name='create_institutional_user'),

    # --- Gestión de Sedes (Administradores Regionales) ---
    path('sedes/registrar/', views.registrar_sede, name='registrar_sede'),
    path('sedes/nueva/', views.registrar_sede, name='registrar_sede_fvrn'), 
    path('sedes/gestionar/', views.gestionar_usuarios_sedes, name='gestionar_sedes'),
    path('sedes/eliminar/<int:user_id>/', views.eliminar_sede, name='eliminar_sede'),
]