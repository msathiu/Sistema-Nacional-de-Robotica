"""
Context processors para el layout del dashboard.
Genera la estructura del menú del sidebar según el rol del usuario.
El estado de submenús se determina por la URL activa o la sesión.
"""


def sidebar_menu(request):
    """
    Genera la estructura del menú del sidebar según el tipo de usuario.
    Los submenús se expanden automáticamente si contienen la página activa.
    """
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {"sidebar_menu": [], "sidebar_header_title": ""}

    user = request.user
    perfil = getattr(user, "userprofile", None)
    if not perfil:
        return {"sidebar_menu": [], "sidebar_header_title": ""}

    user_type = getattr(perfil, "user_type", "")
    url_name = ""
    if hasattr(request, "resolver_match") and request.resolver_match:
        url_name = request.resolver_match.url_name or ""

    # Submenús que el usuario expandió manualmente (persistidos en sesión)
    expanded_submenus = request.session.get("expanded_submenus", [])

    def _is_active(*names):
        return "active" if url_name in names else ""

    def _is_expanded(label, items):
        """Un submenu está expandido si contiene la página activa o fue expandido manualmente."""
        slug = _slugify(label)
        # Si algún hijo está activo, expandir automáticamente
        if any(item.get("active") for item in items):
            return True
        # Si el usuario lo expandió manualmente
        return slug in expanded_submenus

    def _slugify(label):
        """Genera un slug simple para el label del submenu."""
        return label.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    es_central = user_type == "fed_central"
    es_regional = user_type == "fed_regional"

    if es_central:
        menu = _menu_central(_is_active, _is_expanded)
        header_title = "Administración Central"
        rol_label = "SUPERADMIN"
        perfil_url = "mi_perfil_federacion"
    elif es_regional:
        menu = _menu_regional(_is_active, _is_expanded)
        header_title = f"Sede Regional: {perfil.estado.nombre}" if getattr(perfil, "estado", None) else "Sede Regional"
        rol_label = "AUDITOR"
        perfil_url = "mi_perfil_federacion"
    else:
        menu = _menu_institucional(_is_active, _is_expanded, request)
        header_title = "Panel Institucional"
        rol_label = "INSTITUCIÓN"
        perfil_url = "mi_perfil_institucional"

    return {
        "sidebar_menu": menu,
        "sidebar_header_title": header_title,
        "sidebar_rol_label": rol_label,
        "sidebar_perfil_url": perfil_url,
    }


def _menu_central(is_active, is_expanded, request=None):
    """Menú para Federación Central."""
    from django.core.cache import cache
    from registry.models import Club
    cache_key = 'clubes_pendientes_count'
    pendientes = cache.get(cache_key)
    if pendientes is None:
        pendientes = Club.objects.filter(status='pendiente', eliminado=False).count()
        cache.set(cache_key, pendientes, 300)

    submenus = [
        ("Administración", "bi-gear", [
            ("Instituciones", "lista_instituciones", "bi-building", None),
            ("Gestionar Sedes", "gestionar_sedes", "bi-shield-lock", None),
        ]),
        ("Gestión Académica", "bi-book", [
            ("Participantes", "lista_participantes", "bi-people", None),
            ("Tutores", "lista_tutores", "bi-person-workspace", None),
            ("Equipos", "mis_grupos", "bi-microsoft-teams", None),
        ]),
        ("Gestión de Clubes", "bi-robot", [
            ("Mis Clubes", "clubes_lista", "bi-folder2-open", None),
            ("Clubes Aprobados", "directorio_clubes_aprobados", "bi-check-circle", None),
            ("Revisar Pendientes", "revisar_clubes", "bi-hourglass-split", pendientes or None),
            ("Membresías", "revisar_membresias", "bi-person-check", None),
            ("Métricas", "dashboard_metricas_clubes", "bi-graph-up", None),
            ("Solicitudes Eliminación", "revisar_solicitudes_eliminacion", "bi-trash3-fill", None),
            ("Papelera", "clubes_eliminados", "bi-trash3", None),
        ]),
    ]
    menu = [{"label": "Inicio", "url_name": "dashboard", "icon": "bi-speedometer2", "active": is_active("dashboard")}]
    for label, icon, children in submenus:
        items = [{"label": c[0], "url_name": c[1], "icon": c[2], "active": is_active(c[1]), "badge": c[3]} for c in children]
        menu.append({"label": label, "icon": icon, "type": "submenu", "items": items, "expanded": is_expanded(label, items)})
    menu.append({"label": "Eventos y Actividades", "url_name": "admin_eventos", "icon": "bi-calendar-event", "active": is_active("admin_eventos", "admin_todos_eventos")})
    # Submenu Reportes (federación central)
    reportes_items = [
        {"label": "Participantes",   "url_name": "exportar_participantes_excel",  "icon": "bi-people",            "active": is_active("exportar_participantes_excel")},
        {"label": "Equipos",         "url_name": "exportar_equipos_excel",         "icon": "bi-microsoft-teams",   "active": is_active("exportar_equipos_excel")},
        {"label": "Tutores",         "url_name": "exportar_tutores_excel",         "icon": "bi-person-workspace",  "active": is_active("exportar_tutores_excel")},
        {"label": "Instituciones",   "url_name": "exportar_instituciones_excel",   "icon": "bi-building",          "active": is_active("exportar_instituciones_excel")},
        {"label": "Inscripciones",   "url_name": "exportar_inscripciones_excel",   "icon": "bi-calendar-check",    "active": is_active("exportar_inscripciones_excel")},
    ]
    menu.append({"label": "Reportes", "icon": "bi-file-earmark-spreadsheet", "type": "submenu", "items": reportes_items, "expanded": is_expanded("Reportes", reportes_items)})
    return menu


def _menu_regional(is_active, is_expanded):
    """Menú para Federación Regional (solo visualización)."""
    reportes_items = [
        {"label": "Participantes",  "url_name": "exportar_participantes_excel", "icon": "bi-people",           "active": is_active("exportar_participantes_excel")},
        {"label": "Equipos",        "url_name": "exportar_equipos_excel",        "icon": "bi-microsoft-teams",  "active": is_active("exportar_equipos_excel")},
        {"label": "Tutores",        "url_name": "exportar_tutores_excel",        "icon": "bi-person-workspace", "active": is_active("exportar_tutores_excel")},
        {"label": "Instituciones",  "url_name": "exportar_instituciones_excel",  "icon": "bi-building",         "active": is_active("exportar_instituciones_excel")},
        {"label": "Inscripciones",  "url_name": "exportar_inscripciones_excel",  "icon": "bi-calendar-check",   "active": is_active("exportar_inscripciones_excel")},
    ]
    return [
        {"label": "Inicio",        "url_name": "dashboard",                  "icon": "bi-speedometer2", "active": is_active("dashboard")},
        {"label": "Instituciones", "url_name": "lista_instituciones",        "icon": "bi-building",     "active": is_active("lista_instituciones")},
        {"label": "Participantes", "url_name": "lista_participantes",        "icon": "bi-people",       "active": is_active("lista_participantes")},
        {"label": "Métricas",      "url_name": "dashboard_metricas_clubes",  "icon": "bi-graph-up",     "active": is_active("dashboard_metricas_clubes")},
        {"label": "Reportes", "icon": "bi-file-earmark-spreadsheet", "type": "submenu", "items": reportes_items, "expanded": is_expanded("Reportes", reportes_items)},
    ]


def _menu_institucional(is_active, is_expanded, request=None):
    """Menú para Usuarios Institucionales."""
    submenus = [
        ("Gestión Académica", "bi-book", [
            ("Participantes", "lista_participantes", "bi-people"),
            ("Tutores", "lista_tutores", "bi-person-workspace"),
            ("Equipos", "mis_grupos", "bi-microsoft-teams"),
        ]),
        ("Gestión de Clubes", "bi-robot", [
            ("Mis Clubes", "clubes_lista", "bi-folder2-open"),
            ("Membresías", "mis_membresias", "bi-star"),
            ("Directorio", "directorio_clubes_aprobados", "bi-book"),
            ("Buscar", "buscar_clubes", "bi-search"),
        ]),
        ("Eventos y Actividades", "bi-calendar-event", [
            ("Eventos", "eventos_disponibles", "bi-calendar-event"),
            ("Mis Eventos", "mis_eventos", "bi-clipboard-check"),
        ]),
    ]
    menu = [{"label": "Inicio", "url_name": "dashboard", "icon": "bi-house-door", "active": is_active("dashboard")}]
    for label, icon, children in submenus:
        items = [{"label": c[0], "url_name": c[1], "icon": c[2], "active": is_active(c[1])} for c in children]
        menu.append({"label": label, "icon": icon, "type": "submenu", "items": items, "expanded": is_expanded(label, items)})
    notif_count = 0
    if request and request.user.is_authenticated:
        notif_count = request.user.notificaciones.filter(leida=False).count()
    menu.append({"label": "Notificaciones", "url_name": "mis_notificaciones", "icon": "bi-bell", "active": is_active("mis_notificaciones"), "badge": notif_count or None})
    # Reportes institucionales
    reportes_inst = [
        {"label": "Participantes",  "url_name": "exportar_participantes_excel", "icon": "bi-people",          "active": is_active("exportar_participantes_excel")},
        {"label": "Equipos",        "url_name": "exportar_equipos_excel",        "icon": "bi-microsoft-teams", "active": is_active("exportar_equipos_excel")},
        {"label": "Inscripciones",  "url_name": "exportar_inscripciones_excel",  "icon": "bi-calendar-check",  "active": is_active("exportar_inscripciones_excel")},
    ]
    menu.append({"label": "Reportes", "icon": "bi-file-earmark-spreadsheet", "type": "submenu", "items": reportes_inst, "expanded": is_expanded("Reportes", reportes_inst)})
    return menu
