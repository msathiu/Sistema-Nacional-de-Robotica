from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required  
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse

from registry.models import Participante, Municipio, Institucion, Estado
from .models import UserProfile  
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
import random
import string
from django.views.generic.edit import UpdateView 
from django.urls import reverse

from registry.models import Evento
from django.db import transaction
from .forms import InstitucionRegistrationForm, CustomUserCreationForm, ParticipanteRegistrationForm
import pandas as pd
from django.contrib.admin.models import LogEntry

def home(request):
    """Página principal con opciones de login y registro"""
    return render(request, 'users/home.html')

def register(request):
    """Vista de registro de participante con redirección al Dashboard Institucional"""
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        participante_form = ParticipanteRegistrationForm(request.POST)
        
        if user_form.is_valid() and participante_form.is_valid():
            with transaction.atomic(): # Usamos atomic para asegurar que se creen ambos o ninguno
                # 1. Crear usuario
                user = user_form.save(commit=False)
                user.email = user_form.cleaned_data['email']
                user.save()
                
                # 2. Crear participante
                participante = participante_form.save(commit=False)
                participante.user = user
                participante.email = user.email
                
                # Opcional: Si quieres que el participante quede ligado a la institución 
                # que lo está registrando en ese momento:
                if request.user.is_authenticated and request.user.userprofile.user_type == 'institucional':
                    participante.institucion = request.user.userprofile.institution
                
                participante.save()
            
            messages.success(request, f'Participante {user.username} registrado exitosamente.')
            
            # 3. REDIRECCIÓN: 
            # Si quien registra es una institución, lo mandamos a su dashboard.
            # Si es un registro público (anonimo), lo mandamos al dashboard general.
            if request.user.is_authenticated and request.user.userprofile.user_type == 'institucional':
                return redirect('dashboard_institucional')
            
            # En caso de que sea un registro independiente:
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
    """Vista de login personalizada"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido de nuevo, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def dashboard(request):
    """Router principal del dashboard"""
    user_profile = request.user.userprofile

    if user_profile.user_type == 'participante':
        return redirect('dashboard_participante')

    elif user_profile.user_type == 'institucional':
        return redirect('dashboard_institucional')

    elif user_profile.user_type == 'admin':
        # --- NUEVA LÓGICA PARA EL MAPA ---
        # 1. Contamos instituciones por nombre de estado
        # Nota: Usamos 'estado__nombre' asumiendo que Institucion tiene una FK a Estado
        conteo_db = Institucion.objects.values('estado__nombre').annotate(total=Count('id'))
        
        # 2. Creamos el diccionario que el JavaScript necesita: {'Miranda': 5, 'Zulia': 2...}
        mapa_data = {registro['estado__nombre']: registro['total'] for registro in conteo_db}
        # ---------------------------------
        
        total_participantes = Participante.objects.count()
        total_instituciones = Institucion.objects.count()
        pendientes_aprobacion = Institucion.objects.filter(activa=False).count()
        cobertura_nacional = Institucion.objects.values('estado').distinct().count()
        total_eventos = Evento.objects.count()

        context = {
            'user': request.user,
            'user_profile': user_profile,
            'total_participantes': total_participantes,
            'total_instituciones': total_instituciones,
            'cobertura_nacional': cobertura_nacional,
            'total_eventos': total_eventos,
            'mapa_data': mapa_data,  # <--- AHORA SÍ TIENE DATOS
            'pendientes_aprobacion': pendientes_aprobacion,
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
    user_profile = request.user.userprofile
    if user_profile.user_type != 'institucional' or not user_profile.institution:
        return redirect('dashboard')

    institution = user_profile.institution

    # --- CÁLCULOS DINÁMICOS ---
    # 1. Participantes de esta institución
    total_mis_participantes = Participante.objects.filter(institucion=institution).count()
    
    # 2. Eventos creados por esta institución
    eventos_qs = Evento.objects.filter(institucion=institution)
    total_eventos = eventos_qs.count()
    
    # 3. Eventos activos (ejemplo: fecha mayor o igual a hoy)
    from django.utils import timezone
    total_activos = eventos_qs.filter(fecha__gte=timezone.now().date()).count()
    
    # 4. Certificados (asumiendo que tienes un modelo o lógica para esto)
    # Si no tienes modelo de certificados, puedes poner 0 o contar inscritos
    total_certificados = 0 # Sustituir por: Certificado.objects.filter(evento__institucion=institution).count()

    context = {
        'user_profile': user_profile,
        'institution': institution,
        'total_mis_participantes': total_mis_participantes,
        'total_eventos': total_eventos,
        'total_activos': total_activos,
        'total_certificados': total_certificados,
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
    """Vista para que el admin vea todas las instituciones con sus usuarios"""
    instituciones = Institucion.objects.all().select_related('estado').prefetch_related('userprofile_set__user').order_by('nombre')
    todas = Institucion.objects.all()
    # Estadísticas
    total_instituciones = todas.count()
    activas = todas.filter(activa=True).count()
    pendientes = todas.filter(activa=False).count()
    instituciones_activas = instituciones.filter(activa=True).count()
    estados = Estado.objects.all() # O Institucion.objects.values('estado__nombre').distinct()
    # Obtener usuarios institucionales para cada institución
    instituciones_con_usuarios = []
    for institucion in instituciones:
        usuarios_institucionales = User.objects.filter(
            userprofile__institution=institucion,
            userprofile__user_type='institucional'
        )
        instituciones_con_usuarios.append({
            'institucion': institucion,
            'usuarios': usuarios_institucionales
        })
    
    context = {
        'instituciones_con_usuarios': instituciones_con_usuarios,
        'total_instituciones': total_instituciones,
        'instituciones_activas': instituciones_activas,
        'instituciones_pendientes': pendientes,
        'estados': estados, # Esto evita que el filtro aparezca vacío
    }
    return render(request, 'users/lista_instituciones.html', context)




def registrar_institucion(request):
    if request.method == 'POST':
        form = InstitucionRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Creamos la institución (con activa=False por defecto en el modelo)
                    institucion = form.save(commit=False)
                    
                    # Unimos el teléfono (lo que ya tenías)
                    cod_area = form.cleaned_data.get('codigo_area')
                    num_tel = form.cleaned_data.get('numero_telefono')
                    institucion.telefono = f"{cod_area}{num_tel}"
                    
                    institucion.save() # Aquí se genera el código SNR

                    # 2. Creamos el usuario pero desactivado (is_active=False)
                    password = form.cleaned_data.get('password')
                    User.objects.create_user(
                        username=institucion.codigo,
                        email=institucion.email,
                        password=password,
                        is_active=False # Nadie entra hasta que la Federación autorice
                    )

                    # 3. NO REDIRIGIMOS, mostramos la pantalla de espera
                    return render(request, 'users/registro_pendiente.html', {
                        'nombre_inst': institucion.nombre,
                        'email': institucion.email
                    })

            except Exception as e:
                form.add_error(None, f"Error inesperado: {e}")
    else:
        form = InstitucionRegistrationForm()
    
    return render(request, 'users/registrar_institucion.html', {'form': form})

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

@login_required
def aprobar_institucion(request, institucion_id):
    # Solo permitimos que el admin realice esta acción
    if request.user.userprofile.user_type != 'admin':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('home')

    if request.method == 'POST':
        institucion = get_object_or_404(Institucion, id=institucion_id)
        institucion.activa = True
        institucion.save()
        
        messages.success(request, f'La institución {institucion.nombre} ha sido activada correctamente.')
    
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
    if request.method == 'POST':
        inst = get_object_or_404(Institucion, id=institucion_id)
        inst.activa = True
        inst.save()
        messages.success(request, f'¡{inst.nombre} ha sido activada!')
    return redirect('lista_instituciones')

# 2. SUSPENDER / DESACTIVAR
@login_required
def desactivar_institucion(request, institucion_id):
    if request.method == 'POST':
        inst = get_object_or_404(Institucion, id=institucion_id)
        inst.activa = False
        inst.save()
        messages.warning(request, f'La institución "{inst.nombre}" ha sido desactivada correctamente.')
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


# EDITAR INFORMACIÓN (MODAL)
@login_required
def editar_institucion_modal(request, institucion_id):
    if request.method == 'POST':
        inst = get_object_or_404(Institucion, id=institucion_id)
        inst.nombre = request.POST.get('nombre')
        inst.email = request.POST.get('email')
        inst.save()
        messages.success(request, f'Datos de {inst.nombre} actualizados.')
    return redirect('lista_instituciones')

# ELIMINAR TOTALMENTE
@login_required
def eliminar_institucion(request, institucion_id):
    if request.method == 'POST':
        inst = get_object_or_404(Institucion, id=institucion_id)
        nombre_cache = inst.nombre
        inst.delete() # Esto elimina la inst y los usuarios si usas on_delete=models.CASCADE
        messages.error(request, f'La institución "{nombre_cache}" ha sido eliminada permanentemente.')
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