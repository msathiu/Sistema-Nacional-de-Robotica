"""
Servicio de Gestión de Participantes Multi-Institución.

Este módulo implementa la lógica de negocio para el registro y gestión de participantes
que pueden estar vinculados a múltiples instituciones.

Reglas de Negocio Implementadas:
- Validación de cédula única antes de crear participante.
- Vinculación de participantes a instituciones con transaction.atomic.
- Estados independientes por institución.
- Historial de grupos por participante.

Autor: Sistema de Registro
Fecha: 2024
"""

import logging
from typing import Optional, Tuple

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import Participante, ParticipanteInstitucion, ParticipanteGrupo, Institucion, Grupo

logger = logging.getLogger(__name__)


class ParticipanteService:
    """
    Servicio que maneja las operaciones relacionadas con participantes multi-institución.
    
    Garantiza la integridad de datos y separación de responsabilidades.
    
    Usage:
        >>> from registry.services import ParticipanteService
        >>> # Registrar participante
        >>> participante, vinculacion, creado = ParticipanteService.registrar_participante_con_institucion(
        ...     institucion=institucion,
        ...     datos_participante=datos,
        ...     grupo=grupo,
        ...     usuario=request.user
        ... )
    """
    
    @staticmethod
    def buscar_por_cedula(cedula: str) -> Optional[Participante]:
        """
        Busca un participante por cédula.
        
        Args:
            cedula: Cédula a buscar (se limpia automáticamente)
            
        Returns:
            Participante si existe, None si no existe
        """
        cedula_limpia = ''.join(filter(str.isdigit, cedula))
        try:
            return Participante.objects.get(cedula=cedula_limpia)
        except Participante.DoesNotExist:
            return None
    
    @staticmethod
    def buscar_por_cedula_escolar(cedula_escolar: str) -> Optional[Participante]:
        """Busca un participante por cédula escolar."""
        cedula_limpia = ''.join(filter(str.isdigit, cedula_escolar))
        try:
            return Participante.objects.get(cedula_escolar=cedula_limpia)
        except Participante.DoesNotExist:
            return None
    
    @staticmethod
    def crear_participante(datos_participante: dict) -> Participante:
        """
        Crea un nuevo participante.
        
        Args:
            datos_participante: Diccionario con datos del participante
            
        Returns:
            Participante creado
        """
        # Limpiar cédulas
        if 'cedula' in datos_participante and datos_participante['cedula']:
            datos_participante['cedula'] = ''.join(filter(str.isdigit, datos_participante['cedula']))
        
        if 'cedula_escolar' in datos_participante and datos_participante['cedula_escolar']:
            datos_participante['cedula_escolar'] = ''.join(filter(str.isdigit, datos_participante['cedula_escolar']))
        
        participante = Participante.objects.create(**datos_participante)
        
        logger.info(f"[Participante] Nuevo participante creado: {participante.nombre_completo} ({participante.cedula})")
        return participante
    
    @staticmethod
    def vincular_participante_institucion(
        participante: Participante,
        institucion: Institucion,
        grupo: Optional[Grupo] = None,
        usuario: Optional[User] = None
    ) -> Tuple[ParticipanteInstitucion, bool]:
        """
        Vincula un participante a una institución.
        
        IMPORTANTE: Los estados son independientes por institución.
        
        Args:
            participante: Participante a vincular
            institucion: Institución destino
            grupo: Grupo opcional
            usuario: Usuario que realiza la vinculación
            
        Returns:
            tuple: (ParticipanteInstitucion, created)
        """
        vinculacion, created = ParticipanteInstitucion.objects.get_or_create(
            participante=participante,
            institucion=institucion,
            defaults={
                'grupo_actual': grupo,
                'status': 'activo',
                'registrado_por': usuario
            }
        )
        
        if not created:
            # Si ya existe, reactivar si estaba inactiva
            if vinculacion.status != 'activo':
                vinculacion.status = 'activo'
                vinculacion.fecha_desvinculacion = None
                vinculacion.save(update_fields=['status', 'fecha_desvinculacion'])
                logger.info(f"[Participante] Vinculación reactivada: {participante} @ {institucion}")
            else:
                logger.info(f"[Participante] Vinculación ya existe: {participante} @ {institucion}")
        else:
            logger.info(f"[Participante] Nueva vinculación: {participante} @ {institucion}")
        
        return vinculacion, created
    
    @staticmethod
    def registrar_participante_con_institucion(
        institucion: Institucion,
        datos_participante: dict,
        grupo: Optional[Grupo] = None,
        usuario: Optional[User] = None
    ) -> Tuple[Participante, ParticipanteInstitucion, bool]:
        """
        Flujo completo: buscar/crear participante + vincular a institución.
        
        Args:
            institucion: Institución donde se registra
            datos_participante: Datos del participante
            grupo: Grupo opcional
            usuario: Usuario que registra
            
        Returns:
            tuple: (Participante, ParticipanteInstitucion, participante_creado)
        """
        with transaction.atomic():
            # Buscar participante existente
            participante = None
            if datos_participante.get('cedula'):
                participante = ParticipanteService.buscar_por_cedula(datos_participante['cedula'])
            
            if not participante and datos_participante.get('cedula_escolar'):
                participante = ParticipanteService.buscar_por_cedula_escolar(datos_participante['cedula_escolar'])
            
            participante_creado = False
            
            if not participante:
                participante = ParticipanteService.crear_participante(datos_participante)
                participante_creado = True
            
            # Vincular a institución
            vinculacion, vinculacion_creada = ParticipanteService.vincular_participante_institucion(
                participante=participante,
                institucion=institucion,
                grupo=grupo,
                usuario=usuario
            )
            
            # Crear historial de grupo si se asignó
            if grupo:
                ParticipanteGrupo.objects.get_or_create(
                    participante=participante,
                    grupo=grupo,
                    defaults={'activo': True}
                )
        
        return participante, vinculacion, participante_creado
    
    @staticmethod
    def asignar_a_grupo(
        participante: Participante,
        grupo: Grupo,
        institucion: Institucion
    ):
        """
        Asigna participante a un grupo.
        
        Args:
            participante: Participante a asignar
            grupo: Grupo destino
            institucion: Institución (debe coincidir con la del grupo)
            
        Raises:
            ValidationError: Si no hay vinculación activa o el grupo no pertenece a la institución
        """
        # Verificar vinculación activa
        try:
            vinculacion = ParticipanteInstitucion.objects.get(
                participante=participante,
                institucion=institucion,
                status='activo'
            )
        except ParticipanteInstitucion.DoesNotExist:
            raise ValidationError(
                f"El participante '{participante.nombre_completo}' no está vinculado activamente "
                f"a la institución '{institucion.nombre}'."
            )
        
        # Verificar que el grupo pertenece a la institución
        if grupo.institucion != institucion:
            raise ValidationError(
                f"El grupo '{grupo.nombre}' no pertenece a la institución '{institucion.nombre}'."
            )
        
        with transaction.atomic():
            # Actualizar grupo actual
            vinculacion.grupo_actual = grupo
            vinculacion.save(update_fields=['grupo_actual'])
            
            # Crear historial
            ParticipanteGrupo.objects.get_or_create(
                participante=participante,
                grupo=grupo,
                defaults={'activo': True}
            )
        
        logger.info(f"[Participante] {participante.nombre_completo} asignado al grupo {grupo.nombre}")
    
    @staticmethod
    def cambiar_estado_participante(
        participante: Participante,
        institucion: Institucion,
        nuevo_status: str,
        usuario: Optional[User] = None
    ) -> ParticipanteInstitucion:
        """
        Cambia el estado de un participante en una institución específica.
        
        IMPORTANTE: El cambio de estado solo afecta a la institución especificada.
        No afecta el estado del participante en otras instituciones.
        
        Args:
            participante: Participante a modificar
            institucion: Institución donde se cambia el estado
            nuevo_status: Nuevo estado (activo/inactivo/suspendido/egresado)
            usuario: Usuario que realiza el cambio
            
        Returns:
            ParticipanteInstitucion: La vinculación actualizada
            
        Raises:
            ValidationError: Si el estado no es válido o no existe vinculación
        """
        if nuevo_status not in ['activo', 'inactivo', 'suspendido', 'egresado']:
            raise ValidationError(
                f"Estado '{nuevo_status}' no válido. Use 'activo', 'inactivo', 'suspendido' o 'egresado'."
            )
        
        try:
            vinculacion = ParticipanteInstitucion.objects.get(
                participante=participante,
                institucion=institucion
            )
        except ParticipanteInstitucion.DoesNotExist:
            raise ValidationError(
                f"El participante no está vinculado a la institución '{institucion.nombre}'."
            )
        
        with transaction.atomic():
            vinculacion.status = nuevo_status
            if nuevo_status == 'inactivo':
                vinculacion.fecha_desvinculacion = timezone.now()
            vinculacion.save(update_fields=['status', 'fecha_desvinculacion'])
        
        logger.info(
            f"[Participante] Estado de {participante.nombre_completo} en {institucion.nombre} "
            f"cambiado a {nuevo_status} por: {usuario.username if usuario else 'Sistema'}"
        )
        return vinculacion
    
    @staticmethod
    def obtener_participantes_por_institucion(
        institucion: Institucion,
        solo_activos: bool = True
    ):
        """
        Obtiene los participantes de una institución.
        
        Args:
            institucion: Institución a consultar
            solo_activos: Si True, solo retorna participantes activos
            
        Returns:
            QuerySet: Vinculaciones ParticipanteInstitucion de la institución
        """
        queryset = ParticipanteInstitucion.objects.select_related('participante').filter(
            institucion=institucion
        )
        
        if solo_activos:
            queryset = queryset.filter(status='activo')
        
        return queryset.order_by('-fecha_vinculacion')
