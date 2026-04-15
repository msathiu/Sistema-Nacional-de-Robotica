import logging
from django.db import transaction
from django.contrib.auth.models import User
from registry.models import Institucion, Estado, Municipio, Parroquia, Dependencia
from .identity_service import IdentityService
from registry.services.admission_service import AdmissionService
from ..utils import LocationUtils, StringUtils

logger = logging.getLogger(__name__)


class InstitutionService:
    """
    Servicio centralizado para la gestión de Instituciones.
    Coordina la creación de la institución, el usuario de Django y el perfil.
    """

    @staticmethod
    def crear_institucion_con_usuario(
        data: dict,
        es_central: bool = False,
        es_regional: bool = False,
        perfil_admin=None,
    ):
        """
        Crea una institución, su usuario de Django y perfil asociado en una transacción.
        """
        # 0. Validación de Duplicidad (Nombre, RIF, Ubicación)
        # Reconstruir RIF para validación - Formato consistente
        rif_letra = data.get("rif_letra")
        rif_num = StringUtils.clean_numeric_id(data.get("rif_numero"))
        rif_completo = data.get("rif")
        if not rif_completo and rif_letra and rif_num:
            # Formato consistente: J-12345678 o J-12345678-90
            rif_num_limpio = rif_num[:10]  # Máximo 10 dígitos
            if len(rif_num_limpio) <= 8:
                rif_completo = f"{rif_letra}-{rif_num_limpio}"
            else:
                rif_completo = (
                    f"{rif_letra}-{rif_num_limpio[:8]}-{rif_num_limpio[8:10]}"
                )

        nombre = data.get("nombre")
        estado_id = data.get("estado")
        municipio_id = data.get("municipio")
        parroquia_id = data.get("parroquia")

        if (
            data.get("tipo_institucion") != "particular"
            and nombre
            and rif_completo
            and estado_id
        ):
            # Resolver objetos para validación precisa
            estado, municipio, parroquia = LocationUtils.resolve_location(
                estado_id, municipio_id, parroquia_id
            )

            rif_num_limpio = rif_num[:10]
            rif_base = f"{rif_letra}-{rif_num_limpio[:8]}"
            rif_posibles = [rif_completo]
            if rif_completo != rif_base:
                rif_posibles.append(rif_base)

            if Institucion.objects.filter(
                nombre__iexact=nombre,
                rif__in=rif_posibles,
                estado=estado,
                municipio=municipio,
                parroquia=parroquia,
                eliminado=False,
            ).exists():
                raise ValueError(
                    f"Ya existe una institución registrada con el nombre '{nombre}' y RIF '{rif_completo}' en esta ubicación."
                )

        with transaction.atomic():
            # 1. Preparar objeto Institución
            # Asumimos que data ya viene validado por el formulario

            # Reconstruir el teléfono y RIF si vienen por partes desde el form
            codigo_area = data.get("codigo_area")
            numero_telefono = data.get("numero_telefono")
            telefono_completo = data.get("telefono")
            if not telefono_completo and codigo_area and numero_telefono:
                telefono_completo = f"{codigo_area}{numero_telefono}"

            rif_letra = data.get("rif_letra")
            rif_numero = data.get("rif_numero")
            rif_completo = data.get("rif")
            if not rif_completo and rif_letra and rif_numero:
                # Formato consistente: J-12345678 o J-12345678-90
                rif_num_limpio = StringUtils.clean_numeric_id(rif_numero)[:10]
                if len(rif_num_limpio) <= 8:
                    rif_completo = f"{rif_letra}-{rif_num_limpio}"
                else:
                    rif_completo = (
                        f"{rif_letra}-{rif_num_limpio[:8]}-{rif_num_limpio[8:10]}"
                    )

            institucion = Institucion(
                nombre=data.get("nombre"),
                email=data.get("email"),
                telefono=telefono_completo,
                telefono_codigo=codigo_area,
                telefono_numero=numero_telefono,
                rif=rif_completo,
                direccion=data.get("direccion"),
                tipo_institucion=data.get("tipo_institucion"),
                dependencia=data.get("dependencia"),
                codigo=data.get("codigo"),  # Si viene del form
                # Datos de persona natural
                particular_nombres=data.get("particular_nombres"),
                particular_apellidos=data.get("particular_apellidos"),
                particular_nacionalidad=data.get("particular_nacionalidad"),
                particular_cedula=data.get("particular_cedula"),
                # Otros campos del modelo
                naturaleza=data.get("naturaleza"),
                subcategoria=data.get("subcategoria"),
                codigo_mppe=data.get("codigo_mppe"),
            )

            # 2. Lógica de Ubicación
            estado_id = data.get("estado")
            municipio_id = data.get("municipio")
            parroquia_id = data.get("parroquia")

            estado, municipio, parroquia = LocationUtils.resolve_location(
                estado_id, municipio_id, parroquia_id
            )

            # Forzar estado si es Regional
            if es_regional and perfil_admin and perfil_admin.estado:
                estado = perfil_admin.estado

            institucion.estado = estado
            institucion.municipio = municipio
            institucion.parroquia = parroquia

            # 3. Lógica de Dependencia
            dependencia_existente = data.get("dependencia_existente")
            nueva_dependencia = data.get("nueva_dependencia")

            if dependencia_existente:
                # Usar dependencia existente (viene como objeto del ModelChoiceField)
                institucion.dependencia_rel = dependencia_existente
                institucion.dependencia = dependencia_existente.nombre
            elif nueva_dependencia and nueva_dependencia.strip():
                # Crear nueva dependencia
                nueva_dependencia = nueva_dependencia.strip()
                dependencia_obj, created = Dependencia.objects.get_or_create(
                    nombre__iexact=nueva_dependencia,
                    defaults={"nombre": nueva_dependencia, "activa": True},
                )
                institucion.dependencia_rel = dependencia_obj
                institucion.dependencia = dependencia_obj.nombre
                if created:
                    logger.info(f"Nueva dependencia creada: {dependencia_obj.nombre}")

            # 4. Lógica de Activación Inicial
            if es_central:
                institucion.activa = data.get("activa", False)
                institucion.estatus = data.get("estatus", "pendiente")
            else:
                institucion.activa = False
                institucion.estatus = "pendiente"

            # 4. Generar código si no existe
            if not institucion.codigo:
                # El código se genera en el save() del modelo si es null
                pass

            institucion.save()

            # 4. Crear Usuario de Django usando IdentityService
            # IMPORTANTE: Usar el código generado por el modelo tras el save()
            username = institucion.codigo
            if not username:
                # Fallback por si acaso, aunque el modelo debería generarlo
                username = data.get("codigo") or institucion.email
            password = data.get("password")

            # Si es central, el usuario puede nacer activo
            is_user_active = es_central

            user, profile = IdentityService.create_user_with_profile(
                username=username,
                email=institucion.email,
                password=password,
                user_type="institucional",
                institution=institucion,
                estado=institucion.estado,
            )

            # Sincronizar estado de activación del usuario
            if user.is_active != is_user_active:
                IdentityService.toggle_user_status(user, is_user_active)

            # Vincular usuario a la institución
            institucion.usuario = user
            institucion.save(update_fields=["usuario"])

            logger.info(
                f"Institución '{institucion.nombre}' creada con éxito (ID: {institucion.id})"
            )
            return institucion

    @staticmethod
    def actualizar_institucion(institucion: Institucion, data: dict):
        """
        Actualiza los datos de una institución.
        """
        with transaction.atomic():
            # Campos básicos
            for field in ["nombre", "email", "telefono", "direccion"]:
                if field in data:
                    setattr(institucion, field, data.get(field))

            # Ubicación
            estado_id = data.get("estado")
            municipio_id = data.get("municipio")
            parroquia_id = data.get("parroquia")

            estado, municipio, parroquia = LocationUtils.resolve_location(
                estado_id, municipio_id, parroquia_id
            )
            if estado:
                institucion.estado = estado
            if municipio:
                institucion.municipio = municipio
            if parroquia:
                institucion.parroquia = parroquia

            institucion.save()

            # Sincronizar email con el usuario si existe
            if institucion.usuario and "email" in data:
                user = institucion.usuario
                user.email = data.get("email")
                user.save(update_fields=["email"])

            logger.info(f"Institución '{institucion.nombre}' actualizada.")
            return institucion

    @staticmethod
    def toggle_status(institucion: Institucion, is_active: bool, admin_user):
        """
        Activa o desactiva una institución y su usuario asociado.
        """
        # Delegar a IdentityService si hay usuario
        if institucion.usuario:
            IdentityService.toggle_user_status(institucion.usuario, is_active=is_active)
        else:
            # Si no hay usuario, manejarlo directamente
            institucion.activa = is_active
            institucion._identity_service_handled = True
            institucion.save(update_fields=["activa"])

        logger.info(
            f"Estado de institución '{institucion.nombre}' cambiado a: {is_active} por {admin_user.username}"
        )

    @staticmethod
    def aprobar_primera_vez(institucion: Institucion, admin_user):
        """
        Realiza la aprobación inicial (generación de RNR) usando AdmissionService.
        """
        return AdmissionService.approve_institution(institucion, admin_user)
