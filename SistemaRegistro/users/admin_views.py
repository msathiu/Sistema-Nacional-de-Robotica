from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count
from registry.models import Institucion, Participante, Evento, Grupo, Club
from users.models import UserProfile


@staff_member_required
def admin_dashboard(request):
    """Dashboard personalizado para el admin de Django"""
    
    # KPIs principales
    context = {
        'total_instituciones': Institucion.objects.count(),
        'instituciones_activas': Institucion.objects.filter(activa=True).count(),
        'instituciones_pendientes': Institucion.objects.filter(activa=False, eliminado=False).count(),
        'total_participantes': Participante.objects.count(),
        'total_eventos': Evento.objects.count(),
        'total_grupos': Grupo.objects.count(),
        'total_clubes': Club.objects.count(),
        'total_usuarios': UserProfile.objects.count(),
        
        # Distribución por tipo de usuario
        'usuarios_por_tipo': UserProfile.objects.values('user_type').annotate(total=Count('id')),
        
        # Instituciones por estado (top 5)
        'instituciones_por_estado': Institucion.objects.values('estado__nombre').annotate(
            total=Count('id')
        ).order_by('-total')[:5],
        
        # Últimas instituciones registradas
        'ultimas_instituciones': Institucion.objects.order_by('-fecha_registro')[:5],
        
        # Próximos eventos
        'proximos_eventos': Evento.objects.filter(activo=True).order_by('fecha')[:5],
    }
    
    return render(request, 'admin/dashboard.html', context)
