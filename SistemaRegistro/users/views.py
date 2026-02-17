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
from .forms import InstitucionRegistrationForm, CustomUserCreationForm, ParticipanteRegistrationForm, ClubRegistrationForm, SedeRegionalForm
import pandas as pd
from django.contrib.admin.models import LogEntry
from django.utils import timezone
from .decorators import admin_required, institucional_required, owns_institution
from django.views.decorators.cache import never_cache
from django.db.models.functions import ExtractMonth
from datetime import datetime



def home(request):
    """Página principal con opciones de login y registro"""
    return render(request, 'users/home.html')

def register(request):
    """Vista de registro de participante con redirección al Dashboard Institucional"""
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        participante_form = ParticipanteRegistrationForm(request.POST)
        
        if user_form.is_valid() and participante_form.is_valid():
            with transaction.atomic():
                # 1. Crear usuario
                user = user_form.save(commit=False)
                user.email = user_form.cleaned_data['email']
                user.save()
                
                # 1.5 Crear perfil si no existe
                UserProfile.objects.get_or_create(user=user, defaults={'user_type': 'participante'})
                
                # 2. Crear participante
                participante = participante_form.save(commit=False)
                participante.user = user
                participante.email = user.email
                
                if request.user.is_authenticated and request.user.userprofile.user_type == 'institucional':
                    participante.institucion = request.user.userprofile.institution
                
                participante.save()
            
            messages.success(request, f'Participante {user.username} registrado exitosamente.')
            
            if request.user.is_authenticated and request.user.userprofile.user_type == 'institucional':
                return redirect('dashboard_institucional')
            
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        user_form = CustomUserCreationForm()
        participante_form = ParticipanteRegistrationForm()
    
    return render(request, 'users/register.html', {
        'user_form': user_form,
        'participante_form': participante_form,
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
    try:
        user_profile = request.user.userprofile
    except AttributeError:
        return redirect('dashboard')

    if user_profile.user_type != 'institucional' or not user_profile.institution:
        return redirect('dashboard')

    institution = user_profile.institution
    usuario = request.user
    hoy = timezone.now().date()

    # 1. Métricas de Grupos y Participantes
    mis_grupos = Grupo.objects.filter(usuario_creador=usuario)
    total_mis_grupos = mis_grupos.count()
    
    # Participantes de esta institución
    total_mis_participantes = Participante.objects.filter(institucion=institution).count()
    
    # 2. Métricas de Eventos (Campos confirmados: fecha, grupos_inscritos)
    total_eventos = Evento.objects.count()
    
    # Eventos futuros
    total_activos = Evento.objects.filter(fecha__gte=hoy).count()
    
    # CORRECCIÓN: Eventos donde mis grupos están inscritos
    # Usamos 'grupos_inscritos' que es el nombre que nos dio el error
    eventos_asignados = Evento.objects.filter(
        grupos_inscritos__usuario_creador=usuario
    ).distinct().count()

    # 3. Listas para las tablas
    proximos_eventos = Evento.objects.filter(fecha__gte=hoy).order_by('fecha')[:5]
    grupos_recientes = mis_grupos.order_by('-fecha_registro')[:3]

    context = {
        'user_profile': user_profile,
        'institution': institution,
        'total_mis_grupos': total_mis_grupos,
        'total_mis_participantes': total_mis_participantes,
        'total_eventos': total_eventos,
        'total_activos': total_activos,
        'eventos_asignados': eventos_asignados,
        'total_certificados': 0,
        'proximos_eventos': proximos_eventos,
        'grupos_recientes': grupos_recientes,
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
    
    # 1. Definir el Queryset base
    if user_type in ['fed_central', 'superuser', 'tecnologico']:
        participantes = Participante.objects.all()
    elif user_type == 'fed_regional':
        participantes = Participante.objects.filter(estado=perfil.estado)
    elif user_type == 'institucional':
        participantes = Participante.objects.filter(institucion=perfil.institution)
    else:
        return redirect('dashboard')

    # 2. Aplicar filtros de URL
    estado_f = request.GET.get('estado')
    if estado_f and user_type != 'fed_regional': # Regional no puede cambiar su estado
        participantes = participantes.filter(estado_id=estado_f)

    context = {
        'participantes': participantes,
        'total_participantes': participantes.count(),
        'estados': Estado.objects.all(),
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

    institution = request.user.userprofile.institution


    # Obtener lista de estados para el select
    from registry.models import Estado
    estados = Estado.objects.all().order_by("nombre")

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        fecha = request.POST.get("fecha")
        descripcion = request.POST.get("descripcion")
        estado_id = request.POST.get("estado")

        estado = Estado.objects.get(id=estado_id)

        Evento.objects.create(
            nombre=nombre,
            fecha=fecha,
            descripcion=descripcion,
            institucion=institution,
            estado=estado
        )
        return redirect("dashboard_institucional")

    return render(request, "users/crear_evento.html", {
        "estados": estados
    })

@login_required
def eventos_disponibles(request):
    from registry.models import Estado, Evento

    # Obtener todos los estados que tienen eventos
    estados = Estado.objects.all().order_by("nombre")

    estados_con_eventos = []

    for estado in estados:
        eventos_estado = Evento.objects.filter(estado=estado).order_by("fecha")
        if eventos_estado.exists():
            estados_con_eventos.append({
                "estado": estado,
                "eventos": eventos_estado
            })

    context = {
        "estados_con_eventos": estados_con_eventos
    }

    return render(request, "users/eventos_disponibles.html", context)


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


@owns_institution
@require_http_methods(["POST"])
def editar_institucion_modal(request, institucion_id):
    inst = get_object_or_404(Institucion, id=institucion_id)
    
    # 1. Intentamos localizar al usuario vinculado
    # Buscamos al usuario cuyo username sea igual al código SNR de la institución
    user = User.objects.filter(username=inst.codigo).first()

    # 2. Actualizar datos básicos de la Institución
    inst.nombre = request.POST.get('nombre', '').upper()
    inst.email = request.POST.get('email', '')
    inst.direccion = request.POST.get('direccion', '')

    # Reconstrucción del RIF desde el modal
    rif_letra = request.POST.get('rif_letra', '')
    rif_num = request.POST.get('rif_numero', '')
    if rif_letra and rif_num:
        inst.rif = f"{rif_letra}-{rif_num}"

    # Reconstrucción del Teléfono
    cod_area = request.POST.get('modal_cod_area', '')
    num_puro = request.POST.get('modal_num_puro', '')
    if cod_area and num_puro:
        inst.telefono = f"{cod_area}{num_puro}"
    
    # 3. Guardar cambios en la Institución
    try:
        inst.save()
        
        # 4. Si encontramos al usuario, actualizamos su clave y correo
        if user:
            # Actualizar email del usuario para que coincida con la institución
            user.email = inst.email
            
            nueva_clave = request.POST.get('new_password')
            confirm_clave = request.POST.get('confirm_password')

            if nueva_clave:
                if nueva_clave == confirm_clave:
                    # set_password encripta la clave correctamente
                    user.set_password(nueva_clave)
                    user.save()
                else:
                    messages.warning(request, f'La institución se actualizó, pero las contraseñas no coincidían.')
            else:
                # Si no hay clave nueva, solo guardamos el posible cambio de email
                user.save()

        messages.success(request, f'Sede {inst.nombre} actualizada correctamente.')
        
    except Exception as e:
        messages.error(request, f"Error al guardar los cambios: {e}")
        
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
def gestionar_eventos_institucion(request):
    """Lista todos los eventos creados por la institución actual"""
    
    institucion = request.user.userprofile.institution
    # Obtenemos eventos y contamos cuántos proyectos hay inscritos en cada uno
    eventos = Evento.objects.filter(institucion=institucion).annotate(
        total_inscritos=Count('inscripcion') 
    ).order_by('-fecha')

    return render(request, 'users/gestionar_eventos.html', {
        'eventos': eventos,
        'institucion': institucion
    })

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
        nombre_grupo = request.POST.get('nombre_grupo')
        tutor_cedula = request.POST.get('tutor_cedula')
        tutor_nombre = request.POST.get('tutor_nombre')
        tutor_telefono = request.POST.get('tutor_telefono')
        
        try:
            # 1. Crear el Grupo vinculado al usuario_creador
            nuevo_grupo = Grupo.objects.create(
                nombre=nombre_grupo,
                tutor_cedula=tutor_cedula,
                tutor_nombre=tutor_nombre,
                tutor_telefono=tutor_telefono,
                usuario_creador=usuario
            )

            # 2. Procesar participantes dinámicos
            for key in request.POST:
                if key.startswith('p_cedula_'):
                    suffix = key.split('_')[-1]
                    
                    Participante.objects.create(
                        grupo=nuevo_grupo,
                        cedula=request.POST.get(f'p_cedula_{suffix}'),
                        nombre=request.POST.get(f'p_nombre_{suffix}'),
                        apellido=request.POST.get(f'p_apellido_{suffix}'),
                        fecha_nacimiento=request.POST.get(f'p_fecha_{suffix}') or None,
                        # Si tu modelo tiene campo 'estado', puedes usar:
                        # estado=request.POST.get(f'p_estado_{suffix}')
                    )
            
            messages.success(request, f"¡El equipo '{nombre_grupo}' ha sido registrado!")
            return redirect('mis_grupos')
            
        except Exception as e:
            messages.error(request, f"Error al guardar: {e}")
            return redirect('mis_grupos')

    # Lógica GET
    grupos = Grupo.objects.filter(usuario_creador=usuario).order_by('-fecha_registro')
    
    # Lista manual para evitar el ImportError de 'Estado'
    estados_venezuela = [
        'Amazonas', 'Anzoátegui', 'Apure', 'Aragua', 'Barinas', 'Bolívar', 
        'Carabobo', 'Cojedes', 'Delta Amacuro', 'Falcón', 'Guárico', 'Lara', 
        'Mérida', 'Miranda', 'Monagas', 'Nueva Esparta', 'Portuguesa', 'Sucre', 
        'Táchira', 'Trujillo', 'Vargas', 'Yaracuy', 'Zulia', 'Distrito Capital'
    ]

    context = {
        'grupos': grupos,
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