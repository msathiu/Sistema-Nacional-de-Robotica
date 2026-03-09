"""
Vistas profesionales para gestión de equipos (grupos).

Incluye:
- Crear equipo con tutores y participantes
- Editar equipo
- Ver detalles
- APIs de búsqueda
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Grupo, Tutor, Participante
from .forms_grupos import GrupoForm


@login_required
def crear_equipo(request):
    """Vista para crear un nuevo equipo."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'institucional':
        messages.error(request, "Solo instituciones pueden crear equipos.")
        return redirect('dashboard')
    
    institucion = request.user.userprofile.institution
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, institucion=institucion, usuario=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear grupo
                    grupo = form.save(commit=False)
                    grupo.usuario_creador = request.user
                    grupo.institucion = institucion
                    grupo.save()
                    
                    # 2. Asignar tutores (OBLIGATORIO)
                    tutores_ids = request.POST.getlist('tutores[]')
                    # Filtrar IDs vacíos, None y duplicados
                    tutores_ids = list(set([tid for tid in tutores_ids if tid and str(tid).strip()]))
                    
                    # Debug: Log de IDs recibidos
                    print(f"[DEBUG] IDs de tutores recibidos: {tutores_ids}")
                    
                    if not tutores_ids:
                        raise ValueError("Debe asignar al menos un tutor al equipo")
                    
                    # Validar que los tutores pertenecen a la institución
                    tutores = Tutor.objects.filter(
                        id__in=tutores_ids,
                        institucion=institucion,
                        status='activo'
                    )
                    
                    print(f"[DEBUG] Tutores encontrados: {tutores.count()} de {len(tutores_ids)} esperados")
                    
                    if tutores.count() != len(tutores_ids):
                        ids_encontrados = set(tutores.values_list('id', flat=True))
                        ids_no_encontrados = set(str(tid) for tid in tutores_ids) - set(str(id) for id in ids_encontrados)
                        raise ValueError(f"Algunos tutores no son válidos. IDs no encontrados: {ids_no_encontrados}")
                    
                    grupo.tutores.set(tutores)
                    
                    # 3. Asignar participantes
                    participantes_ids = request.POST.getlist('participantes[]')
                    # Filtrar IDs vacíos, None y duplicados
                    participantes_ids = list(set([pid for pid in participantes_ids if pid and str(pid).strip()]))
                    
                    # Debug: Log de IDs recibidos
                    print(f"[DEBUG] IDs de participantes recibidos: {participantes_ids}")
                    
                    if not participantes_ids:
                        raise ValueError("Debe agregar al menos un participante al equipo")
                    
                    # Validar que los participantes pertenecen a la institución
                    participantes = Participante.objects.filter(
                        id__in=participantes_ids,
                        institucion=institucion,
                        status='activo'
                    )
                    
                    print(f"[DEBUG] Participantes encontrados: {participantes.count()} de {len(participantes_ids)} esperados")
                    
                    if participantes.count() != len(participantes_ids):
                        # Identificar cuáles IDs no se encontraron
                        ids_encontrados = set(participantes.values_list('id', flat=True))
                        ids_no_encontrados = set(int(pid) for pid in participantes_ids) - ids_encontrados
                        raise ValueError(f"Algunos participantes no son válidos. IDs no encontrados: {ids_no_encontrados}")
                    
                    grupo.participantes.set(participantes)
                    
                    messages.success(
                        request,
                        f'✅ Equipo "{grupo.nombre}" creado exitosamente con código {grupo.codigo}'
                    )
                    return redirect('mis_grupos')
                    
            except ValueError as e:
                messages.error(request, f"Error: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error al crear el equipo: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = GrupoForm(institucion=institucion, usuario=request.user)
    
    # Obtener tutores y participantes disponibles
    tutores_disponibles = Tutor.objects.filter(
        institucion=institucion,
        status='activo'
    ).order_by('apellidos', 'nombres')
    
    participantes_disponibles = Participante.objects.filter(
        institucion=institucion,
        status='activo'
    ).order_by('apellidos', 'nombres')
    
    context = {
        'form': form,
        'tutores_disponibles': tutores_disponibles,
        'participantes_disponibles': participantes_disponibles,
        'total_tutores': tutores_disponibles.count(),
        'total_participantes': participantes_disponibles.count(),
        'criterios': Grupo.CRITERIO_CHOICES,
    }
    return render(request, 'registry/grupo_crear.html', context)


@login_required
def editar_equipo(request, grupo_id):
    """Vista para editar un equipo existente."""
    grupo = get_object_or_404(
        Grupo,
        id=grupo_id,
        usuario_creador=request.user,
        activo=True
    )
    
    # Solo se puede editar si está en estado 'editable'
    if grupo.estado_grupo != 'editable':
        messages.warning(request, "Este equipo no puede ser editado en su estado actual.")
        return redirect('mis_grupos')
    
    institucion = request.user.userprofile.institution
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo, institucion=institucion, usuario=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Actualizar grupo
                    grupo = form.save()
                    
                    # 2. Actualizar tutores
                    tutores_ids = request.POST.getlist('tutores[]')
                    # Filtrar IDs vacíos o inválidos
                    tutores_ids = [tid for tid in tutores_ids if tid and tid.strip()]
                    
                    if tutores_ids:
                        tutores = Tutor.objects.filter(
                            id__in=tutores_ids,
                            institucion=institucion,
                            status='activo'
                        )
                        grupo.tutores.set(tutores)
                    else:
                        grupo.tutores.clear()
                    
                    # 3. Actualizar participantes
                    participantes_ids = request.POST.getlist('participantes[]')
                    # Filtrar IDs vacíos o inválidos
                    participantes_ids = [pid for pid in participantes_ids if pid and pid.strip()]
                    
                    if not participantes_ids:
                        raise ValueError("Debe tener al menos un participante")
                    
                    participantes = Participante.objects.filter(
                        id__in=participantes_ids,
                        institucion=institucion,
                        status='activo'
                    )
                    grupo.participantes.set(participantes)
                    
                    messages.success(request, f'✅ Equipo "{grupo.nombre}" actualizado exitosamente')
                    return redirect('mis_grupos')
                    
            except ValueError as e:
                messages.error(request, f"Error: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error al actualizar: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = GrupoForm(instance=grupo, institucion=institucion, usuario=request.user)
    
    # Obtener datos actuales
    tutores_actuales = grupo.tutores.all()
    participantes_actuales = grupo.participantes.all()
    
    # Obtener disponibles
    tutores_disponibles = Tutor.objects.filter(
        institucion=institucion,
        status='activo'
    ).order_by('apellidos', 'nombres')
    
    participantes_disponibles = Participante.objects.filter(
        institucion=institucion,
        status='activo'
    ).order_by('apellidos', 'nombres')
    
    context = {
        'form': form,
        'grupo': grupo,
        'tutores_actuales': tutores_actuales,
        'participantes_actuales': participantes_actuales,
        'tutores_disponibles': tutores_disponibles,
        'participantes_disponibles': participantes_disponibles,
        'es_edicion': True,
    }
    return render(request, 'registry/grupo_editar.html', context)


@login_required
def ver_equipo(request, grupo_id):
    """Vista para ver detalles de un equipo."""
    grupo = get_object_or_404(
        Grupo.objects.select_related('institucion', 'usuario_creador')
                     .prefetch_related('tutores', 'participantes', 'inscripciones'),
        id=grupo_id,
        usuario_creador=request.user,
        activo=True
    )
    
    context = {
        'grupo': grupo,
        'tutores': grupo.tutores.all(),
        'participantes': grupo.participantes.all(),
        'inscripciones': grupo.inscripciones.select_related('evento').all(),
        'puede_editar': grupo.estado_grupo == 'editable',
    }
    return render(request, 'registry/grupo_detalle.html', context)


@login_required
def eliminar_equipo(request, grupo_id):
    """Vista para eliminar un equipo (solo si está editable)."""
    if request.method != 'POST':
        return redirect('mis_grupos')
    
    grupo = get_object_or_404(
        Grupo,
        id=grupo_id,
        usuario_creador=request.user,
        activo=True
    )
    
    if grupo.estado_grupo != 'editable':
        messages.error(request, "No se puede eliminar un equipo inscrito o bloqueado.")
        return redirect('mis_grupos')
    
    nombre = grupo.nombre
    codigo = grupo.codigo
    
    # Soft delete
    grupo.activo = False
    grupo.save(update_fields=['activo'])
    
    messages.success(request, f'✅ Equipo "{nombre}" ({codigo}) eliminado correctamente.')
    return redirect('mis_grupos')


# ============================================================================
# APIs DE BÚSQUEDA
# ============================================================================

@login_required
def api_buscar_tutor(request):
    """API para buscar tutor por cédula."""
    cedula = request.GET.get('cedula', '').strip()
    
    if not cedula:
        return JsonResponse({'found': False, 'error': 'Cédula requerida'})
    
    # Limpiar cédula (solo números)
    cedula_limpia = ''.join(filter(str.isdigit, cedula))
    
    if not cedula_limpia:
        return JsonResponse({'found': False, 'error': 'Cédula inválida'})
    
    institucion = request.user.userprofile.institution
    
    try:
        tutor = Tutor.objects.get(
            cedula=cedula_limpia,
            institucion=institucion,
            status='activo'
        )
        
        return JsonResponse({
            'found': True,
            'id': str(tutor.id),
            'nombre_completo': tutor.get_nombre_completo(),
            'nacionalidad': tutor.get_nacionalidad_display(),
            'cedula': tutor.cedula,
            'email': tutor.email,
            'telefono': f"{tutor.telefono_codigo}-{tutor.telefono}" if tutor.telefono_codigo and tutor.telefono else '',
            'profesion': tutor.profesion or 'No especificada',
        })
    except Tutor.DoesNotExist:
        return JsonResponse({'found': False})
    except Exception as e:
        return JsonResponse({'found': False, 'error': str(e)})


@login_required
def api_buscar_participante_equipo(request):
    """API para buscar participante por cédula (personal o escolar)."""
    cedula = request.GET.get('cedula', '').strip()
    
    if not cedula:
        return JsonResponse({'found': False, 'error': 'Cédula requerida'})
    
    # Limpiar cédula (solo números)
    cedula_limpia = ''.join(filter(str.isdigit, cedula))
    
    if not cedula_limpia:
        return JsonResponse({'found': False, 'error': 'Cédula inválida'})
    
    institucion = request.user.userprofile.institution
    
    try:
        participante = Participante.objects.get(
            Q(cedula=cedula_limpia) | Q(cedula_escolar=cedula_limpia),
            institucion=institucion,
            status='activo'
        )
        
        return JsonResponse({
            'found': True,
            'id': participante.id,
            'nombres': participante.nombres,
            'apellidos': participante.apellidos,
            'nombre_completo': f"{participante.nombres} {participante.apellidos}",
            'nacionalidad': participante.get_nacionalidad_display(),
            'cedula': participante.cedula,
            'cedula_escolar': participante.cedula_escolar or '',
            'edad': participante.edad,
            'grado_escolar': participante.get_grado_escolar_display(),
            'email': participante.email,
            'telefono': participante.telefono_completo,
        })
    except Participante.DoesNotExist:
        return JsonResponse({'found': False})
    except Participante.MultipleObjectsReturned:
        # Si hay múltiples, retornar el primero
        participante = Participante.objects.filter(
            Q(cedula=cedula_limpia) | Q(cedula_escolar=cedula_limpia),
            institucion=institucion,
            status='activo'
        ).first()
        
        return JsonResponse({
            'found': True,
            'id': participante.id,
            'nombres': participante.nombres,
            'apellidos': participante.apellidos,
            'nombre_completo': f"{participante.nombres} {participante.apellidos}",
            'edad': participante.edad,
            'grado_escolar': participante.get_grado_escolar_display(),
            'email': participante.email,
        })
    except Exception as e:
        return JsonResponse({'found': False, 'error': str(e)})



@login_required
def mis_grupos(request):
    """Vista para listar todos los grupos del usuario institucional."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'institucional':
        messages.error(request, "Solo instituciones pueden acceder a esta sección.")
        return redirect('dashboard')
    
    institucion = request.user.userprofile.institution
    
    # Obtener grupos con anotaciones
    grupos = Grupo.objects.filter(
        usuario_creador=request.user,
        activo=True
    ).select_related(
        'institucion',
        'usuario_creador',
        'evento'
    ).prefetch_related(
        'tutores',
        'participantes'
    ).annotate(
        num_participantes=Count('participantes', distinct=True),
        num_tutores=Count('tutores', distinct=True)
    ).order_by('-fecha_registro')
    
    # Preparar datos para el template
    grupos_data = []
    for grupo in grupos:
        # Obtener primer tutor como responsable
        tutor_principal = grupo.tutores.first()
        
        # Generar descripción del criterio
        criterio_detalle = ""
        if grupo.criterio == 'edad':
            if grupo.edad_desde == grupo.edad_hasta:
                criterio_detalle = f"{grupo.edad_desde} años"
            else:
                criterio_detalle = f"{grupo.edad_desde} a {grupo.edad_hasta} años"
        elif grupo.criterio == 'nivel':
            criterio_detalle = grupo.get_nivel_educativo_display() if grupo.nivel_educativo else "No especificado"
        elif grupo.criterio == 'proyecto':
            criterio_detalle = grupo.nombre_proyecto if grupo.nombre_proyecto else "Sin nombre"
        
        grupos_data.append({
            'id': grupo.id,
            'nombre': grupo.nombre,
            'codigo': grupo.codigo,
            'criterio': grupo.criterio,  # Valor del campo para filtros
            'criterio_display': grupo.get_criterio_display(),  # Display para mostrar
            'criterio_detalle': criterio_detalle,  # Detalle específico del criterio
            'estado_grupo': grupo.estado_grupo,
            'num_participantes': grupo.num_participantes,
            'num_tutores': grupo.num_tutores,
            'tutor_nombre': tutor_principal.nombres if tutor_principal else 'Sin asignar',
            'tutor_apellidos': tutor_principal.apellidos if tutor_principal else '',
            'fecha_registro': grupo.fecha_registro,
            'tiene_evento': grupo.evento is not None,
            'puede_eliminar': grupo.estado_grupo == 'editable' and not grupo.evento,
        })
    
    context = {
        'grupos': grupos_data,
        'total_grupos': len(grupos_data),
    }
    
    return render(request, 'registry/grupos_lista.html', context)
