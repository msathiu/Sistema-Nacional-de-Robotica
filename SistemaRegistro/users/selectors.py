from django.db.models import Q, Count
from django.contrib.auth.models import User
from registry.models import Evento, Club, MembresiaClu, EstadoEvento, Participante, Institucion

class JurisdictionSelector:
    """
    Centraliza la lógica de roles y jurisdicción territorial del sistema.
    """
    ROLES_RECTORES = ["fed_central", "superuser", "tecnologico"]
    ROLES_FEDERACION = ["fed_central", "fed_regional", "superuser", "tecnologico"]

    @staticmethod
    def es_rector(perfil):
        return getattr(perfil, "user_type", None) in JurisdictionSelector.ROLES_RECTORES

    @staticmethod
    def es_federacion(perfil):
        return getattr(perfil, "user_type", None) in JurisdictionSelector.ROLES_FEDERACION

    @staticmethod
    def filtrar_por_territorio(queryset, perfil, campo_estado="estado", campo_institucion="institucion"):
        """
        Aplica filtros territoriales genéricos a un queryset basado en el perfil del usuario.
        """
        user_type = getattr(perfil, "user_type", None)
        
        if user_type in JurisdictionSelector.ROLES_RECTORES:
            return queryset
            
        if user_type == "fed_regional" and perfil.estado:
            return queryset.filter(**{campo_estado: perfil.estado})
            
        if user_type == "institucional" and perfil.institution:
            return queryset.filter(**{campo_institucion: perfil.institution})
            
        return queryset.none()


class EventoSelector:
    """
    Clase para manejar la lógica de consulta (read) de eventos.
    """
    
    ESTADOS_EVENTO_PUBLICABLES = [
        EstadoEvento.ABIERTO,
        EstadoEvento.PAUSADO,
        EstadoEvento.EN_PROCESO,
        EstadoEvento.FINALIZADO,
    ]

    @staticmethod
    def es_rector_eventos(perfil):
        return JurisdictionSelector.es_rector(perfil)

    @staticmethod
    def es_usuario_federacion_eventos(perfil):
        return JurisdictionSelector.es_federacion(perfil)

    @staticmethod
    def get_estado_contexto(perfil, institucion=None):
        if JurisdictionSelector.es_federacion(perfil):
            return getattr(perfil, "estado", None)
        if institucion and hasattr(institucion, "estado"):
            return institucion.estado
        return None

    @staticmethod
    def get_clubes_disponibles_para_formulario(perfil):
        user_type = getattr(perfil, "user_type", None)
        institution = getattr(perfil, "institution", None)

        if user_type == "institucional" and institution:
            # Clubes donde la institución es creadora
            clubes_creados = Club.objects.filter(
                institucion_creadora=institution,
                status="aprobado",
                activo=True,
            )
            # Clubes donde la institución es miembro activo
            clubes_miembro = Club.objects.filter(
                membresias__institucion=institution,
                membresias__estado="miembro_activo",
                status="aprobado",
                activo=True,
            )
            # Unir ambos querysets sin duplicados
            return (clubes_creados | clubes_miembro).distinct().select_related("institucion_creadora")

        if user_type == "fed_central":
            # fed_central puede crear eventos para cualquier club aprobado (ente rector)
            return Club.objects.filter(
                status="aprobado",
                eliminado=False,
            ).select_related("institucion_creadora").order_by("nombre")

        if JurisdictionSelector.es_federacion(perfil):
            return Club.objects.filter(
                status="aprobado",
                activo=True,
            ).select_related("institucion_creadora")

        return Club.objects.none()

    @staticmethod
    def get_eventos_visibles(user_or_perfil):
        """
        Retorna los eventos visibles para el catálogo general según rol,
        territorio y audiencia.

        Compatibilidad:
        - acepta `UserProfile`
        - acepta `User` con atributo `userprofile`

        Criterios aplicados:
        - solo estados publicables
        - solo eventos activos y no cancelados
        - `fed_central`/roles rectores: ven todo lo publicable
        - `fed_regional`: solo eventos publicables de su territorio
        - `institucional`: respeta audiencia, membresía y excluye eventos propios
        """
        perfil = getattr(user_or_perfil, "userprofile", user_or_perfil)
        user_type = getattr(perfil, "user_type", None)
        institucion = getattr(perfil, "institution", None)
        estado_perfil = getattr(perfil, "estado", None)

        eventos_base = Evento.objects.filter(
            estado_evento__in=EventoSelector.ESTADOS_EVENTO_PUBLICABLES,
            activo=True,
            cancelado=False,
        ).select_related(
            "estado",
            "municipio",
            "parroquia",
            "institucion",
            "club_organizador",
            "club_organizador__institucion_creadora",
            "creado_por",
        )

        # fed_central, superuser y tecnologico ven todo lo publicable.
        if JurisdictionSelector.es_rector(perfil):
            # Para vista administrativa, incluir todos los eventos (activos, pausados, cancelados)
            # Usar queryset completo sin filtro de eventos_base
            eventos_admin = Evento.objects.select_related(
                "estado", "municipio", "parroquia", "institucion", "club_organizador",
                "club_organizador__institucion_creadora",
                "creado_por",
            ).filter(Q(activo=True) | Q(cancelado=True))
            return eventos_admin.distinct()

        # fed_regional solo ve eventos publicables de su territorio.
        if user_type == "fed_regional":
            if not estado_perfil:
                return eventos_base.none()
            return eventos_base.filter(estado=estado_perfil).distinct()

        # Instituciones: audiencia estricta + membresía + exclusión de eventos propios.
        if user_type == "institucional":
            if not institucion:
                return eventos_base.none()

            clubes_miembro_ids = EventoSelector.get_clubes_miembro_activo(institucion)

            eventos_visibles = eventos_base.filter(
                Q(audiencia="publica")
                | Q(audiencia="institucional_privado", institucion=institucion)
                | Q(audiencia="club_exclusivo", club_organizador_id__in=clubes_miembro_ids)
            )

            # El catálogo institucional no debe incluir eventos propios:
            # - eventos institucionales de esta institución
            # - eventos de club creados por un usuario de esta institución
            eventos_visibles = eventos_visibles.exclude(
                Q(institucion=institucion)
                | Q(club_organizador__isnull=False, creado_por__userprofile__institution=institucion)
            )

            return eventos_visibles.distinct()

        # Cualquier otro perfil no autorizado no ve eventos en este catálogo.
        return eventos_base.none()

    @staticmethod
    def get_clubes_miembro_activo(institucion):
        if not institucion:
            return MembresiaClu.objects.none().values_list("club_id", flat=True)
        return MembresiaClu.objects.filter(
            institucion=institucion,
            estado="miembro_activo",
        ).values_list("club_id", flat=True)


class EventoActionSelector:
    """
    Centraliza la lógica de acciones disponibles por rol y estado del evento.
    Basado en la matriz de acciones de EVENTO.md.
    """

    @staticmethod
    def es_evento_propio(evento, perfil):
        """
        Determina si el evento pertenece a la institución del usuario.
        Soporta: evento institucional directo, club creado por la institución,
        o club donde la institución es miembro activo.
        """
        if not perfil:
            return False
        user_type = getattr(perfil, "user_type", None)
        institution = getattr(perfil, "institution", None)

        if not institution or user_type != "institucional":
            return False

        # Evento institucional directo
        if evento.institucion == institution:
            return True

        # Evento de club
        if evento.club_organizador:
            # Creador del club
            if evento.club_organizador.institucion_creadora == institution:
                return True
            # Miembro activo — usar caché del perfil si está disponible (evita N+1)
            clubes_ids = getattr(perfil, "_clubes_miembro_ids", None)
            if clubes_ids is not None:
                return evento.club_organizador_id in clubes_ids
            # Fallback: query directa (cuando se llama fuera del contexto de la view)
            from registry.models import MembresiaClu
            return MembresiaClu.objects.filter(
                club=evento.club_organizador,
                institucion=institution,
                estado="miembro_activo",
            ).exists()

        return False

    @staticmethod
    def get_acciones_evento(evento, perfil, vista="mis_eventos"):
        """
        Retorna un diccionario con las acciones disponibles para el evento según el perfil del usuario.
        
        Args:
            evento: Instancia del modelo Evento
            perfil: UserProfile del usuario actual
            vista: Vista desde la que se consulta ('mis_eventos', 'eventos', 'admin')
            
        Returns:
            dict con claves: editar, enviar_revision, reenviar, eliminar, cancelar, 
                           aprobar, rechazar, pausar, reanudar, ver, inscribir
        """
        user_type = getattr(perfil, "user_type", None)
        institution = getattr(perfil, "institution", None)
        es_rector = JurisdictionSelector.es_rector(perfil)
        es_federacion = JurisdictionSelector.es_federacion(perfil)
        
        estado = evento.estado_evento
        es_propio = EventoActionSelector.es_evento_propio(evento, perfil)
        
        acciones = {
            "editar": False,
            "enviar_revision": False,
            "reenviar": False,
            "eliminar": False,
            "cancelar": False,
            "aprobar": False,
            "rechazar": False,
            "pausar": False,
            "reanudar": False,
            "ver": True,
            "inscribir": False,
        }
        
        if user_type == "institucional":
            if vista == "mis_eventos":
                if estado == EstadoEvento.BORRADOR and es_propio:
                    acciones["editar"] = True
                    acciones["enviar_revision"] = True
                    acciones["eliminar"] = True
                    acciones["cancelar"] = True
                elif estado == EstadoEvento.RECHAZADO and es_propio:
                    acciones["editar"] = True
                    acciones["reenviar"] = True
                    acciones["eliminar"] = True
                elif estado == EstadoEvento.REVISION and es_propio:
                    acciones["ver"] = True
                elif estado in [EstadoEvento.ABIERTO, EstadoEvento.PAUSADO, EstadoEvento.EN_PROCESO] and es_propio:
                    acciones["ver"] = True
                    acciones["cancelar"] = True
                    if estado == EstadoEvento.ABIERTO:
                        acciones["inscribir"] = True
                elif estado == EstadoEvento.ABIERTO and not es_propio:
                    acciones["inscribir"] = True
                elif estado in [EstadoEvento.FINALIZADO, EstadoEvento.CANCELADO]:
                    acciones["ver"] = True
            elif vista == "eventos":
                if estado == EstadoEvento.ABIERTO and not es_propio:
                    acciones["inscribir"] = True
                elif estado in [EstadoEvento.PAUSADO, EstadoEvento.EN_PROCESO, EstadoEvento.FINALIZADO]:
                    pass  # Solo ver, sin inscribir
        
        elif es_rector:
            if vista in ["mis_eventos", "admin"]:
                if estado == EstadoEvento.REVISION:
                    acciones["aprobar"] = True
                    acciones["rechazar"] = True
                elif estado in [EstadoEvento.ABIERTO, EstadoEvento.EN_PROCESO]:
                    acciones["pausar"] = True
                    acciones["cancelar"] = True
                elif estado == EstadoEvento.PAUSADO:
                    acciones["reanudar"] = True
                    acciones["cancelar"] = True
                elif estado in [EstadoEvento.BORRADOR, EstadoEvento.RECHAZADO]:
                    acciones["editar"] = True
                    acciones["cancelar"] = True
        
        elif user_type == "fed_regional":
            if vista == "admin":
                acciones["ver"] = True
                acciones["pausar"] = False
                acciones["aprobar"] = False
                acciones["rechazar"] = False
                acciones["cancelar"] = False
        
        return acciones

    @staticmethod
    def puede_inscribir(evento, perfil):
        """
        Determina si el usuario puede inscribir grupos en el evento.
        """
        user_type = getattr(perfil, "user_type", None)
        
        if user_type != "institucional":
            return False
        
        if evento.estado_evento != EstadoEvento.ABIERTO:
            return False
        
        if EventoActionSelector.es_evento_propio(evento, perfil):
            return False
        
        return True


class ParticipanteSelector:
    """
    Clase para manejar la lógica de consulta (read) de participantes.
    """

    @staticmethod
    def get_participantes_para_perfil(perfil):
        user_type = getattr(perfil, "user_type", None)
        
        if JurisdictionSelector.es_rector(perfil):
            return Participante.objects.all()
        
        # Filtro territorial para participantes a través de sus vinculaciones activas
        if user_type == "fed_regional" and perfil.estado:
            return Participante.objects.filter(
                Q(vinculaciones__tipo_vinculacion='regional', vinculaciones__estado=perfil.estado, vinculaciones__status='activo') |
                Q(vinculaciones__tipo_vinculacion='institucional', vinculaciones__institucion__estado=perfil.estado, vinculaciones__status='activo')
            ).distinct()

        if user_type == "institucional" and perfil.institution:
            return Participante.objects.filter(
                vinculaciones__institucion=perfil.institution,
                vinculaciones__status="activo",
            ).distinct()
        
        return Participante.objects.none()

    @staticmethod
    def buscar_participantes(queryset, query):
        if not query:
            return queryset
        return queryset.filter(
            Q(nombres__icontains=query) | 
            Q(apellidos__icontains=query) | 
            Q(cedula__icontains=query)
        )

    @staticmethod
    def get_estado_para_formulario(perfil, institucion=None):
        """Determina el estado base para un formulario según el perfil e institución."""
        if JurisdictionSelector.es_rector(perfil):
            return None
        
        if institucion and hasattr(institucion, "estado"):
            return institucion.estado
            
        return getattr(perfil, "estado", None)

    @staticmethod
    def get_todos_estados_para_formulario(perfil):
        """Retorna los estados que el usuario puede seleccionar."""
        from registry.models import Estado
        if JurisdictionSelector.es_rector(perfil):
            return Estado.objects.all().order_by("nombre")
        
        estado = ParticipanteSelector.get_estado_para_formulario(perfil)
        return [estado] if estado else []

    @staticmethod
    def get_nombre_sede(perfil, institucion=None):
        """Retorna el nombre descriptivo de la sede para la UI."""
        inst = institucion or getattr(perfil, "institution", None)
        if not inst:
            return None
            
        nombre = inst.nombre
        estado = getattr(inst, "estado", None)
        if estado:
            nombre = f"{nombre} ({estado.nombre})"
        return nombre

    @staticmethod
    def get_municipios_para_formulario(estado):
        """Retorna los municipios para un estado dado."""
        from registry.models import Municipio
        if not estado:
            return []
        return Municipio.objects.filter(estado=estado).order_by("nombre")


class InstitucionSelector:
    """
    Clase para manejar la lógica de consulta (read) de instituciones.
    """

    @staticmethod
    def get_instituciones_para_perfil(perfil):
        queryset = Institucion.objects.filter(eliminado=False).select_related(
            "estado", "municipio"
        )
        return JurisdictionSelector.filtrar_por_territorio(queryset, perfil)

    @staticmethod
    def get_stats_instituciones(queryset):
        total = queryset.count()
        activas = queryset.filter(activa=True, estatus="aprobado").count()
        return {
            "total": total,
            "activas": activas,
            "pendientes": total - activas
        }

    @staticmethod
    def get_instituciones_con_usuarios(queryset):
        """
        Retorna una lista de diccionarios con la institución y sus usuarios asociados.
        Optimizado para evitar el problema N+1.
        """
        # Pre-cargar los perfiles de usuario y sus objetos User asociados en una sola consulta
        queryset = queryset.prefetch_related('userprofile_set__user')
        
        resultado = []
        for inst in queryset:
            # Al estar pre-cargado, .all() no dispara una nueva consulta SQL
            usuarios = [up.user for up in inst.userprofile_set.all()]
            resultado.append({"institucion": inst, "usuarios": usuarios})
        return resultado
