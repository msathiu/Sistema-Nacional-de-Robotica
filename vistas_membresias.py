@login_required
def gestionar_membresias_club(request, club_id):
    """Vista para que el propietario del club gestione las membresías."""
    club = get_object_or_404(Club, id=club_id)
    
    # Verificar que el usuario sea el propietario del club
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'institucional':
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    if club.institucion_creadora != request.user.userprofile.institution:
        messages.error(request, "No tienes permiso para gestionar este club.")
        return redirect("clubes_lista")
    
    # Solo clubes aprobados pueden tener membresías
    if club.status != 'aprobado':
        messages.warning(request, "Solo los clubes aprobados pueden gestionar membresías.")
        return redirect("clubes_lista")
    
    # Obtener membresías por estado
    membresias_pendientes = club.membresias.filter(estado='pendiente').select_related('institucion')
    membresias_aprobadas = club.membresias.filter(estado='aprobada').select_related('institucion')
    membresias_rechazadas = club.membresias.filter(estado='rechazada').select_related('institucion')
    
    context = {
        'club': club,
        'membresias_pendientes': membresias_pendientes,
        'membresias_aprobadas': membresias_aprobadas,
        'membresias_rechazadas': membresias_rechazadas,
        'total_miembros': membresias_aprobadas.count(),
        'cupos_disponibles': club.cupos_disponibles,
    }
    return render(request, 'registry/gestionar_membresias_club.html', context)


@login_required
def mis_membresias(request):
    """Vista para que una institución vea sus membresías a clubes."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'institucional':
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    institucion = request.user.userprofile.institution
    
    # Obtener membresías por estado
    membresias_pendientes = MembresiaClu.objects.filter(
        institucion=institucion,
        estado='pendiente'
    ).select_related('club', 'club__institucion_creadora')
    
    membresias_aprobadas = MembresiaClu.objects.filter(
        institucion=institucion,
        estado='aprobada'
    ).select_related('club', 'club__institucion_creadora')
    
    membresias_rechazadas = MembresiaClu.objects.filter(
        institucion=institucion,
        estado='rechazada'
    ).select_related('club', 'club__institucion_creadora')
    
    context = {
        'membresias_pendientes': membresias_pendientes,
        'membresias_aprobadas': membresias_aprobadas,
        'membresias_rechazadas': membresias_rechazadas,
        'total_clubes': membresias_aprobadas.count(),
    }
    return render(request, 'registry/mis_membresias.html', context)


@login_required
def detalle_membresia(request, membresia_id):
    """Vista detallada de una membresía específica."""
    membresia = get_object_or_404(MembresiaClu.objects.select_related(
        'club', 'club__institucion_creadora', 'institucion'
    ), id=membresia_id)
    
    # Verificar permisos
    user_type = request.user.userprofile.user_type
    
    if user_type == 'institucional':
        # Puede ver si es propietario del club o miembro
        es_propietario = membresia.club.institucion_creadora == request.user.userprofile.institution
        es_miembro = membresia.institucion == request.user.userprofile.institution
        
        if not (es_propietario or es_miembro):
            messages.error(request, "No tienes permiso para ver esta membresía.")
            return redirect("clubes_lista")
    elif user_type not in ['fed_central', 'fed_regional', 'superuser']:
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect("dashboard")
    
    context = {
        'membresia': membresia,
        'es_propietario': membresia.club.institucion_creadora == request.user.userprofile.institution,
    }
    return render(request, 'registry/detalle_membresia.html', context)
