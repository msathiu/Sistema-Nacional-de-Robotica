from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required  
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Estados, Municipios
from registry.models import (
    Club,
    Dependencia,
    Estado,
    Grupo,
    Institucion,
    Municipio,
    Participante,
)
from .models import UserProfile  
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
import random
import string
from django.views.generic.edit import UpdateView 
from django.urls import reverse
from registry.models import Evento
from django.db import transaction
from .forms import InstitucionRegistrationForm, CustomUserCreationForm, ParticipanteRegistrationForm, ClubRegistrationForm
import pandas as pd
from django.contrib.admin.models import LogEntry
from django.utils import timezone

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
    """Router principal del dashboard con estadísticas completas para Admin"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Manejo de seguridad para usuarios sin perfil (como superusers de consola)
        if request.user.is_superuser:
            user_type = 'admin'
        else:
            messages.error(request, 'No tienes un perfil configurado.')
            return redirect('login')
    else:
        user_type = user_profile.user_type

    if user_type == 'participante':
        return redirect('dashboard_participante')

    elif user_type == 'institucional':
        return redirect('dashboard_institucional')

    elif user_type == 'admin' or request.user.is_superuser:
        # 1. MÉTRICAS BÁSICAS (TARJETAS)
        total_participantes = Participante.objects.count()
        total_instituciones = Institucion.objects.count()
        total_clubes = Club.objects.count()
        total_eventos = Evento.objects.count()
        pendientes_aprobacion = Institucion.objects.filter(activa=False).count()
        cobertura_nacional = Institucion.objects.values('estado').distinct().count()
        
        # Conteo de Tutores (basado en cédulas únicas en la tabla Grupo)
        total_tutores = Grupo.objects.values('tutor_cedula').distinct().count()

        # 2. CURVA DE INSCRIPCIÓN MENSUAL (Instituciones)
        year_actual = datetime.now().year
        registros_por_mes = (
            Institucion.objects.filter(fecha_registro__year=year_actual)
            .annotate(mes=ExtractMonth('fecha_registro'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        data_crecimiento = [0] * 12
        for r in registros_por_mes:
            if r['mes']: data_crecimiento[r['mes'] - 1] = r['total']

        # 3. DISTRIBUCIÓN DE GÉNERO (Participantes)
        total_p = Participante.objects.count() or 1
        
        # Cambiamos 'genero' por 'sexo' que es el nombre real en tu BD
        mujeres = Participante.objects.filter(sexo='F').count() 
        hombres = Participante.objects.filter(sexo='M').count()
        
        porcentaje_mujeres = round((mujeres / total_p) * 100)
        porcentaje_hombres = round((hombres / total_p) * 100)

        # 4. ESPECIALIDADES DE CLUBES (Radar Chart)
        # Contamos cuántas veces aparece cada opción en linea_1 (puedes ampliarlo a las 3)
        clubes_stats = Club.objects.values('linea_1').annotate(total=Count('id')).order_by('-total')
        
        # Extraemos los nombres y los totales
        # Si el campo está vacío, ponemos 'General'
        clubes_labels = [c['linea_1'] if c['linea_1'] else 'General' for c in clubes_stats]
        clubes_data = [c['total'] for c in clubes_stats]

        # Si no hay datos, enviamos valores por defecto para que no rompa el JS
        if not clubes_labels:
            clubes_labels = ['Sin Líneas']
            clubes_data = [0]

        # 5. DISTRIBUCIÓN GEOGRÁFICA DE TUTORES (Bar Chart)
        # Obtenemos la ubicación de los tutores a través de los estados de sus participantes
        tutores_stats = (
            Participante.objects.values('estado__nombre')
            .annotate(total=Count('grupos__tutor_cedula', distinct=True))
            .order_by('-total')[:5]
        )
        
        tutores_labels = [t['estado__nombre'] for t in tutores_stats if t['estado__nombre']]
        tutores_data = [t['total'] for t in tutores_stats if t['estado__nombre']]

        # Fallback si no hay datos
        if not tutores_labels:
            tutores_labels = ['Sin Datos']
            tutores_data = [0]

        # 6. DATOS DEL MAPA (Existente)
        conteo_db = Institucion.objects.values('estado__nombre').annotate(total=Count('id'))
        mapa_data = {registro['estado__nombre']: registro['total'] for registro in conteo_db}

        context = {
            'user': request.user,
            'total_participantes': total_participantes,
            'total_instituciones': total_instituciones,
            'total_clubes': total_clubes,
            'total_tutores': total_tutores,
            'total_eventos': total_eventos,
            'pendientes_aprobacion': pendientes_aprobacion,
            'cobertura_nacional': cobertura_nacional,
            
            # Datos para Gráficas
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

    messages.error(request, 'Tipo de usuario no reconocido.')
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

@user_passes_test(is_admin)
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

@user_passes_test(is_admin)
def ver_logs_sistema(request):
    # Usamos LogEntry de Django para mostrar las últimas acciones del panel
    logs = LogEntry.objects.all().select_related('user', 'content_type')[:100]
    return render(request, 'users/logs_sistema.html', {'logs': logs})

def create_institutional_user(request):
    """Redirige al formulario unificado de institución"""
    messages.info(request, 'Ahora el registro de instituciones incluye la creación de usuarios automáticamente.')
    return redirect('registrar_institucion')

@login_required
@user_passes_test(is_admin)
def lista_instituciones(request):
    """Vista para que el admin vea todas las instituciones con sus usuarios (sin las eliminadas)"""
    
    # 1. Filtramos la base principal: Solo lo que NO está eliminado
    # Usamos select_related para traer el estado de una vez y mejorar el rendimiento
    instituciones_base = Institucion.objects.filter(eliminado=False).select_related('estado').order_by('nombre')
    
    # 2. Estadísticas (KPIs) basadas solo en las instituciones NO eliminadas
    total_instituciones = instituciones_base.count()
    instituciones_activas = instituciones_base.filter(activa=True).count() # Corregido el nombre
    instituciones_pendientes = instituciones_base.filter(activa=False).count()
    
    # 3. Datos para los filtros de la vista
    estados = Estado.objects.all()

    # 4. Construcción de la lista con usuarios
    instituciones_con_usuarios = []
    for institucion in instituciones_base:
        # Filtramos los usuarios asociados a esta institución específica
        usuarios_institucionales = User.objects.filter(
            userprofile__institution=institucion,
            userprofile__user_type='institucional'
        )
        
        instituciones_con_usuarios.append({
            'institucion': institucion,
            'usuarios': usuarios_institucionales
        })
    
    # 5. Contexto (Asegúrate de que los nombres coincidan con tu HTML)
    context = {
        'instituciones_con_usuarios': instituciones_con_usuarios,
        'total_instituciones': total_instituciones,
        'instituciones_activas': instituciones_activas,       # Variable ya definida arriba
        'instituciones_pendientes': instituciones_pendientes, # Variable ya definida arriba
        'estados': estados,
    }
    
    return render(request, 'users/lista_instituciones.html', context)



def registrar_institucion(request):
    # Detectar si el usuario es un administrador de la FVRN
    es_administrador = (
        request.user.is_authenticated and 
        hasattr(request.user, 'userprofile') and 
        request.user.userprofile.user_type == 'admin'
    )

    # Definir el template base dinámicamente
    if es_administrador:
        base_template = 'users/base_dashboard.html'
    else:
        base_template = 'base.html'

    if request.method == 'POST':
        form = InstitucionRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar la institución (sin commit para procesar datos)
                    institucion = form.save(commit=False)
                    
                    # Si registra el admin, se aprueba de una vez
                    if es_administrador:
                        institucion.activa = True
                        institucion.estatus = 'aprobado'
                    else:
                        institucion.activa = False
                        institucion.estatus = 'pendiente'
                    
                    institucion.save()

                    # 2. Crear el Usuario asociado
                    # El username inicial es el código generado (RNR...) o el email si aún no tiene código
                    password = form.cleaned_data.get('password')
                    nuevo_usuario = User.objects.create_user(
                        username=institucion.codigo if institucion.codigo else institucion.email,
                        email=institucion.email,
                        password=password,
                        # El usuario solo puede loguear si el admin lo registró o si ya fue activado
                        is_active=True if es_administrador else False,
                    )

                    # 3. Vincular usuario e institución
                    institucion.usuario = nuevo_usuario
                    institucion.save(update_fields=['usuario'])

                    # 4. Crear Perfil de Usuario con rol institucional
                    profile, created = UserProfile.objects.get_or_create(user=nuevo_usuario)
                    profile.user_type = 'institucional'
                    profile.institution = institucion
                    profile.save()

                    # --- REDIRECCIONES SEGÚN EL ROL ---
                    if es_administrador:
                        messages.success(request, f"La sede '{institucion.nombre}' ha sido registrada y activada correctamente.")
                        return redirect('lista_instituciones')
                    else:
                        # Usuario común va a la página de espera
                        return render(request, 'users/registro_pendiente.html', {
                            'nombre_inst': institucion.nombre,
                            'email': institucion.email,
                            'base_template': base_template
                        })

            except Exception as e:
                messages.error(request, f"Ocurrió un error inesperado: {str(e)}")
    else:
        form = InstitucionRegistrationForm()

    # Se ejecuta si es GET o si el formulario falló (POST con errores)
    return render(request, 'users/registrar_institucion.html', { 
        'form': form,
        'base_template': base_template,
        'dependencias': Dependencia.objects.all()
    })

@login_required
@login_required
def lista_participantes(request):
    """Vista inteligente: Admin ve todo, Institución ve lo suyo"""
    user_profile = request.user.userprofile
    
    # 1. Definir el Queryset base según el rol
    if user_profile.user_type == 'admin':
        participantes = Participante.objects.all()
    elif user_profile.user_type == 'institucional':
        # Filtro estricto: Solo lo que pertenece a su institución vinculada
        participantes = Participante.objects.filter(institucion=user_profile.institution)
    else:
        # Si un participante intenta entrar aquí, lo sacamos
        messages.error(request, "No tienes permiso para ver este listado.")
        return redirect('dashboard')

    # 2. Aplicar filtros comunes (esto sirve para AMBOS)
    estado_filter = request.GET.get('estado')
    sexo_filter = request.GET.get('sexo')

    if estado_filter:
        participantes = participantes.filter(estado_id=estado_filter)
    if sexo_filter:
        participantes = participantes.filter(sexo=sexo_filter)

    # 3. Datos para los selectores del template
    estados = Estado.objects.all().order_by('nombre')
    
    context = {
        'participantes': participantes,
        'total_participantes': participantes.count(),
        'estados': estados,
        'is_admin': user_profile.user_type == 'admin', # Para mostrar/ocultar botones en el HTML
    }
    
    return render(request, 'users/lista_participantes.html', context)

@login_required
@user_passes_test(is_admin)
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

@login_required
def crear_evento(request):
    if request.user.userprofile.user_type != "institucional":

        return redirect("dashboard")

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

def buscar_usuarios(request):
    q = request.GET.get('q', '')

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
def aprobar_institucion(request, institucion_id):
    # Solo permitimos que el admin realice esta acción
    if request.user.userprofile.user_type != 'admin':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('home')

    if request.method == 'POST':
        with transaction.atomic(): # Usamos atomic para que se activen los dos o ninguno
            institucion = get_object_or_404(Institucion, id=institucion_id)
            
            # 1. Activamos la institución (tu modelo)
            institucion.activa = True
            institucion.estatus = 'aprobado'
            institucion.save()
            
            # 2. Activamos el usuario de Django (la cuenta de acceso)
            # Buscamos el usuario asociado a través del UserProfile
            perfil = UserProfile.objects.filter(institution=institucion).select_related('user').first()
            if perfil and perfil.user:
                perfil.user.is_active = True # <--- ESTO ES LO QUE FALTABA
                perfil.user.username = institucion.codigo
                perfil.user.save()
                messages.success(request, f'La cuenta de {institucion.nombre} ha sido activada correctamente.')
            else:
                messages.warning(request, f'Institución activada, pero no se encontró un usuario vinculado.')
    
    return redirect('lista_instituciones')

# 2. SUSPENDER / DESACTIVAR
@login_required
def desactivar_institucion(request, institucion_id):
    if request.method == 'POST':
        with transaction.atomic():
            inst = get_object_or_404(Institucion, id=institucion_id)
            
            # 1. Desactivamos institución
            inst.activa = False
            inst.save()
            
            # 2. Desactivamos usuario de Django
            perfil = UserProfile.objects.filter(institution=inst).first()
            if perfil and perfil.user:
                perfil.user.is_active = False # <--- BLOQUEA EL LOGIN
                perfil.user.save()
            
            messages.warning(request, f'La institución "{inst.nombre}" y su acceso han sido suspendidos.')
    return redirect('lista_instituciones')

# 3. GESTIONAR CREDENCIALES (Cambio de contraseña)
@login_required
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


@login_required
def editar_institucion_modal(request, institucion_id):
    if request.method == 'POST':
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
@login_required
@user_passes_test(is_admin)
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

@login_required
def gestionar_eventos_institucion(request):
    """Lista todos los eventos creados por la institución actual"""
    if request.user.userprofile.user_type != 'institucional':
        return redirect('dashboard')
    
    institucion = request.user.userprofile.institution
    # Obtenemos eventos y contamos cuántos proyectos hay inscritos en cada uno
    eventos = Evento.objects.filter(institucion=institucion).annotate(
        total_inscritos=Count('inscripcion') 
    ).order_by('-fecha')

    return render(request, 'users/gestionar_eventos.html', {
        'eventos': eventos,
        'institucion': institucion
    })

@login_required
def detalle_evento_institucion(request, evento_id):
    """Ver quiénes están inscritos en un evento específico y gestionar"""
    evento = get_object_or_404(Evento, id=evento_id, institucion=request.user.userprofile.institution)
    
    # Supongamos que tienes un modelo Inscripcion que vincula al Evento
    inscripciones = evento.inscripcion_set.all().select_related('lider')

    return render(request, 'users/detalle_evento_gestion.html', {
        'evento': evento,
        'inscripciones': inscripciones
    })

def ajax_dependencias(request):
    q = request.GET.get('q', '').strip()
    queryset = Dependencia.objects.filter(activa=True).order_by('nombre')
    if q:
        queryset = queryset.filter(nombre__icontains=q)
    data = [{'id': d.id, 'nombre': d.nombre} for d in queryset[:30]]
    return JsonResponse(data, safe=False)


def ajax_municipios(request):
    estado_id = request.GET.get('estado_id')
    # Filtramos los municipios por el ID del estado seleccionado
    municipios = Municipios.objects.filter(id_estado_id=estado_id).order_by('municipio')
    data = [{'id': m.id_municipio, 'nombre': m.municipio} for m in municipios]
    return JsonResponse(data, safe=False)
    
def lista_grupos_institucion(request):
    # Filtramos por la institución del usuario actual
    grupos = Grupo.objects.filter(institucion=request.user.institucion) 
    return render(request, 'users/ver_grupo.html', {'grupos': grupos})

@login_required
def mi_perfil(request):
    # Obtenemos datos básicos del usuario
    usuario = request.user
    
    # Si es una institución, podemos contar sus recursos para el resumen
    context = {
        'usuario': usuario,
        'fecha_unido': usuario.date_joined,
    }
    
    return render(request, 'users/mi_perfil.html', context)

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
            return redirect('lista_clubes') # Cambia esto a tu URL de éxito
    else:
        form = ClubRegistrationForm()
    
    return render(request, 'registrar_club.html', {'form': form})

