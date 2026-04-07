"""Vistas para búsqueda avanzada y reportes de clubes."""

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, DurationField
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import csv

from users.report_export_utils import parse_export_format, rows_to_response

from .models import Club, MembresiaClu, HistorialClub, Grupo, InscripcionGrupoEvento
from .models.tutor import Tutor, TutorInstitucion
from .models.institucion import Institucion


@login_required
def buscar_clubes(request):
    """Búsqueda avanzada de clubes con filtros múltiples."""
    clubes = Club.objects.filter(status='aprobado', activo=True, eliminado=False)
    
    # Filtros
    linea = request.GET.get('linea')
    estado_id = request.GET.get('estado')
    municipio_id = request.GET.get('municipio')
    estado_vinculacion = request.GET.get('estado_vinculacion')
    cupos_min = request.GET.get('cupos_min')
    busqueda = request.GET.get('q')
    
    if linea:
        # ✅ CORRECCIÓN: Filtrar a través de la relación club_lineas
        clubes = clubes.filter(club_lineas__linea_id=linea).distinct()
    
    if estado_id:
        clubes = clubes.filter(institucion_creadora__estado_id=estado_id)
    
    if municipio_id:
        clubes = clubes.filter(institucion_creadora__municipio_id=municipio_id)
    
    if estado_vinculacion:
        clubes = clubes.filter(estado_vinculacion=estado_vinculacion)
    
    if busqueda:
        clubes = clubes.filter(
            Q(nombre__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda) |
            Q(institucion_creadora__nombre__icontains=busqueda)
        )
    
    clubes = clubes.select_related(
        'institucion_creadora',
        'institucion_creadora__estado',
    ).prefetch_related(
        'club_lineas__linea',
    ).annotate(
        num_membresias=Count('membresias', filter=Q(membresias__estado='miembro_activo'))
    )
    
    if cupos_min:
        clubes = [c for c in clubes if c.cupos_disponibles >= int(cupos_min)]
    
    # ✅ CORRECCIÓN: Obtener líneas desde LineaInvestigacion
    from .models import LineaInvestigacion
    lineas_disponibles = LineaInvestigacion.objects.all().order_by('nombre')
    
    context = {
        'clubes': clubes,
        'total_resultados': len(clubes) if cupos_min else clubes.count(),
        'lineas': lineas_disponibles,  # ✅ Usar LineaInvestigacion
        'estados_vinculacion': Club.ESTADO_VINCULACION_CHOICES,
    }
    return render(request, 'registry/buscar_clubes.html', context)


@login_required
def dashboard_metricas_clubes(request):
    """Dashboard con métricas avanzadas de clubes - Federación Central y Regional."""
    # Verificar permisos
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, "No tiene permisos para acceder a esta sección.")
        return redirect('dashboard')
    
    perfil = request.user.userprofile
    es_central = perfil.user_type in ['fed_central', 'superuser', 'tecnologico']
    es_regional = perfil.user_type == 'fed_regional'
    
    if not (es_central or es_regional):
        messages.error(request, "No tiene permisos para acceder a esta sección.")
        return redirect('dashboard')
    
    # Filtrar clubes según el rol
    clubes_base = Club.objects.filter(eliminado=False)
    if es_regional and perfil.estado:
        # Federación regional solo ve clubes de su estado
        clubes_base = clubes_base.filter(institucion_creadora__estado=perfil.estado)
    
    # Métricas generales
    total_clubes = clubes_base.count()
    clubes_aprobados = clubes_base.filter(status='aprobado', activo=True).count()
    clubes_pendientes = clubes_base.filter(status='pendiente').count()
    clubes_rechazados = clubes_base.filter(status='rechazado').count()
    
    # Tasa de aprobación: aprobados / (aprobados + rechazados) dentro del scope del usuario
    total_procesados = clubes_base.filter(status__in=['aprobado', 'rechazado']).count()
    tasa_aprobacion = (clubes_aprobados / total_procesados * 100) if total_procesados > 0 else 0
    
    # Clubes por línea de investigación - ✅ CORRECCIÓN
    from .models import LineaInvestigacion
    
    clubes_por_linea = {}
    for linea_obj in LineaInvestigacion.objects.all():
        count = clubes_base.filter(
            club_lineas__linea=linea_obj,  # ✅ Usar relación correcta
            status='aprobado',
            activo=True
        ).distinct().count()
        if count > 0:
            clubes_por_linea[linea_obj.nombre] = count
    
    # Clubes por estado
    from .models import Estado
    clubes_por_estado = []
    if es_central:
        # Central ve todos los estados
        for estado in Estado.objects.all():
            count = clubes_base.filter(
                institucion_creadora__estado=estado,
                status='aprobado',
                activo=True
            ).count()
            if count > 0:
                clubes_por_estado.append({'estado': estado.nombre, 'count': count})
    else:
        # Regional solo ve su estado
        if perfil.estado:
            count = clubes_base.filter(
                status='aprobado',
                activo=True
            ).count()
            if count > 0:
                clubes_por_estado.append({'estado': perfil.estado.nombre, 'count': count})
    
    # Tiempo promedio de revisión
    ultimos_30_dias = timezone.now() - timedelta(days=30)
    clubes_aprobados_recientes = clubes_base.filter(
        status='aprobado',
        fecha_aprobacion__gte=ultimos_30_dias
    )
    
    resultado = clubes_aprobados_recientes.filter(
        fecha_aprobacion__isnull=False,
        fecha_creacion__isnull=False
    ).annotate(
        duracion=ExpressionWrapper(
            F('fecha_aprobacion') - F('fecha_creacion'),
            output_field=DurationField()
        )
    ).aggregate(promedio=Avg('duracion'))

    promedio = resultado['promedio']
    tiempo_promedio_revision = round(promedio.days, 1) if promedio else 0
    
    # Clubes más populares (más membresías)
    clubes_populares = clubes_base.filter(
        status='aprobado',
        activo=True
    ).annotate(
        num_membresias=Count('membresias', filter=Q(membresias__estado='miembro_activo'))
    ).order_by('-num_membresias')[:5]
    
    context = {
        'total_clubes': total_clubes,
        'clubes_aprobados': clubes_aprobados,
        'clubes_pendientes': clubes_pendientes,
        'clubes_rechazados': clubes_rechazados,
        'tasa_aprobacion': round(tasa_aprobacion, 1),
        'total_procesados': total_procesados,
        'clubes_por_linea': clubes_por_linea,
        'clubes_por_estado': clubes_por_estado,
        'tiempo_promedio_revision': round(tiempo_promedio_revision, 1),
        'clubes_populares': clubes_populares,
        'es_regional': es_regional,
        'es_central': es_central,
    }
    return render(request, 'registry/dashboard_metricas_clubes.html', context)


@staff_member_required
def exportar_clubes_csv(request):
    """Exporta lista de clubes a CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clubes_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Nombre', 'Siglas', 'Estado', 'Institución', 'Estado Ubicación',
        'Líneas Investigación', 'Cupo Máximo', 'Membresías Aprobadas',
        'Fecha Creación', 'Fecha Aprobación'
    ])
    
    clubes = Club.objects.filter(
        status='aprobado',
        activo=True,
        eliminado=False
    ).select_related('institucion_creadora').annotate(
        num_membresias=Count('membresias', filter=Q(membresias__estado='miembro_activo'))
    )
    
    for club in clubes:
        lineas = ', '.join([l for l in club.lineas_investigacion])
        writer.writerow([
            club.nombre,
            club.siglas or '',
            club.get_status_display(),
            club.institucion_creadora.nombre,
            club.institucion_creadora.estado.nombre,
            lineas,
            club.cupo_maximo,
            club.num_membresias,
            club.fecha_creacion.strftime('%d/%m/%Y'),
            club.fecha_aprobacion.strftime('%d/%m/%Y') if club.fecha_aprobacion else ''
        ])
    
    return response


@staff_member_required
def exportar_clubes_json(request):
    """Exporta lista de clubes a JSON para análisis."""
    clubes = Club.objects.filter(
        status='aprobado',
        activo=True,
        eliminado=False
    ).select_related('institucion_creadora').annotate(
        num_membresias=Count('membresias', filter=Q(membresias__estado='miembro_activo'))
    )
    
    data = []
    for club in clubes:
        data.append({
            'id': club.id,
            'nombre': club.nombre,
            'siglas': club.siglas or '',
            'institucion': club.institucion_creadora.nombre,
            'estado': club.institucion_creadora.estado.nombre,
            'lineas': club.lineas_investigacion,
            'cupo_maximo': club.cupo_maximo,
            'cupos_disponibles': club.cupos_disponibles,
            'membresias_aprobadas': club.num_membresias,
            'fecha_creacion': club.fecha_creacion.isoformat(),
            'fecha_aprobacion': club.fecha_aprobacion.isoformat() if club.fecha_aprobacion else None,
        })
    
    return JsonResponse({'clubes': data, 'total': len(data)})


# ─────────────────────────────────────────────
# EXPORTACIONES EXCEL (openpyxl via HttpResponse)
# ─────────────────────────────────────────────

def _es_federacion(perfil):
    return perfil.user_type in ("fed_central", "fed_regional", "superuser", "tecnologico")


def _es_institucional(perfil):
    return perfil.user_type == "institucional"


def _filtro_territorial(qs, perfil, campo_estado):
    """Aplica filtro por estado si el usuario es fed_regional."""
    if perfil.user_type == "fed_regional" and perfil.estado:
        return qs.filter(**{campo_estado: perfil.estado})
    return qs


def _report_format_or_chooser(request, title: str):
    try:
        fmt = parse_export_format(request)
    except ValueError:
        return None, HttpResponseBadRequest(
            "Formato no válido. Use format=xlsx o format=csv.",
            content_type="text/plain; charset=utf-8",
        )
    if fmt is None:
        return None, render(
            request,
            "users/report_export_format.html",
            {"report_title": title, "export_base_path": request.path},
        )
    return fmt, None


@login_required
def exportar_equipos_excel(request):
    """Exporta equipos (grupos) a Excel o CSV según permisos del usuario."""
    out = _report_format_or_chooser(request, "Exportar equipos")
    if out[1] is not None:
        return out[1]
    fmt = out[0]

    perfil = request.user.userprofile
    if not (_es_federacion(perfil) or _es_institucional(perfil)):
        messages.error(request, "No tienes permisos para exportar equipos.")
        return redirect("dashboard")

    qs = Grupo.objects.filter(activo=True).select_related(
        "institucion", "institucion__estado", "evento"
    ).prefetch_related("tutores", "participantes")

    if _es_institucional(perfil):
        qs = qs.filter(institucion=perfil.institution)
    else:
        qs = _filtro_territorial(qs, perfil, "institucion__estado")

    headers = [
        "Código", "Nombre", "Criterio", "Nivel Educativo",
        "Estado Grupo", "Institución", "Estado", "Tutores",
        "N° Participantes", "Evento Inscrito", "Fecha Registro",
    ]
    rows = []
    for g in qs:
        tutores = ", ".join(
            f"{t.nombres} {t.apellidos}" for t in g.tutores.all()
        )
        rows.append([
            g.codigo,
            g.nombre,
            g.get_criterio_display(),
            g.nivel_educativo or "",
            g.get_estado_grupo_display(),
            g.institucion.nombre if g.institucion else "",
            g.institucion.estado.nombre if g.institucion and g.institucion.estado else "",
            tutores,
            g.participantes.count(),
            g.evento.nombre if g.evento else "",
            g.fecha_registro.strftime("%d/%m/%Y") if g.fecha_registro else "",
        ])

    return rows_to_response(headers, rows, "equipos_export", fmt)


@login_required
def exportar_tutores_excel(request):
    """Exporta tutores a Excel o CSV según permisos del usuario."""
    out = _report_format_or_chooser(request, "Exportar tutores")
    if out[1] is not None:
        return out[1]
    fmt = out[0]

    perfil = request.user.userprofile
    if not (_es_federacion(perfil) or _es_institucional(perfil)):
        messages.error(request, "No tienes permisos para exportar tutores.")
        return redirect("dashboard")

    qs = TutorInstitucion.objects.select_related(
        "tutor", "institucion", "institucion__estado", "estado"
    )
    if _es_institucional(perfil):
        qs = qs.filter(institucion=perfil.institution)
    else:
        qs = _filtro_territorial(qs, perfil, "institucion__estado")

    headers = [
        "Nombres", "Apellidos", "Cédula", "Sexo", "Email",
        "Teléfono", "Profesión", "Institución", "Estado",
        "Rol", "Status Vinculación",
    ]
    rows = []
    for vi in qs:
        t = vi.tutor
        rows.append([
            t.nombres,
            t.apellidos,
            f"{t.nacionalidad}-{t.cedula}" if t.cedula else "",
            t.get_sexo_display() if t.sexo else "",
            t.email,
            f"{t.telefono_codigo}-{t.telefono}" if t.telefono else "",
            t.profesion or "",
            vi.institucion.nombre if vi.institucion else "",
            vi.institucion.estado.nombre if vi.institucion and vi.institucion.estado else "",
            vi.rol or "",
            vi.get_status_display(),
        ])

    return rows_to_response(headers, rows, "tutores_export", fmt)


@login_required
def exportar_instituciones_excel(request):
    """Exporta instituciones a Excel o CSV. Solo federación."""
    out = _report_format_or_chooser(request, "Exportar instituciones")
    if out[1] is not None:
        return out[1]
    fmt = out[0]

    perfil = request.user.userprofile
    if not _es_federacion(perfil):
        messages.error(request, "No tienes permisos para exportar instituciones.")
        return redirect("dashboard")

    qs = Institucion.objects.filter(eliminado=False).select_related(
        "estado", "municipio"
    )
    qs = _filtro_territorial(qs, perfil, "estado")

    headers = [
        "Código", "Nombre", "RIF", "Tipo", "Naturaleza",
        "Estado", "Municipio", "Email", "Teléfono",
        "Estatus", "Federado", "Fecha Registro",
    ]
    rows = []
    for inst in qs:
        rows.append([
            inst.codigo,
            inst.nombre,
            inst.rif or "",
            inst.get_tipo_institucion_display() if inst.tipo_institucion else "",
            inst.get_naturaleza_display() if inst.naturaleza else "",
            inst.estado.nombre if inst.estado else "",
            inst.municipio.nombre if inst.municipio else "",
            inst.email or "",
            inst.telefono or "",
            inst.estatus,
            "Sí" if inst.federado else "No",
            inst.fecha_registro.strftime("%d/%m/%Y") if inst.fecha_registro else "",
        ])

    return rows_to_response(headers, rows, "instituciones_export", fmt)


@login_required
def exportar_inscripciones_excel(request):
    """Exporta inscripciones de equipos a eventos a Excel o CSV."""
    out = _report_format_or_chooser(request, "Exportar inscripciones")
    if out[1] is not None:
        return out[1]
    fmt = out[0]

    perfil = request.user.userprofile
    if not (_es_federacion(perfil) or _es_institucional(perfil)):
        messages.error(request, "No tienes permisos para exportar inscripciones.")
        return redirect("dashboard")

    qs = InscripcionGrupoEvento.objects.filter(activo=True).select_related(
        "evento", "evento__estado", "grupo", "grupo__institucion",
        "grupo__institucion__estado",
    ).prefetch_related("grupo__tutores", "grupo__participantes")

    if _es_institucional(perfil):
        qs = qs.filter(grupo__institucion=perfil.institution)
    else:
        qs = _filtro_territorial(qs, perfil, "grupo__institucion__estado")

    headers = [
        "Evento", "Fecha Evento", "Estado Evento",
        "Equipo", "Código Equipo", "Institución",
        "Tutor(es)", "N° Participantes", "Fecha Inscripción",
    ]
    rows = []
    for ins in qs:
        tutores = ", ".join(
            f"{t.nombres} {t.apellidos}" for t in ins.grupo.tutores.all()
        )
        rows.append([
            ins.evento.nombre,
            ins.evento.fecha.strftime("%d/%m/%Y") if ins.evento.fecha else "",
            ins.evento.get_estado_evento_display(),
            ins.grupo.nombre,
            ins.grupo.codigo,
            ins.grupo.institucion.nombre if ins.grupo.institucion else "",
            tutores,
            ins.grupo.participantes.count(),
            ins.fecha_inscripcion.strftime("%d/%m/%Y") if hasattr(ins, "fecha_inscripcion") and ins.fecha_inscripcion else "",
        ])

    return rows_to_response(headers, rows, "inscripciones_export", fmt)
