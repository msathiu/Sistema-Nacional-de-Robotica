from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .models import Estados, Municipios
from registry.models import (
    Club,
    Dependencia,
    Estado,
    Grupo,
    Institucion,
    Municipio,
    Participante,
    Evento,
    Parroquia,
    InscripcionGrupoEvento,
)
from .models import UserProfile  
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
import random
import string
from django.views.generic.edit import UpdateView 
from django.urls import reverse
from registry.models import Evento
from django.db import transaction
from .forms import InstitucionRegistrationForm, CustomUserCreationForm, ParticipanteRegistrationForm, ClubRegistrationForm, SedeRegionalForm, ParticipanteModalEditForm
import pandas as pd
from django.contrib.admin.models import LogEntry
from django.utils import timezone
from .decorators import admin_required, institucional_required, owns_institution, admin_or_owner_required
from django.views.decorators.cache import never_cache
from django.db.models.functions import ExtractMonth
from django.apps import apps  
import secrets
from datetime import date, datetime 


@login_required
def detalle_evento_inscripcion(request, evento_id):
    """
    Vista para ver detalles de un evento e inscribir grupos
    """
    evento = get_object_or_404(
        Evento.objects.select_related('estado', 'municipio', 'parroquia'),
        id=evento_id,
        activo=True
    )
    
    # Obtener grupos del usuario actual que no están inscritos en este evento
    grupos_disponibles = Grupo.objects.filter(
        usuario_creador=request.user,
        activo=True
    ).exclude(
        inscripciones__evento=evento
    )
    
    # Obtener grupos ya inscritos
    grupos_inscritos = InscripcionGrupoEvento.objects.filter(
        evento=evento,
        activo=True
    ).select_related('grupo')
    
    hoy = date.today()
    
    context = {
        'evento': evento,
        'grupos_disponibles': grupos_disponibles,
        'grupos_inscritos': grupos_inscritos,
        'hoy': hoy,
    }
    return render(request, 'users/detalle_evento_inscripcion.html', context)


@login_required
@transaction.atomic
def inscribir_grupo_evento(request, evento_id):
    """
    Vista para inscribir un grupo en un evento
    """
    if request.method == 'POST':
        evento = get_object_or_404(Evento, id=evento_id, activo=True)
        grupo_id = request.POST.get('grupo_id')
        rol = request.POST.get('rol', 'participante')
        
        try:
            grupo = Grupo.objects.get(id=grupo_id, usuario_creador=request.user)
        except Grupo.DoesNotExist:
            messages.error(request, "❌ El grupo seleccionado no existe o no te pertenece.")
            return redirect('detalle_evento_inscripcion', evento_id=evento_id)
        
        # Verificar que el evento esté abierto
        if evento.estado_evento != 'abierto':
            messages.error(request, "❌ El evento no está abierto para inscripciones.")
            return redirect('detalle_evento_inscripcion', evento_id=evento_id)
        
        # Verificar fecha
        if evento.fecha < date.today():
            messages.error(request, "❌ No puedes inscribirte en un evento que ya pasó.")
            return redirect('detalle_evento_inscripcion', evento_id=evento_id)
        
        # Verificar que el grupo no esté ya inscrito
        if InscripcionGrupoEvento.objects.filter(evento=evento, grupo=grupo).exists():
            messages.warning(request, "⚠️ Este grupo ya está inscrito en el evento.")
            return redirect('detalle_evento_inscripcion', evento_id=evento_id)
        
        # Crear inscripción
        InscripcionGrupoEvento.objects.create(
            evento=evento,
            grupo=grupo,
            rol_participacion=rol,
            activo=True
        )
        
        messages.success(request, f"✅ Grupo '{grupo.nombre}' inscrito exitosamente en el evento.")
        return redirect('detalle_evento_inscripcion', evento_id=evento_id)
    
    return redirect('eventos_disponibles')

def home(request):
    """Página principal con opciones de login y registro"""
    return render(request, 'users/home.html')



def register(request):
    """Vista de registro de participante compatible con campos de 7 dígitos"""
    
    if not request.user.is_authenticated or request.user.userprofile.user_type != 'institucional':
        messages.error(request, "No tienes permisos para registrar participantes.")
        return redirect('login')

    perfil_inst = request.user.userprofile.institution
    estado_inst = perfil_inst.estado
    municipios = Municipio.objects.filter(estado=estado_inst).order_by('nombre')

    if request.method == 'POST':
        participante_form = ParticipanteRegistrationForm(request.POST)
        
        # Extracción de campos que no están en el form o requieren manejo manual
        email = request.POST.get('email')
        nacionalidad = request.POST.get('nacionalidad', 'V')
        cedula_num = request.POST.get('cedula')
        
        # Códigos de área (Se guardan en sus propios campos de max_length=4)
        cod_area_part = request.POST.get('codigo_area')
        cod_area_rep = request.POST.get('codigo_area_representante')
        
        profesion = request.POST.get('profesion', '')
        parroquia_id = request.POST.get('parroquia')

        if participante_form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Formatear Cédula Principal (Max 20 chars, esto cabe bien)
                    cedula_completa = f"{nacionalidad}-{cedula_num}"
                    
                    if User.objects.filter(username=cedula_completa).exists():
                        messages.error(request, f"Ya existe un registro con la cédula {cedula_completa}")
                        return render(request, 'users/register.html', {
                            'participante_form': participante_form,
                            'municipios': municipios,
                            'institucion': perfil_inst
                        })

                    # 2. Crear Usuario
                    password_aleatoria = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                    user = User.objects.create_user(
                        username=cedula_completa,
                        email=email,
                        password=password_aleatoria
                    )
                    
                    UserProfile.objects.get_or_create(user=user, defaults={'user_type': 'participante'})
                    
                    # 3. Preparar Participante
                    participante = participante_form.save(commit=False)
                    participante.user = user
                    participante.cedula = cedula_completa
                    participante.email = email
                    participante.institucion = perfil_inst
                    participante.estado = estado_inst
                    
                    # ASIGNACIÓN CORRECTA DE TELÉFONOS (Sin concatenar para evitar el error de los 7 caracteres)
                    if cod_area_part:
                        participante.codigo_area = cod_area_part
                    
                    # Cédula del representante (Se concatena nacionalidad)
                    rep_nac = request.POST.get('rep_nacionalidad', 'V')
                    if participante.cedula_representante:
                        participante.cedula_representante = f"{rep_nac}-{participante.cedula_representante}"

                    # Teléfono del representante
                    if cod_area_rep:
                        participante.codigo_area_representante = cod_area_rep

                    # La edad NO se asigna porque es una @property en tu modelo
                    
                    if profesion:
                        # Si tu modelo no tiene el campo 'profesion', esto fallará. 
                        # Si lo tiene, asegúrate de que exista en el model.
                        pass 
                    
                    if parroquia_id:
                        try:
                            participante.parroquia = Parroquia.objects.get(id=parroquia_id)
                        except:
                            pass
                    
                    # 4. Guardar (Aquí se ejecuta el clean() del modelo que valida los 7 dígitos)
                    participante.save()
                
                messages.success(request, f'Participante registrado exitosamente.')
                return redirect('lista_participantes')

            except Exception as e:
                messages.error(request, f'Error crítico: {str(e)}')
        else:
            for field, errors in participante_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        participante_form = ParticipanteRegistrationForm()

    return render(request, 'users/register.html', {
        'participante_form': participante_form,
        'municipios': municipios,
        'institucion': perfil_inst
    })

def custom_login(request):
    """Vista de login personalizada con redirección para superusuarios"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Si es superusuario, redirigir al admin de Django
                if user.is_superuser:
                    messages.success(request, f'¡Bienvenido Superusuario, {username}!')
                    return redirect('/admin/')
                
                # Para otros usuarios, continuar con la lógica normal
                try:
                    profile = user.userprofile
                    user_type = profile.user_type
                except UserProfile.DoesNotExist:
                    if user.is_staff:
                        user_type = 'admin'
                    else:
                        user_type = 'participante'
                
                messages.success(request, f'¡Bienvenido de nuevo, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})
@login_required
def dashboard(request):
    """Router principal del dashboard con soberanía territorial completa"""
    try:
        user_profile = request.user.userprofile
        user_type = user_profile.user_type
        user_estado = user_profile.estado  
    except Exception: # Captura si no existe perfil
        if request.user.is_superuser:
            user_type = 'superuser'
            user_estado = None
            user_profile = None
        else:
            messages.error(request, 'No tienes un perfil configurado.')
            return redirect('login')

    roles_administrativos = ['tecnologico', 'fed_central', 'fed_regional', 'superuser']

    # --- LÓGICA PARA ADMINISTRADORES (CENTRAL Y REGIONAL) ---
    if user_type in roles_administrativos:
        # CONFIGURACIÓN DE FILTROS DINÁMICOS
        filtros_inst = Q()
        filtros_club = Q()
        filtros_part = Q()

        # Soberanía Territorial: Filtrar por estado si es regional
        if user_type == 'fed_regional' and user_estado:
            filtros_inst &= Q(estado=user_estado)
            filtros_club &= Q(institucion_creadora__estado=user_estado)
            filtros_part &= Q(estado=user_estado)
        
        # 1. MÉTRICAS BÁSICAS
        total_participantes = Participante.objects.filter(filtros_part).count()
        total_instituciones = Institucion.objects.filter(filtros_inst).count()
        total_clubes = Club.objects.filter(filtros_club).count()
        total_eventos = Evento.objects.count()
        
        pendientes_aprobacion = Institucion.objects.filter(filtros_inst, activa=False).count()
        cobertura_nacional = Institucion.objects.filter(filtros_inst).values('estado').distinct().count()
        
        # Contar tutores únicos basados en la cédula dentro del ámbito territorial
        total_tutores = Grupo.objects.filter(
            participantes__in=Participante.objects.filter(filtros_part)
        ).values('tutor_cedula').distinct().count()

        # 2. CURVA DE INSCRIPCIÓN MENSUAL (Año Actual)
        year_actual = datetime.now().year
        registros_por_mes = (
            Institucion.objects.filter(filtros_inst, fecha_registro__year=year_actual)
            .annotate(mes=ExtractMonth('fecha_registro'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        data_crecimiento = [0] * 12
        for r in registros_por_mes:
            if r['mes']: 
                data_crecimiento[r['mes'] - 1] = r['total']

        # 3. DISTRIBUCIÓN DE GÉNERO
        total_p = total_participantes or 1
        mujeres = Participante.objects.filter(filtros_part, sexo='F').count() 
        hombres = Participante.objects.filter(filtros_part, sexo='M').count()
        porcentaje_mujeres = round((mujeres / total_p) * 100)
        porcentaje_hombres = round((hombres / total_p) * 100)

        # 4. ESPECIALIDADES DE CLUBES (Radar Chart)
        clubes_stats = Club.objects.filter(filtros_club).values('linea_1').annotate(total=Count('id')).order_by('-total')
        clubes_labels = [c['linea_1'] if c['linea_1'] else 'General' for c in clubes_stats]
        clubes_data = [c['total'] for c in clubes_stats]
        if not clubes_labels:
            clubes_labels, clubes_data = ['Sin Datos'], [0]

        # 5. DISTRIBUCIÓN DE TUTORES POR ESTADO (Barras)
        tutores_stats = (
            Participante.objects.filter(filtros_part).values('estado__nombre')
            .annotate(total=Count('grupos__tutor_cedula', distinct=True))
            .order_by('-total')[:5]
        )
        tutores_labels = [t['estado__nombre'] for t in tutores_stats if t['estado__nombre']]
        tutores_data = [t['total'] for t in tutores_stats if t['estado__nombre']]

        # 6. DATOS DEL MAPA
        conteo_db = Institucion.objects.filter(filtros_inst).values('estado__nombre').annotate(total=Count('id'))
        mapa_data = {registro['estado__nombre']: registro['total'] for registro in conteo_db}

        context = {
            'perfil': user_profile,
            'user_type': user_type,
            'total_participantes': total_participantes,
            'total_instituciones': total_instituciones,
            'total_clubes': total_clubes,
            'total_tutores': total_tutores,
            'total_eventos': total_eventos,
            'pendientes_aprobacion': pendientes_aprobacion,
            'cobertura_nacional': cobertura_nacional,
            
            'es_central': user_type in ['fed_central', 'superuser'], 
            'es_regional': user_type == 'fed_regional',
            
            'data_crecimiento': data_crecimiento,
            'meses_labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            'porcentaje_mujeres': porcentaje_mujeres,
            'porcentaje_hombres': porcentaje_hombres,
            'clubes_labels': clubes_labels,
            'clubes_data': clubes_data,
            'tutores_labels': tutores_labels,
            'tutores_data': tutores_data,
            'mapa_data': mapa_data,
        }
        return render(request, 'users/dashboard_admin.html', context)

    # --- REDIRECCIÓN PARA USUARIOS NO ADMINISTRATIVOS ---
    if user_type == 'institucional':
        return redirect('dashboard_institucional')
    elif user_type == 'participante':
        return redirect('dashboard_participante')

    messages.error(request, 'Tipo de usuario no reconocido o acceso denegado.')
    return redirect('home')

@login_required
def dashboard_participante(request):
    """Panel de control exclusivo para participantes"""
    

    user_profile = request.user.userprofile
    
    if user_profile.user_type != 'participante':
        # Redirigir directamente al dashboard institucional si es el caso
        if user_profile.user_type == 'institucional':
             return redirect('dashboard_institucional') 
        return redirect('dashboard')
        
    context = {
        'user': request.user,
        'user_profile': user_profile,
        
    }
    
    try:
        participante = Participante.objects.get(user=request.user)
        context['participante'] = participante
    except Participante.DoesNotExist:
        context['participante'] = None
        
    return render(request, 'users/dashboard_participante.html', context)

def crear_usuario_institucional(request, institucion_id):
    # Aquí iría la lógica para crear el usuario asociado a la institución
    # Por ahora, puedes poner un pass o un return básico para que el servidor arranque
    return render(request, 'users/algun_template.html')
@login_required
def dashboard_institucional(request):
    """
    Vista principal del panel para usuarios institucionales.
    Muestra métricas clave y listas rápidas de eventos y grupos.
    """
    # 1. Validación de perfil y tipo de usuario
    try:
        user_profile = request.user.userprofile
    except AttributeError:
        # Si el usuario no tiene perfil (ej. superuser sin perfil creado)
        messages.error(request, "No se encontró un perfil asociado a tu cuenta.")
        return redirect('dashboard')

    if user_profile.user_type != 'institucional' or not user_profile.institution:
        messages.warning(request, "Acceso restringido a cuentas institucionales.")
        return redirect('dashboard')

    # 2. Configuración de datos básicos
    institution = user_profile.institution
    usuario = request.user
    hoy = timezone.now().date()

    # 3. Métricas de Grupos y Participantes
    # Obtenemos los grupos creados por el usuario actual
    mis_grupos = Grupo.objects.filter(usuario_creador=usuario, activo=True)
    total_mis_grupos = mis_grupos.count()
    
    # Participantes vinculados a la institución del usuario
    total_mis_participantes = Participante.objects.filter(institucion=institution).count()
    
    # 4. Métricas de Eventos
    # Eventos globales que están por venir y están activos
    eventos_disponibles_qs = Evento.objects.filter(
        fecha__gte=hoy, 
        activo=True,
        estado_evento='abierto'
    )
    total_eventos_disponibles = eventos_disponibles_qs.count()
    
    # Eventos donde el usuario ya tiene grupos inscritos
    # Usamos distinct() para evitar contar el mismo evento varias veces si tiene varios grupos
    eventos_asignados = Evento.objects.filter(
        grupos_inscritos__usuario_creador=usuario,
        activo=True
    ).distinct().count()

    # 5. Listas para las tablas del dashboard
    # Limitamos a los 5 eventos más cercanos y los 3 grupos más recientes
    proximos_eventos = eventos_disponibles_qs.order_by('fecha')[:5]
    grupos_recientes = mis_grupos.order_by('-fecha_registro')[:3]

    # 6. Construcción del contexto
    context = {
        'user_profile': user_profile,
        'institution': institution,
        'total_mis_grupos': total_mis_grupos,
        'total_mis_participantes': total_mis_participantes,
        'eventos_disponibles': total_eventos_disponibles, 
        'eventos_asignados': eventos_asignados,
        'proximos_eventos': proximos_eventos,
        'grupos_recientes': grupos_recientes,
        'hoy': hoy,
    }

    return render(request, 'users/dashboard_institucional.html', context)

def is_admin(user):
    """Verifica si el usuario es administrador"""
    return hasattr(user, 'userprofile') and user.userprofile.user_type == 'admin'

@admin_required
def exportar_participantes_excel(request):
    # Obtenemos todos los registros
    participantes = Participante.objects.all().values()
    df = pd.DataFrame(participantes)

    # Creamos la respuesta HTTP con el tipo de contenido de Excel
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Padrón_Nacional_Robotica.xlsx"'
    
    # Escribimos el dataframe al response
    df.to_excel(response, index=False, engine='openpyxl')
    return response

@admin_required
def ver_logs_sistema(request):
    # Usamos LogEntry de Django para mostrar las últimas acciones del panel
    logs = LogEntry.objects.all().select_related('user', 'content_type')[:100]
    return render(request, 'users/logs_sistema.html', {'logs': logs})

def create_institutional_user(request):
    """Redirige al formulario unificado de institución"""
    messages.info(request, 'Ahora el registro de instituciones incluye la creación de usuarios automáticamente.')
    return redirect('registrar_institucion')

@never_cache
@login_required
def lista_instituciones(request):
    perfil = request.user.userprofile
    user_type = perfil.user_type
    
    roles_admin = ['fed_central', 'fed_regional', 'superuser', 'tecnologico']
    
    if user_type not in roles_admin:
        messages.error(request, "No tienes permisos para gestionar instituciones.")
        return redirect('dashboard')

    # 1. Filtro base (Optimizado con select_related para evitar 1000 consultas)
    if user_type == 'fed_regional':
        instituciones_qs = Institucion.objects.filter(eliminado=False, estado=perfil.estado).select_related('estado', 'municipio')
    else:
        instituciones_qs = Institucion.objects.filter(eliminado=False).select_related('estado', 'municipio')

    # 2. KPIs CORREGIDOS:
    # Una institución está ACTIVA solo si activa=True Y estatus='aprobado'
    total_instituciones = instituciones_qs.count()
    instituciones_activas = instituciones_qs.filter(activa=True, estatus='aprobado').count()
    
    # Pendientes son todas las que NO cumplen lo anterior
    instituciones_pendientes = total_instituciones - instituciones_activas
    
    # 3. Construcción eficiente de la lista (Evitando el loop lento)
    # Es mejor usar un prefetch_related o buscar perfiles directamente
    instituciones_con_usuarios = []
    for inst in instituciones_qs:
        # Buscamos los usuarios asociados a través del perfil
        usuarios = User.objects.filter(userprofile__institution=inst)
        instituciones_con_usuarios.append({
            'institucion': inst, 
            'usuarios': usuarios
        })
    
    context = {
        'instituciones_con_usuarios': instituciones_con_usuarios,
        'total_instituciones': total_instituciones,
        'instituciones_activas': instituciones_activas,
        'instituciones_pendientes': instituciones_pendientes,
        'estados': Estado.objects.all(),
        'es_central': user_type in ['fed_central', 'superuser'],
        'es_regional': user_type == 'fed_regional',
        'perfil': perfil,
    }
    return render(request, 'users/lista_instituciones.html', context)
def registrar_institucion(request):
    """
    Registro de instituciones con detección de jurisdicción regional.
    """
    perfil_admin = getattr(request.user, 'userprofile', None) if request.user.is_authenticated else None
    
    # Roles y Permisos
    es_central = perfil_admin.user_type in ['fed_central', 'superuser'] if perfil_admin else False
    es_regional = perfil_admin.user_type == 'fed_regional' if perfil_admin else False
    es_federacion = es_central or es_regional

    # Template dinámico
    base_template = 'users/base_dashboard.html' if es_federacion else 'base.html'

    if request.method == 'POST':
        form = InstitucionRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    institucion = form.save(commit=False)
                    
                    # A. Lógica de Activación
                    if es_central:
                        institucion.activa = True
                        institucion.estatus = 'aprobado'
                    else:
                        institucion.activa = False
                        institucion.estatus = 'pendiente'
                    
                    # B. Forzar Estado si es Regional (Seguridad lado servidor)
                    if es_regional and perfil_admin.estado:
                        institucion.estado = perfil_admin.estado
                    
                    institucion.save()

                    # C. Usuario de Django
                    password = form.cleaned_data.get('password')
                    nuevo_usuario = User.objects.create_user(
                        username=institucion.email, 
                        email=institucion.email,
                        password=password,
                        is_active=True if es_central else False 
                    )
                    
                    institucion.usuario = nuevo_usuario
                    institucion.save(update_fields=['usuario'])

                    # D. Perfil Institucional
                    profile, _ = UserProfile.objects.get_or_create(user=nuevo_usuario)
                    profile.user_type = 'institucional'
                    profile.institution = institucion
                    # Si la sede nace en un estado, el perfil del usuario también
                    profile.estado = institucion.estado 
                    profile.save()

                    # E. Redirecciones
                    if es_central:
                        messages.success(request, f"Sede '{institucion.nombre}' activada con éxito.")
                        return redirect('lista_instituciones')
                    elif es_federacion:
                        messages.info(request, f"Registro de '{institucion.nombre}' enviado a Sede Central para validación.")
                        return redirect('lista_instituciones')
                    else:
                        return render(request, 'users/registro_pendiente.html', {
                            'nombre_inst': institucion.nombre,
                            'email': institucion.email,
                            'base_template': base_template
                        })

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        # Inicialización del formulario con el estado predeterminado
        initial_data = {}
        if es_regional and perfil_admin.estado:
            initial_data['estado'] = perfil_admin.estado.id
        
        form = InstitucionRegistrationForm(initial=initial_data)

    context = {
        'form': form,
        'base_template': base_template,
        'dependencias': Dependencia.objects.all(),
        'es_federacion': es_federacion,
        'es_central': es_central,
        'es_regional': es_regional,
        'estado_fijo_id': perfil_admin.estado.id if es_regional and perfil_admin.estado else None
    }

    return render(request, 'users/registrar_institucion.html', context)

@login_required
def lista_participantes(request):
    """Vista inteligente: Federación (Central/Regional) e Instituciones"""
    perfil = request.user.userprofile
    user_type = perfil.user_type
    
    # 1. Definir el Queryset base según permisos
    if user_type in ['fed_central', 'superuser', 'tecnologico']:
        participantes = Participante.objects.all()
    elif user_type == 'fed_regional':
        participantes = Participante.objects.filter(estado=perfil.estado)
    elif user_type == 'institucional':
        participantes = Participante.objects.filter(institucion=perfil.institution)
    else:
        return redirect('dashboard')

    # 2. Aplicar filtros de URL (Búsqueda y Filtros)
    q = request.GET.get('q')
    if q:
        participantes = participantes.filter(
            Q(nombres__icontains=q) | 
            Q(apellidos__icontains=q) | 
            Q(cedula__icontains=q)
        )

    estado_f = request.GET.get('estado')
    if estado_f and user_type != 'fed_regional':
        participantes = participantes.filter(estado_id=estado_f)

    sexo_f = request.GET.get('sexo')
    if sexo_f:
        participantes = participantes.filter(sexo=sexo_f)

    # 3. Lógica para Menores de Edad (Evitar el FieldError de 'edad')
    # Calculamos la fecha límite: hoy hace 18 años
    hoy = date.today()
    fecha_limite_menores = date(hoy.year - 18, hoy.month, hoy.day)

    # 4. Construcción del Contexto
    context = {
        'participantes': participantes.order_by('-fecha_registro'),
        'total_participantes': participantes.count(),
        'estados': Estado.objects.all().order_by('nombre'),
        
        # Estadísticas corregidas
        'participantes_hombres': participantes.filter(sexo='M').count(),
        'participantes_mujeres': participantes.filter(sexo='F').count(),
        
        # Filtramos por fecha_nacimiento (nacidos después de la fecha límite son menores)
        'menores_edad': participantes.filter(fecha_nacimiento__gt=fecha_limite_menores).count(),
        
        'es_central': user_type in ['fed_central', 'superuser'],
        'es_regional': user_type == 'fed_regional',
        'perfil': perfil,
    }
    return render(request, 'users/lista_participantes.html', context)

@admin_required
def admin_crear_institucion(request):
    if request.method == 'POST':
        form = InstitucionRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # 1. Creamos la institución y la marcamos ACTIVA de una vez
                institucion = form.save(commit=False)
                institucion.activa = True  # <--- Por ser Admin, va activa
                # ... (tu lógica de teléfono) ...
                institucion.save()

                # 2. Creamos el usuario activo
                user = User.objects.create_user(
                    username=institucion.codigo,
                    email=institucion.email,
                    password=form.cleaned_data['password'],
                    is_active=True # <--- ACTIVO inmediatamente
                )

                # 3. Vinculamos el perfil
                profile = user.userprofile
                profile.user_type = 'institucional'
                profile.institution = institucion
                profile.save()
                
            messages.success(request, "Institución creada y activada correctamente.")
            return redirect('lista_instituciones')



class ParticipanteUpdateView(UpdateView):
    # Modelo que se va a editar
    model = Participante
    
    # Formulario que se va a usar
    form_class = ParticipanteRegistrationForm 
    
    # Plantilla que mostrará el formulario
    template_name = 'users/participante_editar.html'
    
    # Define a dónde ir después de guardar los cambios
    def get_success_url(self):
        return reverse('dashboard')



@login_required
def estadisticas_por_estado(request):
    return render(request, "users/estadisticas_estados.html")


@institucional_required
def crear_evento(request):
    """
    Vista mejorada para crear eventos - Toma el estado de la institución por defecto
    """
    institution = request.user.userprofile.institution
    
    # Obtener el estado de la institución (si tiene)
    estado_institucion = institution.estado if hasattr(institution, 'estado') else None
    
    # Obtener listas para los selects
    estados = Estado.objects.all().order_by("nombre")
    hoy = date.today().isoformat()
    
    # Categorías predefinidas
    categorias = [
        'Competencia',
        'Taller',
        'Seminario',
        'Conferencia',
        'Exhibición',
        'Hackathon',
        'Feria',
        'Encuentro',
        'Capacitación',
        'Otro'
    ]
    
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        categoria = request.POST.get("categoria")
        fecha_str = request.POST.get("fecha")
        descripcion = request.POST.get("descripcion")
        modalidad = request.POST.get("modalidad", "presencial")
        ubicacion = request.POST.get("ubicacion", "")
        estado_id = request.POST.get("estado")
        municipio_id = request.POST.get("municipio")
        parroquia_id = request.POST.get("parroquia")
        direccion = request.POST.get("direccion", "")
        requisitos = request.POST.get("requisitos")
        estado_evento = request.POST.get("estado_evento", "abierto")
        
        # Validar que la fecha no sea anterior a hoy
        try:
            fecha_evento = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            if fecha_evento < date.today():
                messages.error(request, "❌ La fecha del evento no puede ser anterior a la fecha actual.")
                return render(request, "users/crear_evento.html", {
                    "estados": estados,
                    "hoy": hoy,
                    "categorias": categorias,
                    "estado_institucion": estado_institucion,
                    "valores_previos": request.POST
                })
        except ValueError:
            messages.error(request, "❌ Formato de fecha inválido.")
            return render(request, "users/crear_evento.html", {
                "estados": estados,
                "hoy": hoy,
                "categorias": categorias,
                "estado_institucion": estado_institucion,
                "valores_previos": request.POST
            })
        
        try:
            estado_obj = Estado.objects.get(id=estado_id) if estado_id else None
            municipio_obj = Municipio.objects.get(id=municipio_id) if municipio_id else None
            parroquia_obj = Parroquia.objects.get(id=parroquia_id) if parroquia_id else None
            
            # Construir ubicación completa
            ubicacion_completa = direccion
            if parroquia_obj:
                ubicacion_completa = f"{direccion}, {parroquia_obj.nombre}"
            elif municipio_obj:
                ubicacion_completa = f"{direccion}, {municipio_obj.nombre}"
            elif estado_obj:
                ubicacion_completa = f"{direccion}, {estado_obj.nombre}"
            
            evento = Evento.objects.create(
                nombre=nombre,
                tipo=categoria,  # Usamos el campo tipo para almacenar la categoría
                fecha=fecha_evento,
                descripcion=descripcion,
                modalidad=modalidad,
                ubicacion=ubicacion_completa,
                estado=estado_obj,
                municipio=municipio_obj,
                parroquia=parroquia_obj,
                direccion=direccion,
                requisitos=requisitos,
                institucion=institution,
                estado_evento=estado_evento,
                activo=True
            )
            
            messages.success(request, f"✅ Evento '{nombre}' creado exitosamente.")
            return redirect("gestionar_eventos_inst")
            
        except Exception as e:
            messages.error(request, f"❌ Error al crear el evento: {str(e)}")
            return render(request, "users/crear_evento.html", {
                "estados": estados,
                "hoy": hoy,
                "categorias": categorias,
                "estado_institucion": estado_institucion,
                "valores_previos": request.POST
            })
    
    # Valores por defecto para el formulario
    valores_default = {
        'estado_evento': 'abierto',
        'modalidad': 'presencial',
    }
    
    return render(request, "users/crear_evento.html", {
        "estados": estados,
        "hoy": hoy,
        "categorias": categorias,
        "estado_institucion": estado_institucion,
        "valores_default": valores_default
    })



@login_required
def eventos_disponibles(request):
    """
    Vista para mostrar eventos disponibles según el perfil del usuario
    """
    from django.utils import timezone
    from datetime import date
    
    hoy = date.today()
    
    # Obtener parámetros de filtro
    estado_filtro = request.GET.get('estado')
    tipo_filtro = request.GET.get('tipo')
    modalidad_filtro = request.GET.get('modalidad')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Query base: eventos activos, no cancelados
    eventos = Evento.objects.filter(
        activo=True,
        cancelado=False
    ).select_related('estado', 'municipio', 'parroquia', 'institucion')
    
    # Aplicar filtros
    if estado_filtro:
        eventos = eventos.filter(estado_id=estado_filtro)
    
    if tipo_filtro:
        eventos = eventos.filter(tipo=tipo_filtro)
    
    if modalidad_filtro:
        eventos = eventos.filter(modalidad=modalidad_filtro)
    
    if fecha_desde:
        eventos = eventos.filter(fecha__gte=fecha_desde)
    
    if fecha_hasta:
        eventos = eventos.filter(fecha__lte=fecha_hasta)
    
    # Separar eventos por estado (activos/hoy/pasados)
    eventos_activos = eventos.filter(fecha__gte=hoy, estado_evento='abierto').order_by('fecha')
    eventos_hoy = eventos.filter(fecha=hoy, estado_evento='abierto').order_by('fecha')
    eventos_proximos = eventos.filter(fecha__gt=hoy, estado_evento='abierto').order_by('fecha')
    eventos_pasados = eventos.filter(fecha__lt=hoy).order_by('-fecha')[:10]
    
    # Agrupar por estado geográfico
    estados_con_eventos = []
    for estado in Estado.objects.all().order_by('nombre'):
        eventos_estado = eventos_activos.filter(estado=estado)
        if eventos_estado.exists():
            estados_con_eventos.append({
                'estado': estado,
                'eventos': eventos_estado
            })
    
    # Estadísticas
    total_eventos = eventos.count()
    total_activos = eventos_activos.count()
    
    context = {
        'estados_con_eventos': estados_con_eventos,
        'eventos_activos': eventos_activos,
        'eventos_hoy': eventos_hoy,
        'eventos_proximos': eventos_proximos,
        'eventos_pasados': eventos_pasados,
        'total_eventos': total_eventos,
        'total_activos': total_activos,
        'hoy': hoy,
        'filtros': {
            'estado': estado_filtro,
            'tipo': tipo_filtro,
            'modalidad': modalidad_filtro,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        },
        'tipos': Evento.TIPO_CHOICES,
        'modalidades': Evento.MODALIDAD_CHOICES,
    }
    
    return render(request, "users/eventos_disponibles.html", context)

@login_required
@institucional_required
def gestionar_eventos_institucion(request):
    """
    Vista para que las instituciones gestionen sus eventos
    """
    institution = request.user.userprofile.institution
    hoy = date.today()
    
    # Filtros
    estado_filtro = request.GET.get('estado')
    tipo_filtro = request.GET.get('tipo')
    estado_evento_filtro = request.GET.get('estado_evento')
    
    eventos = Evento.objects.filter(institucion=institution).select_related('estado')
    
    if estado_filtro:
        eventos = eventos.filter(estado_id=estado_filtro)
    
    if tipo_filtro:
        eventos = eventos.filter(tipo=tipo_filtro)
    
    if estado_evento_filtro:
        eventos = eventos.filter(estado_evento=estado_evento_filtro)
    else:
        # Por defecto, mostrar todos excepto cancelados
        eventos = eventos.exclude(cancelado=True)
    
    # Obtener todos los grupos disponibles de la institución
    grupos_disponibles = Grupo.objects.filter(
        usuario_creador=request.user
    ).order_by('nombre')
    
    # Calcular total de inscripciones para las estadísticas
    total_inscripciones = 0
    for evento in eventos:
        # CORREGIDO: usar inscripciones_grupo en lugar de inscripciones
        total_inscripciones += evento.inscripciones_grupo.count()
    
    # Calcular eventos activos (próximas fechas)
    eventos_activos = eventos.filter(
        fecha__gte=hoy, 
        estado_evento='abierto', 
        cancelado=False
    ).count()
    
    # Estadísticas
    stats = {
        'total': eventos.count(),
        'activos': eventos.filter(estado_evento='abierto', fecha__gte=hoy, cancelado=False).count(),
        'pausados': eventos.filter(estado_evento='pausado', cancelado=False).count(),
        'cerrados': eventos.filter(estado_evento='cerrado', cancelado=False).count(),
        'finalizados': eventos.filter(estado_evento='finalizado', cancelado=False).count(),
        'cancelados': eventos.filter(cancelado=True).count(),
        'hoy': eventos.filter(fecha=hoy, cancelado=False).count(),
        'proximos': eventos.filter(fecha__gt=hoy, estado_evento='abierto', cancelado=False).count(),
    }
    
    context = {
        'eventos': eventos.order_by('-fecha'),
        'grupos_disponibles': grupos_disponibles,
        'total_inscripciones': total_inscripciones,
        'eventos_activos': eventos_activos,
        'stats': stats,
        'hoy': hoy,
        'estados': Estado.objects.all().order_by('nombre'),
        'tipos': Evento.TIPO_CHOICES,
        'estados_evento': Evento.ESTADO_CHOICES,
    }
    
    # Para depuración - imprime en la consola
    print(f"Total grupos encontrados: {grupos_disponibles.count()}")
    for grupo in grupos_disponibles:
        print(f"Grupo: {grupo.nombre} - ID: {grupo.id}")
    
    return render(request, 'users/gestionar_eventos.html', context)

@login_required
@institucional_required
def editar_evento(request, evento_id):
    """
    Vista para editar un evento existente con validacion de integridad
    """
    evento = get_object_or_404(
        Evento, 
        id=evento_id, 
        institucion=request.user.userprofile.institution
    )
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        
        # Validacion para evitar IntegrityError por campo nulo
        if not nombre:
            messages.error(request, "El nombre del evento es obligatorio.")
        else:
            evento.nombre = nombre
            evento.tipo = request.POST.get('tipo')
            evento.fecha = request.POST.get('fecha')
            evento.descripcion = request.POST.get('descripcion')
            evento.modalidad = request.POST.get('modalidad')
            evento.ubicacion = request.POST.get('ubicacion')
            evento.estado_id = request.POST.get('estado')
            evento.municipio_id = request.POST.get('municipio')
            evento.parroquia_id = request.POST.get('parroquia')
            evento.direccion = request.POST.get('direccion')
            
            # Manejo de capacidad maxima
            capacidad = request.POST.get('capacidad_maxima')
            if capacidad and capacidad.strip():
                evento.capacidad_maxima = capacidad
            else:
                evento.capacidad_maxima = None
                
            evento.requisitos = request.POST.get('requisitos')
            evento.estado_evento = request.POST.get('estado_evento')
            
            try:
                evento.save()
                messages.success(request, f"Evento '{evento.nombre}' actualizado correctamente.")
                return redirect('gestionar_eventos_inst')
            except Exception as e:
                messages.error(request, f"Error al guardar los cambios: {e}")
    
    # GET - Preparar datos para el formulario
    estados = Estado.objects.all().order_by('nombre')
    municipios = Municipio.objects.filter(estado=evento.estado) if evento.estado else []
    parroquias = Parroquia.objects.filter(municipio=evento.municipio) if evento.municipio else []
    
    context = {
        'evento': evento,
        'estados': estados,
        'municipios': municipios,
        'parroquias': parroquias,
        'tipos': Evento.TIPO_CHOICES,
        'modalidades': Evento.MODALIDAD_CHOICES,
        'estados_evento': Evento.ESTADO_CHOICES,
    }
    return render(request, 'users/editar_evento.html', context)

@login_required
@institucional_required
def cambiar_estado_evento(request, evento_id):
    """
    Vista para cambiar el estado de un evento (abierto/pausado/cerrado/finalizado)
    """
    if request.method == 'POST':
        evento = get_object_or_404(
            Evento, 
            id=evento_id, 
            institucion=request.user.userprofile.institution
        )
        
        nuevo_estado = request.POST.get('estado_evento')
        if nuevo_estado in dict(Evento.ESTADO_CHOICES).keys():
            evento.estado_evento = nuevo_estado
            evento.save()
            messages.success(request, f"✅ Estado del evento cambiado a '{evento.get_estado_evento_display()}'.")
        else:
            messages.error(request, "❌ Estado no válido.")
    
    return redirect('gestionar_eventos_inst')


@login_required
@institucional_required
def cancelar_evento(request, evento_id):
    """
    Vista para cancelar un evento
    """
    if request.method == 'POST':
        evento = get_object_or_404(
            Evento, 
            id=evento_id, 
            institucion=request.user.userprofile.institution
        )
        
        motivo = request.POST.get('motivo', '')
        
        if not evento.cancelado:
            evento.cancelado = True
            evento.activo = False
            evento.estado_evento = 'cerrado'
            evento.motivo_cancelacion = motivo
            evento.save()
            
            messages.warning(request, f"⚠️ Evento '{evento.nombre}' ha sido cancelado.")
        else:
            messages.info(request, f"ℹ️ El evento ya estaba cancelado.")
    
    return redirect('gestionar_eventos_inst')


@login_required
@institucional_required
def eliminar_evento(request, evento_id):
    """
    Vista para eliminar un evento (solo si no tiene inscritos)
    """
    if request.method == 'POST':
        evento = get_object_or_404(
            Evento, 
            id=evento_id, 
            institucion=request.user.userprofile.institution
        )
        
        # Verificar si tiene proyectos inscritos (asumiendo relación)
        if hasattr(evento, 'proyectos') and evento.proyectos.exists():
            messages.warning(request, "❌ No se puede eliminar el evento porque tiene proyectos inscritos.")
            return redirect('gestionar_eventos_inst')
        
        nombre_evento = evento.nombre
        evento.delete()
        messages.success(request, f"✅ Evento '{nombre_evento}' eliminado correctamente.")
    
    return redirect('gestionar_eventos_inst')


@login_required
def detalle_evento(request, evento_id):
    """
    Vista para ver detalles de un evento
    """
    evento = get_object_or_404(
        Evento.objects.select_related('estado', 'municipio', 'parroquia', 'institucion'),
        id=evento_id,
        activo=True
    )
    
    context = {
        'evento': evento,
        'puede_inscribirse': evento.puede_inscribirse if hasattr(evento, 'puede_inscribirse') else False,
    }
    return render(request, 'users/detalle_evento.html', context)


# ============================================
# VISTAS AJAX
# ============================================

def ajax_municipios_por_estado(request):
    """Vista AJAX para cargar municipios según el estado"""
    estado_id = request.GET.get('estado_id')
    if estado_id:
        municipios = Municipio.objects.filter(estado_id=estado_id).order_by('nombre').values('id', 'nombre')
        return JsonResponse(list(municipios), safe=False)
    return JsonResponse([], safe=False)


def ajax_parroquias_por_municipio(request):
    """Vista AJAX para cargar parroquias según el municipio"""
    municipio_id = request.GET.get('municipio_id')
    if municipio_id:
        parroquias = Parroquia.objects.filter(municipio_id=municipio_id).order_by('nombre').values('id', 'nombre')
        return JsonResponse(list(parroquias), safe=False)
    return JsonResponse([], safe=False)


@login_required
def inscripcion_evento_url(request, evento_id):
    # Aquí se renderiza el mismo formulario pero con su propia URL

    evento = get_object_or_404(Evento, id=evento_id)

    # Evitar doble inscripción
    if Inscripcion.objects.filter(evento=evento, lider=request.user).exists():
        messages.warning(request, 'Ya estás inscrita en este evento.')
        return redirect('eventos_disponibles')

    if request.method == 'POST':
        modalidad = request.POST.get('modalidad')
        nombre = request.POST.get('nombre_proyecto')
        descripcion = request.POST.get('descripcion')

        inscripcion = Inscripcion.objects.create(
            evento=evento,
            lider=request.user,
            modalidad=modalidad,
            nombre_proyecto=nombre,
            descripcion_proyecto=descripcion
        )

        if modalidad == 'equipo':
            integrantes_ids = request.POST.getlist('integrantes[]')
            for uid in integrantes_ids:
                if int(uid) != request.user.id:
                    IntegranteEquipo.objects.create(
                        inscripcion=inscripcion,
                        usuario_id=uid
                    )

        messages.success(request, 'Inscripción realizada correctamente')
        return redirect('eventos_disponibles')

    return render(request, 'registry/inscribirse_evento.html', {
        'evento': evento
    })

@login_required
def buscar_usuarios(request):
    q = request.GET.get('q', '').strip()[:50]  # Limitar longitud
    
    if len(q) < 2:  # Requerir mínimo 2 caracteres
        return JsonResponse([], safe=False)
    
    usuarios = User.objects.filter(
        username__icontains=q
    )[:10]

    data = [
        {
            "id": u.id,
            "username": u.username,
            "nombre": f"{u.first_name} {u.last_name}"
        }
        for u in usuarios
    ]

    return JsonResponse(data, safe=False)


from django.shortcuts import render, redirect

@login_required
def agregar_grupo(request):
    """Vista para agregar un grupo (prototipo con select estático)"""
    # Lista de participantes de ejemplo
    participantes = [
        {'id': 1, 'nombre': 'Juan Pérez'},
        {'id': 2, 'nombre': 'María Gómez'},
        {'id': 3, 'nombre': 'Luis Rodríguez'},
    ]
    
    if request.method == 'POST':
        nombre_grupo = request.POST.get('nombre_grupo')
        miembros_ids = request.POST.getlist('miembros')
        # Solo para el ejemplo: filtramos los nombres seleccionados
        miembros = [p['nombre'] for p in participantes if str(p['id']) in miembros_ids]
        
        # Guardamos en sesión temporal para el ejemplo
        grupos = request.session.get('grupos', [])
        grupos.append({'nombre': nombre_grupo, 'miembros': miembros})
        request.session['grupos'] = grupos
        
        return redirect('dashboard_participante')
    
    return render(request, 'users/agregar_grupo.html', {'participantes': participantes})


@login_required
def ver_grupo(request, nombre_grupo):
    """Vista para mostrar un grupo con miembros, representante y eventos (prototipo)"""
    # Tomamos los grupos guardados en sesión
    grupos = request.session.get('grupos', [])
    grupo = next((g for g in grupos if g['nombre'] == nombre_grupo), None)
    
    if not grupo:
        grupo = {'nombre': nombre_grupo, 'miembros': ['Juan Pérez', 'María Gómez']}
    
    # Datos de ejemplo
    representante = 'Juan Pérez'
    eventos = [
        'Competencia Regional de Robótica 2024',
        'Taller de Programación Avanzada'
    ]
    
    context = {
        'grupo': grupo,
        'representante': representante,
        'eventos': eventos
    }
    
    return render(request, 'users/ver_grupo.html', context)

# 1. ACTIVAR / VALIDAR
@login_required
@require_http_methods(["POST"])
def aprobar_institucion(request, institucion_id):
    perfil_admin = request.user.userprofile
    institucion = get_object_or_404(Institucion, id=institucion_id)
    
    # 1. SEGURIDAD: Validar si el administrador tiene competencia territorial
    # Un regional de Miranda no puede validar una sede de Carabobo.
    if perfil_admin.user_type == 'fed_regional' and institucion.estado != perfil_admin.estado:
        return JsonResponse({
            'status': 'error', 
            'message': f'No tienes permiso para validar sedes fuera de {perfil_admin.estado.nombre}.'
        }, status=403)

    try:
        with transaction.atomic():
            # 2. PROCESO DE ACTIVACIÓN
            # Guardamos si era temporal para saber si enviar correo después
            era_pendiente = (institucion.estatus == 'pendiente')
            
            institucion.activa = True
            institucion.estatus = 'aprobado'
            # Aquí, el método save() de tu modelo debería disparar la lógica del RNR
            institucion.save() 
            
            # 3. ACTIVACIÓN DE ACCESO (Django User)
            # Buscamos el usuario vinculado a esta institución
            perfil_inst = UserProfile.objects.filter(institution=institucion).first()
            
            if perfil_inst and perfil_inst.user:
                user = perfil_inst.user
                user.is_active = True
                
                # Sincronizamos el username con el nuevo código oficial (si cambió)
                if institucion.codigo:
                    user.username = institucion.codigo
                
                user.save()

                # 4. NOTIFICACIÓN (Opcional)
                if era_pendiente:
                    try:
                        # institucion.enviar_correo_bienvenida() 
                        pass
                    except:
                        pass

        # Respuesta para el Switch de JavaScript
        return JsonResponse({
            'status': 'success', 
            'message': f'Institución {institucion.nombre} validada con éxito.'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# 2. SUSPENDER / DESACTIVAR
@login_required
@require_http_methods(["POST"])
def desactivar_institucion(request, institucion_id):
    perfil_admin = request.user.userprofile
    inst = get_object_or_404(Institucion, id=institucion_id)

    # REGLA DE ORO: Validar territorio
    if perfil_admin.user_type == 'fed_regional' and inst.estado != perfil_admin.estado:
        return JsonResponse({'status': 'error', 'message': 'No tienes permiso sobre esta región.'}, status=403)

    try:
        with transaction.atomic():
            inst.activa = False
            inst.save()
            
            # Desactivar acceso de TODOS los usuarios vinculados a esa institución
            User.objects.filter(userprofile__institution=inst).update(is_active=False)
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        messages.warning(request, f'Acceso suspendido para: {inst.nombre}')
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return redirect('lista_instituciones')

# 3. GESTIONAR CREDENCIALES (Cambio de contraseña)
@admin_required
def gestionar_credenciales(request, institucion_id):
    inst = get_object_or_404(Institucion, id=institucion_id)
    usuario = inst.usuarios.first() # Suponiendo relación inversa
    if request.method == 'POST':
        nueva_pass = request.POST.get('password')
        usuario.set_password(nueva_pass)
        usuario.save()
        messages.success(request, 'Contraseña actualizada correctamente.')
        return redirect('lista_instituciones')
    return render(request, 'users/gestionar_credenciales.html', {'institucion': inst, 'usuario': usuario})

@admin_or_owner_required
def editar_institucion_modal(request, institucion_id):
    Institucion = apps.get_model('registry', 'Institucion')
    inst = get_object_or_404(Institucion, id=institucion_id)
    
    if request.method == 'POST':
        try:
            # 1. Actualización de datos de la Institución
            # Usamos or inst.nombre por si el campo llega vacío en el formulario
            inst.nombre = (request.POST.get('nombre') or inst.nombre).upper()
            inst.email = (request.POST.get('email') or inst.email).lower()
            inst.direccion = request.POST.get('direccion') or inst.direccion

            # RIF (Letra + Número)
            rif_letra = request.POST.get('rif_letra')
            rif_num = request.POST.get('rif_numero')
            if rif_letra and rif_num:
                inst.rif = f"{rif_letra}-{rif_num}"

            # Teléfono (Código + Número)
            cod_area = request.POST.get('modal_cod_area')
            num_puro = request.POST.get('modal_num_puro')
            if cod_area and num_puro:
                inst.telefono = f"{cod_area}{num_puro}"
            
            inst.save()
            print(f"[VISTA] Institución {inst.id} guardada exitosamente.")

            # 2. Sincronización con el Usuario de Django
            user_vinculado = User.objects.filter(username=inst.codigo).first()
            if user_vinculado:
                user_vinculado.email = inst.email
                
                nueva_clave = request.POST.get('new_password')
                confirm_clave = request.POST.get('confirm_password')

                if nueva_clave:
                    if nueva_clave == confirm_clave:
                        user_vinculado.set_password(nueva_clave)
                        messages.info(request, f'Contraseña de {user_vinculado.username} actualizada.')
                    else:
                        messages.warning(request, 'Sede guardada, pero las claves no coinciden.')
                
                user_vinculado.save()

            messages.success(request, f'Sede {inst.nombre} actualizada correctamente.')
            
        except Exception as e:
            print(f"[ERROR EN VISTA] {str(e)}")
            messages.error(request, f"Error al guardar: {str(e)}")
    
    return redirect('lista_instituciones')

# ELIMINAR 
@admin_required
@require_http_methods(["POST"])
def eliminar_institucion(request, institucion_id):
    """
    Mueve la institución a la papelera (eliminado=True) 
    y desactiva su estatus (activa=False).
    """
    # Buscamos la institución por el ID que viene de la URL
    institucion = get_object_or_404(Institucion, id=institucion_id) 
    
    if request.method == 'POST':
        # 1. Cambiamos los estados según lo solicitado
        institucion.eliminado = True
        institucion.activa = False  # <--- Aquí forzamos el estado inactivo
        
        # 2. Guardamos la fecha si el campo existe en tu modelo
        if hasattr(institucion, 'fecha_eliminacion'):
            institucion.fecha_eliminacion = timezone.now()
        
        institucion.save()
        
        # 3. Seguridad: Desactivamos el acceso de sus usuarios asociados
        # para que no puedan iniciar sesión mientras la sede esté "borrada"
        User.objects.filter(userprofile__institution=institucion).update(is_active=False)
        
        messages.warning(request, f"La institución '{institucion.nombre}' ha sido desactivada y movida a la papelera.")
        return redirect('lista_instituciones')
    
    return redirect('lista_instituciones')
def estadisticas_demografia(request):
    # Cálculos para las tarjetas KPI
    context = {
        'total_participantes': Participante.objects.count(),
        'total_instituciones': Institucion.objects.count(),
        'total_eventos': Evento.objects.count(),
        # Calculando porcentaje de mujeres
        'mujeres_count': Participante.objects.filter(genero='F').count(),
        # Datos para el gráfico de barras (Estados)
        'datos_estados': Institucion.objects.values('estado').annotate(total=Count('id')).order_size('total'),
    }
    return render(request, 'tu_app/estadisticas.html', context)

def mapa_interactivo(request):
    # 1. Creamos un diccionario de mapeo (Nombre en DB -> Código del Mapa)
    mapeo_codigos = {
        'Amazonas': 've-am', 'Anzoátegui': 've-an', 'Apure': 've-ap',
        'Aragua': 've-ar', 'Barinas': 've-ba', 'Bolívar': 've-bo',
        'Carabobo': 've-ca', 'Cojedes': 've-co', 'Delta Amacuro': 've-da',
        'Distrito Capital': 've-dc', 'Falcón': 've-fa', 'Guárico': 've-gu',
        'Lara': 've-la', 'Mérida': 've-me', 'Miranda': 've-mi',
        'Monagas': 've-mo', 'Nueva Esparta': 've-ne', 'Portuguesa': 've-po',
        'Sucre': 've-su', 'Táchira': 've-ta', 'Trujillo': 've-tr',
        'Vargas': 've-va', 'Yaracuy': 've-ya', 'Zulia': 've-zu'
    }

    # 2. Consultamos la base de datos agrupando por estado
    # Esto cuenta las instituciones por cada estado de una sola vez
    conteo_db = Institucion.objects.values('estado__nombre').annotate(total=Count('id'))

    # 3. Construimos el JSON que entiende el JavaScript
    mapa_data = {}
    for registro in conteo_db:
        nombre_estado = registro['estado__nombre']
        if nombre_estado in mapeo_codigos:
            codigo_mapa = mapeo_codigos[nombre_estado]
            mapa_data[codigo_mapa] = registro['total']

    return render(request, 'users/mapa_interactivo.html', {
        'mapa_data': mapa_data
    })

def dashboard_mapa(request):
    # Ejemplo de cómo agrupar instituciones por estado
    from django.db.models import Count
    # Asumiendo que tu modelo Institucion tiene un campo 'estado'
    conteo = Institucion.objects.values('estado').annotate(total=Count('id'))
    
    # Crear el diccionario: {'Miranda': 10, 'Zulia': 5...}
    mapa_data = {item['estado']: item['total'] for item in conteo}
    
    return render(request, 'tu_template.html', {'mapa_data': mapa_data})


@institucional_required
def detalle_evento_institucion(request, evento_id):
    """Ver quiénes están inscritos en un evento específico y gestionar"""
    evento = get_object_or_404(Evento, id=evento_id, institucion=request.user.userprofile.institution)
    
    # Supongamos que tienes un modelo Inscripcion que vincula al Evento
    inscripciones = evento.inscripcion_set.all().select_related('lider')

    return render(request, 'users/detalle_evento_gestion.html', {
        'evento': evento,
        'inscripciones': inscripciones
    })

@login_required
def ajax_dependencias(request):
    q = request.GET.get('q', '').strip()[:100]  # Limitar longitud
    queryset = Dependencia.objects.filter(activa=True).order_by('nombre')
    if q:
        queryset = queryset.filter(nombre__icontains=q)
    data = [{'id': d.id, 'nombre': d.nombre} for d in queryset[:30]]
    return JsonResponse(data, safe=False)


@login_required
def ajax_municipios(request):
    try:
        estado_id = int(request.GET.get('estado_id', 0))
        if estado_id <= 0:
            return JsonResponse([], safe=False)
        municipios = Municipios.objects.filter(id_estado_id=estado_id).order_by('municipio')
        data = [{'id': m.id_municipio, 'nombre': m.municipio} for m in municipios]
        return JsonResponse(data, safe=False)
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)
    
def lista_grupos_institucion(request):
    # Filtramos por la institución del usuario actual
    grupos = Grupo.objects.filter(institucion=request.user.institucion) 
    return render(request, 'users/ver_grupo.html', {'grupos': grupos})

@login_required
def mi_perfil(request):
    try:
        perfil = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Si no hay perfil, creamos uno básico de participante por seguridad
        perfil = UserProfile.objects.create(user=request.user, user_type='participante')

    # LÓGICA DE REDIRECCIÓN POR ROL
    if perfil.user_type in ['fed_central', 'fed_regional', 'superuser', 'tecnologico']:
        # Si el usuario es administrativo, usamos la vista de Federación
        return mi_perfil_federacion_logic(request, perfil)
    else:
        # Si es institucional o participante, podrías redirigir o mostrar otra
        return render(request, 'users/perfil_institucion.html', {'perfil': perfil})

def mi_perfil_federacion_logic(request, perfil):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        perfil.phone = request.POST.get('telefono')
        
        user.save()
        perfil.save()
        messages.success(request, "Perfil de Federación actualizado.")
        return redirect('mi_perfil')

    return render(request, 'users/perfil_federacion.html', {
        'perfil': perfil, 
        'user': user,
        'estados': Estado.objects.all()
    })

@login_required
def mi_perfil_institucional(request):
    usuario = request.user
    
    # Intentamos obtener la institución a través del perfil del usuario
    # Según tu error, 'userprofile' es una opción válida en Institucion
    institucion = Institucion.objects.filter(userprofile__user=usuario).first()
    
    # Si lo anterior falla, revisemos si la institución se busca por el email
    if not institucion:
        institucion = Institucion.objects.filter(email=usuario.email).first()

    context = {
        'usuario': usuario,
        'institucion': institucion,
        'fecha_unido': usuario.date_joined,
    }
    return render(request, 'users/mi_perfil.html', context)

@login_required
def mis_grupos(request):
    usuario = request.user

    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        # ============================================
        # ACCIÓN: ELIMINAR GRUPO
        # ============================================
        if accion == 'eliminar':
            try:
                grupo_id = request.POST.get('grupo_id')
                grupo = Grupo.objects.get(id=grupo_id, usuario_creador=usuario)
                
                with transaction.atomic():
                    # Eliminar relaciones de participantes primero (si es ManyToMany)
                    grupo.participantes.clear()
                    # Eliminar el grupo
                    grupo.delete()
                
                messages.success(request, "El escuadrón ha sido eliminado correctamente.")
                return redirect('mis_grupos')
                
            except Grupo.DoesNotExist:
                messages.error(request, "El grupo no existe o no tienes permiso para eliminarlo.")
                return redirect('mis_grupos')
            except Exception as e:
                print(f"DEBUG ERROR ELIMINAR: {str(e)}")
                messages.error(request, f"Error al eliminar: {e}")
                return redirect('mis_grupos')
        
        # ============================================
        # ACCIÓN: EDITAR GRUPO
        # ============================================
        elif accion == 'editar':
            try:
                grupo_id = request.POST.get('grupo_id')
                grupo = Grupo.objects.get(id=grupo_id, usuario_creador=usuario)
                
                with transaction.atomic():
                    # 1. Actualizar nombre del grupo
                    nuevo_nombre = request.POST.get('nombre_grupo')
                    if nuevo_nombre:
                        grupo.nombre = nuevo_nombre
                    
                    # 2. Mantener los datos del tutor (no se editan)
                    tutor_nombre = request.POST.get('tutor_nombre')
                    tutor_cedula = request.POST.get('tutor_cedula')
                    
                    if tutor_nombre:
                        grupo.tutor_nombre = tutor_nombre
                    if tutor_cedula:
                        grupo.tutor_cedula = tutor_cedula
                    
                    grupo.save()
                    
                    # 3. Procesar participantes a ELIMINAR
                    indices_eliminar = request.POST.getlist('eliminar_participante')
                    if indices_eliminar:
                        # Obtener lista de participantes actuales
                        participantes_actuales = list(grupo.participantes.all())
                        
                        # Eliminar por índice (basado en el orden actual)
                        for idx_str in indices_eliminar:
                            try:
                                idx = int(idx_str)
                                if idx < len(participantes_actuales):
                                    participante = participantes_actuales[idx]
                                    grupo.participantes.remove(participante)
                            except (ValueError, IndexError):
                                pass
                    
                    # 4. Procesar NUEVOS participantes
                    nuevas_cedulas = request.POST.getlist('nuevo_participante_cedula[]')
                    
                    for cedula in nuevas_cedulas:
                        if cedula.strip():
                            # Buscar si el participante ya existe
                            try:
                                participante = Participante.objects.get(cedula=cedula.strip())
                            except Participante.DoesNotExist:
                                # Si no existe, crear uno básico
                                participante = Participante.objects.create(
                                    cedula=cedula.strip(),
                                    nombre="Pendiente",
                                    apellido="Pendiente"
                                )
                            
                            # Agregar al grupo
                            grupo.participantes.add(participante)
                    
                    messages.success(request, f"El escuadrón '{grupo.nombre}' ha sido actualizado correctamente.")
                    return redirect('mis_grupos')
                    
            except Grupo.DoesNotExist:
                messages.error(request, "El grupo no existe o no tienes permiso para editarlo.")
                return redirect('mis_grupos')
            except Exception as e:
                print(f"DEBUG ERROR EDITAR: {str(e)}")
                messages.error(request, f"Error al editar: {e}")
                return redirect('mis_grupos')
        
        # ============================================
        # ACCIÓN: CREAR NUEVO GRUPO (código original)
        # ============================================
        else:
            # 1. Capturar datos básicos del grupo
            nombre_grupo = request.POST.get('nombre_grupo')
            tutor_cedula = request.POST.get('tutor_cedula')
            tutor_nombre = request.POST.get('tutor_nombre')
            tutor_telefono = request.POST.get('tutor_telefono')
            
            try:
                with transaction.atomic():
                    # --- LÓGICA DE HERENCIA DINÁMICA ---
                    # Si el usuario NO escribió el nombre del tutor, lo buscamos en los participantes
                    if not tutor_nombre:
                        # Buscamos en el diccionario POST cualquier clave que empiece con p_nombre_
                        clave_nombre = next((k for k in request.POST if k.startswith('p_nombre_')), None)
                        
                        if clave_nombre:
                            suffix = clave_nombre.split('_')[-1]
                            p_nom = request.POST.get(f'p_nombre_{suffix}', '')
                            p_ape = request.POST.get(f'p_apellido_{suffix}', '')
                            
                            tutor_nombre = f"{p_nom} {p_ape}".strip()
                            tutor_cedula = request.POST.get(f'p_cedula_{suffix}', tutor_cedula)
                            tutor_telefono = request.POST.get(f'p_telefono_{suffix}', tutor_telefono)
                    
                    # --- VALIDACIÓN DE EMERGENCIA ---
                    if not tutor_nombre:
                        tutor_nombre = f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username
                    if not tutor_cedula:
                        tutor_cedula = "0"

                    # 2. Crear el Grupo
                    nuevo_grupo = Grupo.objects.create(
                        nombre=nombre_grupo,
                        tutor_cedula=tutor_cedula,
                        tutor_nombre=tutor_nombre,
                        tutor_telefono=tutor_telefono or '',
                        usuario_creador=usuario
                    )

                    # 3. Procesar y asociar participantes (formato array)
                    cedulas_participantes = request.POST.getlist('participante_cedulas[]')
                    
                    for cedula in cedulas_participantes:
                        if cedula.strip():
                            # Buscar si el participante ya existe
                            try:
                                participante = Participante.objects.get(cedula=cedula.strip())
                            except Participante.DoesNotExist:
                                # Si no existe, crear uno básico
                                participante = Participante.objects.create(
                                    cedula=cedula.strip(),
                                    nombre="Pendiente",
                                    apellido="Pendiente"
                                )
                            
                            # Agregar al grupo
                            nuevo_grupo.participantes.add(participante)
                    
                    # 4. Procesar formato anterior con sufijos (por compatibilidad)
                    for key in request.POST:
                        if key.startswith('p_cedula_'):
                            suffix = key.split('_')[-1]
                            cedula = request.POST.get(f'p_cedula_{suffix}')
                            nombre = request.POST.get(f'p_nombre_{suffix}')
                            apellido = request.POST.get(f'p_apellido_{suffix}')
                            
                            if cedula:
                                try:
                                    participante = Participante.objects.get(cedula=cedula)
                                except Participante.DoesNotExist:
                                    # Crear con los datos proporcionados
                                    participante = Participante.objects.create(
                                        cedula=cedula,
                                        nombre=nombre or "Pendiente",
                                        apellido=apellido or "Pendiente",
                                        fecha_nacimiento=request.POST.get(f'p_fecha_{suffix}') or None,
                                    )
                                
                                nuevo_grupo.participantes.add(participante)

                    messages.success(request, f"¡El equipo '{nombre_grupo}' ha sido registrado!")
                    return redirect('mis_grupos')
                
            except Exception as e:
                print(f"DEBUG ERROR CREAR: {str(e)}")
                messages.error(request, f"Error al guardar: {e}")
                return redirect('mis_grupos')

    # ============================================
    # LÓGICA GET
    # ============================================
    grupos = Grupo.objects.filter(usuario_creador=usuario).order_by('-fecha_registro')
    
    # Calcular total de participantes
    total_participantes = 0
    for grupo in grupos:
        total_participantes += grupo.participantes.count()
    
    estados_venezuela = [
        'Amazonas', 'Anzoátegui', 'Apure', 'Aragua', 'Barinas', 'Bolívar', 
        'Carabobo', 'Cojedes', 'Delta Amacuro', 'Falcón', 'Guárico', 'Lara', 
        'Mérida', 'Miranda', 'Monagas', 'Nueva Esparta', 'Portuguesa', 'Sucre', 
        'Táchira', 'Trujillo', 'Vargas', 'Yaracuy', 'Zulia', 'Distrito Capital'
    ]

    context = {
        'grupos': grupos,
        'total_participantes': total_participantes,
        'estados': estados_venezuela,
    }
    return render(request, 'users/mis_grupos.html', context)

def obtener_datos_persona(request):
    """ API para buscar datos por cédula y autocompletar """
    cedula = request.GET.get('cedula')
    # Lógica para buscar en Participantes o Tutores existentes
    # data = { 'nombres': 'Juan', 'apellidos': 'Perez', ... }
    return JsonResponse({'status': 'success', 'data': {}})

@login_required
def dashboard_central(request):
    hoy = timezone.now().date()
    
    # KPIs Básicos
    total_participantes = Participante.objects.count()
    total_instituciones = Institution.objects.count() # Usando el nombre corregido
    total_eventos = Evento.objects.filter(fecha__gte=hoy).count()
    
    # Cobertura: Ajustado al nombre del campo que vimos en errores anteriores
    cobertura_nacional = Institution.objects.values('estado').distinct().count()

    # 1. Gráfica de Barras: Distribución de Instituciones por Estado
    stats_estados = Institution.objects.values('estado') \
        .annotate(total=Count('id')) \
        .order_by('-total')[:8]
    
    labels_estados = [item['estado'] for item in stats_estados]
    data_estados = [item['total'] for item in stats_estados]

    # 2. Gráfica de Línea: Crecimiento por mes
    # Usamos 'fecha_registro' si existe, si no, puedes usar 'id' para probar
    crecimiento_inst = Institution.objects.filter(fecha_registro__year=hoy.year) \
        .values('fecha_registro__month') \
        .annotate(total=Count('id')) \
        .order_by('fecha_registro__month')

    data_crecimiento = [0] * 12
    for item in crecimiento_inst:
        # Django a veces devuelve el mes en una llave diferente según la DB
        mes_num = item.get('fecha_registro__month')
        if mes_num:
            data_crecimiento[mes_num - 1] = item['total']

    # 3. Género
    porcentaje_mujeres = 0
    if total_participantes > 0:
        mujeres = Participante.objects.filter(genero='Femenino').count()
        porcentaje_mujeres = round((mujeres / total_participantes) * 100)

    context = {
        'total_participantes': total_participantes,
        'total_instituciones': total_instituciones,
        'total_eventos': total_eventos,
        'cobertura_nacional': cobertura_nacional,
        'labels_estados': labels_estados,
        'data_estados': data_estados,
        'data_crecimiento': data_crecimiento,
        'porcentaje_mujeres': porcentaje_mujeres,
        'pendientes_aprobacion': 0, 
    }
    return render(request, 'users/dashboard_central.html', context)


def registrar_club(request):
    if request.method == 'POST':
        form = ClubRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clubes')
    else:
        form = ClubRegistrationForm()
    
    return render(request, 'registrar_club.html', {'form': form})

@login_required
def registrar_sede(request):
    # Obtenemos el perfil del usuario logueado
    perfil_usuario = request.user.userprofile
    
    # Verificamos permisos de forma estricta
    is_admin_central = perfil_usuario.user_type == 'fed_central' or request.user.is_superuser
    
    if not is_admin_central:
        messages.error(request, "Acceso denegado: Se requiere nivel de Administración Central.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = SedeRegionalForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear el usuario
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['nombres'],
                        last_name=form.cleaned_data['apellidos']
                    )

                    # 2. Configurar perfil como Regional
                    profile = user.userprofile
                    profile.user_type = 'fed_regional'
                    profile.estado = form.cleaned_data['estado']
                    profile.cedula = form.cleaned_data['cedula']
                    profile.phone = f"{form.cleaned_data['codigo_area']}{form.cleaned_data['numero_telefono']}"
                    profile.save()

                    messages.success(request, f"¡Éxito! Nodo Regional {profile.estado.nombre} activado.")
                    return redirect('lista_instituciones')
            except Exception as e:
                messages.error(request, f"Error crítico: {str(e)}")
    else:
        form = SedeRegionalForm()

    # IMPORTANTE: Pasar las variables que base_dashboard.html necesita
    return render(request, 'users/registrar_sede.html', {
        'form': form,
        'es_central': is_admin_central,
        'perfil': perfil_usuario,
        'user_type': perfil_usuario.user_type
    })

@login_required
def gestionar_usuarios_sedes(request):
    if not request.user.is_superuser and request.user.userprofile.user_type != 'fed_central':
        return redirect('dashboard')

    sedes = UserProfile.objects.filter(user_type='fed_regional').select_related('user', 'estado')
    estados = Estado.objects.all()

    return render(request, 'users/gestionar_sedes.html', {
        'sedes': sedes,
        'estados': estados,
        'es_central': True
    })

@login_required
def mi_perfil_federacion(request):
    perfil = request.user.userprofile
    user = request.user
    
    if request.method == 'POST':
        # Procesar actualización de datos básicos
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        # Actualizar datos del perfil
        perfil.phone = request.POST.get('telefono')
        
        # Solo el superusuario o central puede cambiarse de estado
        if perfil.user_type in ['fed_central', 'superuser']:
            nuevo_estado_id = request.POST.get('estado')
            if nuevo_estado_id:
                perfil.estado = Estado.objects.get(id=nuevo_estado_id)
        
        user.save()
        perfil.save()
        
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect('mi_perfil_federacion')

    context = {
        'perfil': perfil,
        'user': user,
        'estados': Estado.objects.all(),
        # Para el menú lateral
        'es_central': perfil.user_type in ['fed_central', 'superuser'],
        'es_regional': perfil.user_type == 'fed_regional',
    }
    return render(request, 'users/perfil_federacion.html', context)

# Vista para eliminar (AJAX o POST directo)
@login_required
def eliminar_sede(request, user_id):
    if request.user.is_superuser or request.user.userprofile.user_type == 'fed_central':
        user_to_delete = get_object_or_404(User, id=user_id)
        nombre = user_to_delete.get_full_name()
        user_to_delete.delete()
        messages.success(request, f"La sede de {nombre} ha sido eliminada permanentemente.")
    return redirect('gestionar_sedes')

def participante_detail(request, pk):
    """Muestra el expediente detallado de un participante"""
    participante = get_object_or_404(Participante, pk=pk)
    return render(request, 'users/participante_detail.html', {'p': participante})

def participante_edit(request, pk):
    participante = get_object_or_404(Participante, pk=pk)
    if request.method == 'POST':
        form = ParticipanteModalEditForm(request.POST, instance=participante)
        if form.is_valid():
            form.save() # Aquí Django guarda automáticamente nombres, apellidos, etc.
            messages.success(request, "Datos actualizados correctamente.")
        else:
            # Esto te dirá en consola o pantalla exactamente qué campo falló
            for field, errors in form.errors.items():
                messages.error(request, f"Error en {field}: {errors.as_text()}")
    
    return redirect('lista_participantes')

def participante_delete(request, pk):
    """Elimina el registro mediante POST"""
    if request.method == 'POST':
        participante = get_object_or_404(Participante, pk=pk)
        nombre = f"{participante.nombres} {participante.apellidos}"
        participante.delete()
        messages.success(request, f"El registro de {nombre} ha sido eliminado.")
    return redirect('lista_participantes')

def load_parroquias(request):
    municipio_id = request.GET.get('municipio_id')
    # Validamos que llegue el ID para evitar errores
    if municipio_id:
        parroquias = Parroquia.objects.filter(municipio_id=municipio_id).order_by('nombre')
    else:
        parroquias = Parroquia.objects.none()
        
    # Retornamos los datos en formato JSON
    return JsonResponse(list(parroquias.values('id', 'nombre')), safe=False)

def api_buscar_participante(request, cedula):
    try:
        # Buscamos en el modelo Participante por la cédula
        p = Participante.objects.get(cedula=cedula)
        return JsonResponse({
            'encontrado': True,
            'id': p.id,
            'nombre': p.nombres,
            'apellido': p.apellidos,
            'edad': p.edad, # Usando la @property edad que definimos antes
        })
    except Participante.DoesNotExist:
        return JsonResponse({'encontrado': False})
    

    # ============================================
# VISTAS PARA ACCIONES DE EVENTOS (AGREGAR AL FINAL DE views.py)
# ============================================

@login_required
def editar_evento(request, evento_id):
    """
    Vista para editar un evento existente
    """
    try:
        # Verificar que el evento pertenezca a la institución del usuario
        evento = Evento.objects.get(
            id=evento_id, 
            institucion__usuario=request.user
        )
        
        if request.method == 'POST':
            # Actualizar datos del evento
            evento.nombre = request.POST.get('nombre')
            evento.descripcion = request.POST.get('descripcion')
            evento.fecha = request.POST.get('fecha')
            evento.estado_id = request.POST.get('estado')
            evento.municipio_id = request.POST.get('municipio')
            evento.parroquia_id = request.POST.get('parroquia')
            evento.direccion = request.POST.get('direccion')
            evento.capacidad_maxima = request.POST.get('capacidad_maxima') or None
            evento.requisitos = request.POST.get('requisitos')
            evento.save()
            
            messages.success(request, f"Evento '{evento.nombre}' actualizado correctamente.")
            return redirect('gestionar_eventos_inst')
        
        # GET - Mostrar formulario de edición
        estados = Estado.objects.all().order_by('nombre')
        
        # Obtener municipios y parroquias para el select
        municipios = Municipio.objects.filter(estado_id=evento.estado_id) if evento.estado_id else []
        parroquias = Parroquia.objects.filter(municipio_id=evento.municipio_id) if evento.municipio_id else []
        
        context = {
            'evento': evento,
            'estados': estados,
            'municipios': municipios,
            'parroquias': parroquias,
        }
        return render(request, 'users/editar_evento.html', context)
        
    except Evento.DoesNotExist:
        messages.error(request, "El evento no existe o no tienes permiso para editarlo.")
        return redirect('gestionar_eventos_inst')


@login_required
def eliminar_evento(request, evento_id):
    """
    Vista para eliminar un evento
    """
    if request.method == 'POST':
        try:
            evento = Evento.objects.get(
                id=evento_id, 
                institucion__usuario=request.user
            )
            
            # Verificar si tiene proyectos inscritos
            if evento.proyectos.exists():
                messages.warning(request, "No se puede eliminar el evento porque tiene proyectos inscritos.")
                return redirect('gestionar_eventos_inst')
            
            nombre_evento = evento.nombre
            evento.delete()
            messages.success(request, f"Evento '{nombre_evento}' eliminado correctamente.")
            
        except Evento.DoesNotExist:
            messages.error(request, "El evento no existe o no tienes permiso para eliminarlo.")
    
    return redirect('gestionar_eventos_inst')




# ============================================
# VISTA AUXILIAR PARA CARGAR MUNICIPIOS (AJAX)
# ============================================
def cargar_municipios_evento(request):
    """
    Vista AJAX para cargar municipios en el modal de edición
    """
    estado_id = request.GET.get('estado_id')
    if estado_id:
        municipios = Municipio.objects.filter(estado_id=estado_id).order_by('nombre').values('id', 'nombre')
        return JsonResponse(list(municipios), safe=False)
    return JsonResponse([], safe=False)


def cargar_parroquias_evento(request):
    """
    Vista AJAX para cargar parroquias en el modal de edición
    """
    municipio_id = request.GET.get('municipio_id')
    if municipio_id:
        parroquias = Parroquia.objects.filter(municipio_id=municipio_id).order_by('nombre').values('id', 'nombre')
        return JsonResponse(list(parroquias), safe=False)
    return JsonResponse([], safe=False)

@login_required
def detalle_evento_gestion(request, evento_id):
    """
    Vista para ver detalles del evento y gestionar inscritos
    """
    try:
        evento = Evento.objects.get(
            id=evento_id, 
            institucion__usuario=request.user
        )
        # CORREGIDO: usar inscripciones_grupo en lugar de proyectos
        inscripciones = evento.inscripciones_grupo.all().select_related('grupo')
        
        context = {
            'evento': evento,
            'inscripciones': inscripciones,
            'total_inscritos': inscripciones.count(),
        }
        return render(request, 'users/detalle_evento_gestion.html', context)
        
    except Evento.DoesNotExist:
        messages.error(request, "El evento no existe o no tienes permiso para verlo.")
        return redirect('gestionar_eventos_inst')