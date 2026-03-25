import secrets
import string
import logging
from django.db import transaction
from django.contrib.auth.models import User
from registry.models import Participante, ParticipanteInstitucion, Institucion, Estado, Municipio, Parroquia
from .identity_service import IdentityService
from ..utils import StringUtils, LocationUtils

logger = logging.getLogger(__name__)

class ParticipanteService:
    """
    Servicio para gestionar el ciclo de vida de los Participantes.
    """

    @staticmethod
    def crear_participante_con_usuario(
        cleaned_data: dict,
        institucion=None,
        registrado_por=None,
        user_type_registrador="institucional",
        tipo_vinculacion="institucional",
        estado_vinculacion=None,
    ):
        """
        Crea un Participante, su Usuario (Django User) y vinculación institucional.
        Recibe cleaned_data de un formulario validado.
        """
        # 1. Obtener datos limpios del form
        nombres = cleaned_data.get("nombres")
        apellidos = cleaned_data.get("apellidos")
        nacionalidad = cleaned_data.get("nacionalidad", "V")
        cedula_personal = cleaned_data.get("cedula_personal")
        cedula_escolar = cleaned_data.get("cedula_escolar_input")
        email = cleaned_data.get("email")
        
        # 2. Determinar el username
        if cedula_personal:
            username = StringUtils.format_username_from_id(nacionalidad, cedula_personal)
        elif cedula_escolar:
            username = StringUtils.format_username_from_id("E", cedula_escolar)
        else:
            raise ValueError("Debe proporcionar al menos una cédula.")

        # 3. Iniciar Transacción
        with transaction.atomic():
            if User.objects.filter(username=username).exists():
                raise ValueError(f"Ya existe un usuario con el identificador {username}")

            # Crear usuario
            password_aleatoria = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            user, profile = IdentityService.create_user_with_profile(
                username=username,
                email=email,
                password=password_aleatoria,
                user_type="participante"
            )

            # Crear Participante (usando el resto de cleaned_data)
            # Removemos campos que no pertenecen al modelo Participante o que manejamos manualmente
            model_data = cleaned_data.copy()
            for key in ['cedula_personal', 'cedula_escolar_input', 'edad', 'profesion', 'institucion', 'grupo', 'tipo_vinculacion', 'vinculacion_institucion', 'vinculacion_estado']:
                model_data.pop(key, None)

            # Asignar campos manuales
            model_data['user'] = user
            model_data['cedula'] = cedula_personal if cedula_personal else None
            model_data['cedula_escolar'] = cedula_escolar if cedula_escolar else None

            creado_por_federacion = user_type_registrador in ['fed_central', 'fed_regional']
            model_data['creado_por_federacion'] = creado_por_federacion

            participante = Participante.objects.create(**model_data)

            # Vincular según tipo de vinculación
            tipo_vinculacion = cleaned_data.get('tipo_vinculacion', 'institucional')
            estado_vinculacion = cleaned_data.get('vinculacion_estado')
            institucion_vinculacion = cleaned_data.get('vinculacion_institucion') or institucion

            if tipo_vinculacion or institucion_vinculacion or estado_vinculacion:
                ParticipanteService.vincular_participante(
                    participante=participante,
                    tipo_vinculacion=tipo_vinculacion,
                    institucion=institucion_vinculacion,
                    estado=estado_vinculacion,
                    usuario=registrado_por if registrado_por else user
                )

            logger.info(f"Participante {nombres} {apellidos} ({username}) creado.")
            return participante

    @staticmethod
    def actualizar_participante(participante: Participante, cleaned_data: dict):
        """
        Actualiza los datos de un participante usando cleaned_data de un formulario.
        """
        with transaction.atomic():
            # Manejo especial de cédulas para evitar conflictos de unicidad (usar None si vacío)
            cedula_personal = cleaned_data.get('cedula_personal')
            cedula_escolar = cleaned_data.get('cedula_escolar_input')

            participante.cedula = cedula_personal if cedula_personal else None
            participante.cedula_escolar = cedula_escolar if cedula_escolar else None

            # Actualizar campos restantes del modelo
            excluded_fields = [
                'cedula_personal', 'cedula_escolar_input', 'cedula', 'cedula_escolar', 
                'edad', 'profesion', 'institucion', 'grupo'
            ]

            for field, value in cleaned_data.items():
                if hasattr(participante, field) and field not in excluded_fields:
                    setattr(participante, field, value)

            participante.save()            
            # Sincronizar email con User
            if participante.user and 'email' in cleaned_data:
                participante.user.email = cleaned_data.get('email')
                participante.user.save(update_fields=['email'])

            logger.info(f"Participante {participante.nombres} {participante.apellidos} actualizado.")
            return participante

    @staticmethod
    def vincular_participante(
        participante: Participante,
        tipo_vinculacion: str = 'institucional',
        institucion: Institucion = None,
        estado: Estado = None,
        rol: str = None,
        usuario: User = None,
    ) -> ParticipanteInstitucion:
        """Crea o reactiva una vinculación para el participante."""
        if tipo_vinculacion not in ['institucional', 'regional', 'central']:
            raise ValueError("Tipo de vinculacion no valido")

        if tipo_vinculacion == 'institucional' and not institucion:
            raise ValueError("Se requiere institucion para vinculacion institucional")
        if tipo_vinculacion == 'regional' and not estado:
            raise ValueError("Se requiere estado para vinculacion regional")

        defaults = {
            'tipo_vinculacion': tipo_vinculacion,
            'registrado_por': usuario,
            'status': 'activo',
        }

        if tipo_vinculacion == 'institucional':
            defaults['institucion'] = institucion
            defaults['estado'] = None
        elif tipo_vinculacion == 'regional':
            defaults['estado'] = estado
            defaults['institucion'] = None
        else:
            defaults['estado'] = None
            defaults['institucion'] = None

        vinculacion, created = ParticipanteInstitucion.objects.get_or_create(
            participante=participante,
            tipo_vinculacion=tipo_vinculacion,
            defaults=defaults,
        )

        if not created:
            if vinculacion.status != 'activo':
                vinculacion.status = 'activo'
                vinculacion.fecha_desvinculacion = None
                vinculacion.registrado_por = usuario
                if tipo_vinculacion == 'institucional':
                    vinculacion.institucion = institucion
                elif tipo_vinculacion == 'regional':
                    vinculacion.estado = estado
                vinculacion.save(update_fields=['status', 'fecha_desvinculacion', 'registrado_por', 'institucion', 'estado'])
                logger.info(f"[Participante] Vinculación reactivada: {participante} @ {tipo_vinculacion}")
            else:
                logger.info(f"[Participante] Vinculación ya existe y está activa: {participante} @ {tipo_vinculacion}")
        else:
            logger.info(f"[Participante] Nueva vinculación: {participante} @ {tipo_vinculacion}")

        return vinculacion

    @staticmethod
    def desvincular_participante(
        participante: Participante,
        tipo_vinculacion: str = 'institucional',
        institucion: Institucion = None,
        estado: Estado = None,
        usuario: User = None,
    ) -> ParticipanteInstitucion:
        """Marca la vinculación como inactiva y registra fecha de desvinculación."""
        queryset = ParticipanteInstitucion.objects.filter(participante=participante, tipo_vinculacion=tipo_vinculacion)

        if tipo_vinculacion == 'institucional':
            queryset = queryset.filter(institucion=institucion)
        elif tipo_vinculacion == 'regional':
            queryset = queryset.filter(estado=estado)

        vinculacion = queryset.first()
        if not vinculacion:
            raise ParticipanteInstitucion.DoesNotExist(
                "No existe una vinculación para el participante con los parámetros especificados"
            )

        vinculacion.status = 'inactivo'
        vinculacion.fecha_desvinculacion = timezone.now()
        vinculacion.registrado_por = usuario
        vinculacion.save(update_fields=['status', 'fecha_desvinculacion', 'registrado_por'])
        logger.info(f"[Participante] Vinculación desvinculada: {participante} @ {tipo_vinculacion}")
        return vinculacion
