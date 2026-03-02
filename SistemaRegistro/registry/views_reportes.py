"""Vistas para búsqueda avanzada y reportes de clubes."""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import csv

from .models import Club, MembresiaClu, HistorialClub


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
    
    clubes = clubes.select_related('institucion_creadora').annotate(
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
    
    # Tasa de aprobación
    total_procesados = Club.objects.filter(status__in=['aprobado', 'rechazado']).count()
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
    
    tiempos_revision = []
    for club in clubes_aprobados_recientes:
        if club.fecha_aprobacion and club.fecha_creacion:
            dias = (club.fecha_aprobacion - club.fecha_creacion).days
            tiempos_revision.append(dias)
    
    tiempo_promedio_revision = sum(tiempos_revision) / len(tiempos_revision) if tiempos_revision else 0
    
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
