from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.dashboard, name='dashboard_admin'),
    path('dashboard/institucion/', views.dashboard, name='dashboard_institucion'),
    path('participante/dashboard/', views.dashboard_participante, name='dashboard_participante'),
    path('institucion/dashboard/', views.dashboard_institucional, name='dashboard_institucional'),
    path('dashboard/analitica/', views.estadisticas_demografia, name='estadisticas_por_estado'),
    path('dashboard/mapa/', views.mapa_interactivo, name='mapa_interactivo'),
    path('exportar/excel/', views.exportar_participantes_excel, name='exportar_participantes_excel'),
    path('sistema/logs/', views.ver_logs_sistema, name='ver_logs_sistema'),
    
    # Instituciones
    path('instituciones/', views.lista_instituciones, name='lista_instituciones'),
    path('instituciones/registrar/', views.registrar_institucion, name='registrar_institucion'),
    path('instituciones/<int:institucion_id>/crear-usuario/', views.crear_usuario_institucional, name='crear_usuario_institucional'),
    path('instituciones/aprobar/<int:institucion_id>/', views.aprobar_institucion, name='aprobar_institucion'),
    path('instituciones/desactivar/<int:institucion_id>/', views.desactivar_institucion, name='desactivar_institucion'),
    path('instituciones/editar/<int:institucion_id>/', views.editar_institucion_modal, name='editar_institucion_modal'),
    path('instituciones/eliminar/<int:institucion_id>/', views.eliminar_institucion, name='eliminar_institucion'),
    
    # Participantes
    path('participante/editar/<int:pk>/', views.ParticipanteUpdateView.as_view(), name='participante_editar'),
    path('participantes/', views.lista_participantes, name='lista_participantes'),

    # Estadísticas
    path("estadisticas/", views.estadisticas_por_estado, name="estadisticas_por_estado"),

    # Eventos
    path("institucion/eventos/crear/", views.crear_evento, name="crear_evento"),
    path('eventos/', views.eventos_disponibles, name='eventos_disponibles'),
    path('eventos/disponibles/', views.eventos_disponibles, name='eventos_disponibles'),
    path('eventos/<int:evento_id>/inscribirse/', views.inscripcion_evento_url, name='inscribirse_evento'),

    # Gestión de Eventos (Específicos para Institución)
    path('institucion/gestionar-eventos/', views.gestionar_eventos_institucion, name='gestionar_eventos_inst'),
    path('institucion/eventos/<int:evento_id>/detalle/', views.detalle_evento_institucion, name='detalle_evento_gestion'),

    # Grupo
    path('grupos/agregar/', views.agregar_grupo, name='agregar_grupo'),

    path('mis-grupos/', views.mis_grupos, name='mis_grupos'),
    path('obtener-datos-persona/', views.obtener_datos_persona, name='obtener_datos_persona'),


    # Otros
    path('buscar-usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
    path('create-institutional-user/', views.create_institutional_user, name='create_institutional_user'),
    path('ajax/municipios/', views.ajax_municipios, name='ajax_municipios'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    path('institucion/perfil/', views.mi_perfil_institucional, name='mi_perfil'),
    path('registrar-club/', views.registrar_club, name='registrar_club'),
]
