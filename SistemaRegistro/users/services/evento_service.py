import logging
from datetime import date, datetime
from django.db import transaction
from django.db.models import Q
from registry.models import (
    Evento,
    Club,
    EstadoEvento,
    AsistenciaEvento,
    InscripcionGrupoEvento,
)
from ..forms import EventoContactDataForm
from ..utils import LocationUtils

logger = logging.getLogger(__name__)


class EventoService:
    """
    Servicio para la gestión de eventos.
    """

    @staticmethod
    def get_initial_form_data(evento):
        """
        Retorna los valores iniciales para el formulario de edición.
        """
        return {
            "nombre": evento.nombre or "",
            "categoria": evento.tipo or "",
            "tipo_evento": evento.tipo_evento or "institucional",
            "fecha": evento.fecha.strftime("%Y-%m-%d") if evento.fecha else "",
            "fecha_hasta": (
                evento.fecha_fin_efectiva.strftime("%Y-%m-%d")
                if evento.fecha_fin_efectiva
                else (
                    evento.fecha_hasta.strftime("%Y-%m-%d")
                    if evento.fecha_hasta
                    else ""
                )
            ),
            "modalidad": evento.modalidad or "presencial",
            "estado_evento": evento.estado_evento or EstadoEvento.BORRADOR,
            "audiencia": getattr(evento, "audiencia", "publica"),
            "estado": evento.estado_id,
            "municipio": evento.municipio_id,
            "parroquia": evento.parroquia_id,
            "direccion": evento.direccion or "",
            "telefono_codigo": getattr(evento, "telefono_codigo", ""),
            "telefono_numero": getattr(evento, "telefono_numero", ""),
            "email_contacto": getattr(evento, "email_contacto", ""),
            "descripcion": evento.descripcion or "",
            "requisitos": evento.requisitos or "",
            "club_organizador": getattr(evento, "club_organizador_id", None),
        }

    @staticmethod
    def _validate_and_prepare_data(perfil, data: dict, instance=None):
        """
        Valida y prepara los datos para creación o actualización.
        """
        user_type = perfil.user_type
        institution = perfil.institution if user_type == "institucional" else None

        # 1. Validar Fechas
        fecha_str = data.get("fecha")
        fecha_hasta_str = (data.get("fecha_hasta") or "").strip()

        try:
            fecha_evento = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            if not instance and fecha_evento < date.today():
                raise ValueError(
                    "La fecha desde del evento no puede ser anterior a la fecha actual."
                )

            if fecha_hasta_str:
                fecha_hasta_evento = datetime.strptime(
                    fecha_hasta_str, "%Y-%m-%d"
                ).date()
            else:
                fecha_hasta_evento = fecha_evento

            if fecha_hasta_evento < fecha_evento:
                raise ValueError(
                    "La fecha hasta no puede ser anterior a la fecha desde."
                )
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD.")
            raise ValueError(str(e))

        # 2. Resolver Ubicación
        estado_id = data.get("estado")
        municipio_id = data.get("municipio")
        parroquia_id = data.get("parroquia")
        direccion = data.get("direccion", "")

        estado_obj, municipio_obj, parroquia_obj = LocationUtils.resolve_location(
            estado_id, municipio_id, parroquia_id
        )
        contacto_form = EventoContactDataForm(
            data={
                "telefono_codigo": data.get("telefono_codigo", ""),
                "telefono_numero": data.get("telefono_numero", ""),
                "email_contacto": data.get("email_contacto", ""),
            }
        )
        if not contacto_form.is_valid():
            first_error = next(iter(contacto_form.errors.values()))[0]
            raise ValueError(first_error)

        telefono_codigo = contacto_form.cleaned_data.get("telefono_codigo", "")
        telefono_numero = contacto_form.cleaned_data.get("telefono_numero", "")

        # 3. Validar Club y Audiencia
        tipo_evento = data.get(
            "tipo_evento", instance.tipo_evento if instance else "institucional"
        )
        club_organizador_id = data.get("club_organizador")
        audiencia = data.get("audiencia", instance.audiencia if instance else "publica")
        club_obj = None

        if tipo_evento == "club":
            if not club_organizador_id:
                raise ValueError("Debe seleccionar un club para eventos de club.")

            try:
                if user_type == "fed_central":
                    # fed_central puede crear eventos para cualquier club aprobado (ente rector)
                    club_obj = Club.objects.get(
                        id=club_organizador_id, status="aprobado", eliminado=False
                    )
                else:
                    club_obj = Club.objects.get(
                        id=club_organizador_id, status="aprobado"
                    )
            except Club.DoesNotExist:
                raise ValueError("El club seleccionado no existe o no está aprobado.")

            if user_type == "institucional":
                es_creador = club_obj.institucion_creadora == institution
                es_miembro = club_obj.membresias.filter(
                    institucion=institution, estado="miembro_activo"
                ).exists()
                if not es_creador and not es_miembro:
                    raise ValueError(
                        "No tienes permisos para crear eventos en este club."
                    )

            audiencia = "club_exclusivo"

        return {
            "nombre": data.get("nombre"),
            "tipo": data.get("categoria"),
            "fecha": fecha_evento,
            "fecha_hasta": fecha_hasta_evento,
            "descripcion": data.get("descripcion", ""),
            "modalidad": data.get("modalidad", "presencial"),
            "estado": estado_obj,
            "municipio": municipio_obj,
            "parroquia": parroquia_obj,
            "direccion": direccion,
            "requisitos": data.get("requisitos", ""),
            "tipo_evento": tipo_evento,
            "institucion": institution
            if (user_type == "institucional" and tipo_evento == "institucional")
            else (instance.institucion if instance else None),
            "club_organizador": club_obj if tipo_evento == "club" else None,
            "audiencia": audiencia,
            "telefono_codigo": telefono_codigo,
            "telefono_numero": telefono_numero,
            "email_contacto": contacto_form.cleaned_data.get("email_contacto", ""),
        }

    @staticmethod
    def crear_evento(user, perfil, data: dict):
        """
        Crea un evento validando roles y estados iniciales.

        El estado inicial se determina en el backend según el rol:
        - fed_central/superuser/tecnologico: ABIERTO (publicación directa)
        - institucional: BORRADOR (requiere revisión)
        - fed_regional: NO PERMITIDO en esta fase
        """
        # Validar que fed_regional no pueda crear eventos en esta fase
        user_type = getattr(perfil, "user_type", None)
        if user_type == "fed_regional":
            raise ValueError(
                "Las sedes regionales no pueden crear eventos en esta fase."
            )

        validated_data = EventoService._validate_and_prepare_data(perfil, data)

        # Determinar Estado Inicial (FUENTE DE VERDAD: backend)
        # Se ignora cualquier valor enviado desde el frontend
        if user_type in ["fed_central", "superuser", "tecnologico"]:
            estado_inicial = EstadoEvento.ABIERTO
            es_publico = validated_data["audiencia"] == "publica"
        else:
            estado_inicial = EstadoEvento.BORRADOR
            es_publico = False

        evento = Evento.objects.create(
            **validated_data,
            es_publico=es_publico,
            estado_evento=estado_inicial,
            creado_por=user,
            activo=True,
        )

        logger.info(
            f"Evento '{evento.nombre}' creado por {user.username} con estado inicial '{estado_inicial}'."
        )
        return evento

    @staticmethod
    def actualizar_evento(evento, perfil, data: dict):
        """
        Actualiza un evento existente.
        """
        validated_data = EventoService._validate_and_prepare_data(
            perfil, data, instance=evento
        )

        for field, value in validated_data.items():
            setattr(evento, field, value)

        evento.save()
        logger.info(f"Evento '{evento.nombre}' actualizado.")
        return evento

    @staticmethod
    def gestionar_estado(
        evento,
        user,
        nuevo_estado,
        observacion="",
        nueva_fecha=None,
        nueva_fecha_hasta=None,
    ):
        """
        Gestiona el cambio de estado de un evento (pausa, reabrir, cancelar).
        Centraliza la lógica de negocio y validaciones de transición.
        """
        update_fields = []

        # 1. Validar fechas si se proporcionan
        if nueva_fecha:
            if nueva_fecha < date.today():
                raise ValueError("La nueva fecha no puede ser anterior a hoy.")
            if nueva_fecha != evento.fecha:
                evento.fecha = nueva_fecha
                update_fields.append("fecha")

        if nueva_fecha_hasta:
            if nueva_fecha and nueva_fecha_hasta < nueva_fecha:
                raise ValueError(
                    "La fecha hasta no puede ser anterior a la fecha desde."
                )
            if nueva_fecha_hasta != evento.fecha_hasta:
                evento.fecha_hasta = nueva_fecha_hasta
                update_fields.append("fecha_hasta")
        elif nueva_fecha and (
            not evento.fecha_hasta or evento.fecha_hasta < nueva_fecha
        ):
            # Ajuste automático si solo se cambia fecha desde
            evento.fecha_hasta = nueva_fecha
            update_fields.append("fecha_hasta")

        # 2. Transiciones según el estado solicitado
        if nuevo_estado == EstadoEvento.PAUSADO:
            if not evento.puede_pausar(user):
                raise ValueError(
                    "Este evento no puede pausarse desde su estado actual o no tienes permisos."
                )
            if not observacion:
                raise ValueError(
                    "Debes indicar una observación visible al pausar el evento."
                )

            if not evento.pausar(observacion):
                raise ValueError("No fue posible pausar el evento.")

            if update_fields:
                evento.save(update_fields=update_fields)

        elif nuevo_estado == EstadoEvento.ABIERTO:
            if (
                evento.estado_evento != EstadoEvento.PAUSADO
                or not evento.puede_transicionar(EstadoEvento.ABIERTO)
            ):
                raise ValueError("Solo se pueden reabrir eventos que estén pausados.")

            evento.estado_evento = EstadoEvento.ABIERTO
            update_fields.append("estado_evento")

            # Gestionar observación
            if observacion:
                evento.observacion_estado = observacion
                update_fields.append("observacion_estado")
            elif evento.observacion_estado:
                evento.observacion_estado = ""
                update_fields.append("observacion_estado")

            evento.save(update_fields=update_fields)

        elif nuevo_estado == EstadoEvento.CANCELADO:
            if not observacion:
                raise ValueError("Debes indicar el motivo de cancelación.")

            with transaction.atomic():
                # Si el evento ya estaba cancelado, hacemos una limpieza idempotente:
                # liberar equipos que pudieran haber quedado vinculados.
                if evento.estado_evento != EstadoEvento.CANCELADO:
                    if not evento.cancelar(observacion):
                        raise ValueError(
                            "Este evento no puede cancelarse desde su estado actual o no tienes permisos."
                        )

                inscripciones = InscripcionGrupoEvento.objects.filter(
                    evento=evento, activo=True
                ).select_related("grupo")

                for inscripcion in inscripciones:
                    grupo = inscripcion.grupo

                    # Al cancelar el evento, la cancelación prima sobre restricciones
                    # de grupo bloqueado: el equipo debe quedar libre.
                    grupo.estado_grupo = "editable"
                    grupo.evento = None
                    grupo.save(update_fields=["estado_grupo", "evento"])

                    inscripcion.delete()

        elif nuevo_estado == EstadoEvento.FINALIZADO:
            if evento.estado_evento not in [
                EstadoEvento.ABIERTO,
                EstadoEvento.EN_PROCESO,
                EstadoEvento.PAUSADO,
            ]:
                raise ValueError(
                    "Solo se pueden finalizar eventos que estén abiertos, en proceso o pausados."
                )
            if not observacion:
                raise ValueError(
                    "Debes indicar una observación al finalizar el evento."
                )

            evento.estado_evento = EstadoEvento.FINALIZADO
            evento.observacion_estado = observacion
            update_fields.extend(["estado_evento", "observacion_estado"])

            evento.save(update_fields=update_fields)

        elif nuevo_estado == "reprogramar":
            # Reprogramar es una acción especial que cambia fechas pero mantiene el estado
            if not nueva_fecha:
                raise ValueError(
                    "Debes especificar una nueva fecha para reprogramar el evento."
                )
            if not observacion:
                raise ValueError("Debes indicar el motivo de la reprogramación.")

            # Las fechas ya fueron validadas y asignadas arriba
            evento.observacion_estado = observacion
            update_fields.append("observacion_estado")

            evento.save(update_fields=update_fields)
            logger.info(f"Evento '{evento.nombre}' reprogramado por {user.username}.")
            return evento

        else:
            raise ValueError(f"Estado '{nuevo_estado}' no soportado para esta acción.")

        logger.info(
            f"Evento '{evento.nombre}' cambió a estado {nuevo_estado} por {user.username}."
        )
        return evento

    @staticmethod
    def eliminar_evento(evento, user):
        """
        Elimina un evento validando que no tenga inscritos.
        """
        # Verificar inscripciones (usando el nombre de relación correcto)
        if evento.inscripciones_grupo.exists():
            raise ValueError(
                "No se puede eliminar un evento que ya tiene equipos inscritos."
            )

        nombre = evento.nombre
        evento.delete()
        logger.info(f"Evento '{nombre}' eliminado por {user.username}.")
        return True

    @staticmethod
    def generar_asistencias_pendientes(evento):
        """
        Crea registros AsistenciaEvento en estado 'pendiente' para todos los
        participantes de equipos inscritos en el evento.
        Usa bulk_create con ignore_conflicts para ser idempotente.
        """
        from registry.models import InscripcionGrupoEvento

        inscripciones = InscripcionGrupoEvento.objects.filter(
            evento=evento, activo=True
        ).prefetch_related("grupo__participantes")

        registros = []
        for inscripcion in inscripciones:
            for participante in inscripcion.grupo.participantes.all():
                registros.append(
                    AsistenciaEvento(
                        evento=evento,
                        participante=participante,
                        grupo=inscripcion.grupo,
                        asistencia="pendiente",
                    )
                )

        if registros:
            AsistenciaEvento.objects.bulk_create(registros, ignore_conflicts=True)
            logger.info(
                f"Generados {len(registros)} registros de asistencia para evento '{evento.nombre}'."
            )
        return len(registros)
