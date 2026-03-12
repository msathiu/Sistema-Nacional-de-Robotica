"""
Servicio de Gestión de Tutores.

Este módulo implementa la lógica de negocio para el registro y asignación de tutores.

Reglas de Negocio Implementadas:
- Validación de cédula única antes de crear tutor.
- Asignación de tutores a grupos con transaction.atomic.
- Validación de integridad: Grupo requiere Tutor antes de vincularse a Evento.

Autor: Sistema de Registro
Fecha: 2026
"""

import logging
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import Tutor, Grupo, Institucion, TutorInstitucion

logger = logging.getLogger(__name__)


class TutorService:
    """
    Servicio que maneja las operaciones relacionadas con tutores.
    
    Garantiza la integridad de datos y separación de responsabilidades.
    
    Usage:
        >>> from registry.services import TutorService
        >>> # Crear tutor
        >>> tutor = TutorService.registrar_tutor(institucion, datos)
        >>> # Asignar a grupo
        >>> TutorService.asignar_tutor_a_grupo(tutor, grupo)
    """
    
    @staticmethod
    def buscar_tutor_por_cedula(cedula: str) -> Optional[Tutor]:
        """Busca un tutor por cédula."""
        cedula_limpia = ''.join(filter(str.isdigit, cedula))
        try:
            return Tutor.objects.get(cedula=cedula_limpia)
        except Tutor.DoesNotExist:
            return None
    
    @staticmethod
    def crear_tutor(datos_tutor: dict) -> Tutor:
        """Crea un nuevo tutor."""
        cedula_limpia = ''.join(filter(str.isdigit, datos_tutor['cedula']))
        
        tutor = Tutor.objects.create(
            nacionalidad=datos_tutor.get('nacionalidad', 'V'),
            nombres=datos_tutor['nombres'],
            apellidos=datos_tutor['apellidos'],
            sexo=datos_tutor.get('sexo', 'M'),
            cedula=cedula_limpia,
            telefono_codigo=datos_tutor.get('telefono_codigo', ''),
            telefono=datos_tutor.get('telefono', ''),
            email=datos_tutor['email'],
            profesion=datos_tutor.get('profesion', ''),
            experiencia=datos_tutor.get('experiencia', ''),
        )
        
        logger.info(f"[Tutor] Nuevo tutor creado: {tutor.get_nombre_completo()} ({cedula_limpia})")
        return tutor
    
    @staticmethod
    def vincular_tutor_institucion(
        tutor: Tutor,
        institucion: Institucion,
        rol: str = 'colaborador',
        usuario: Optional[User] = None
    ) -> tuple:
        """
        Vincula un tutor a una institución.
        
        Returns:
            tuple: (TutorInstitucion, created)
        """
        vinculacion, created = TutorInstitucion.objects.get_or_create(
            tutor=tutor,
            institucion=institucion,
            defaults={'rol': rol, 'status': 'activo'}
        )
        
        if not created:
            if vinculacion.status != 'activo':
                vinculacion.status = 'activo'
                vinculacion.fecha_desvinculacion = None
                vinculacion.save(update_fields=['status', 'fecha_desvinculacion'])
                logger.info(f"[Tutor] Vinculación reactivada: {tutor} @ {institucion}")
            else:
                logger.info(f"[Tutor] Vinculación ya existe: {tutor} @ {institucion}")
        else:
            logger.info(f"[Tutor] Nueva vinculación: {tutor} @ {institucion}")
        
        return vinculacion, created
    
    @staticmethod
    def registrar_tutor_con_institucion(
        institucion: Institucion,
        datos_tutor: dict,
        rol: str = 'colaborador',
        usuario: Optional[User] = None
    ) -> tuple:
        """
        Flujo completo: buscar/crear tutor + vincular a institución.
        
        Returns:
            tuple: (Tutor, TutorInstitucion, tutor_creado)
        """
        with transaction.atomic():
            tutor = TutorService.buscar_tutor_por_cedula(datos_tutor['cedula'])
            tutor_creado = False
            
            if not tutor:
                tutor = TutorService.crear_tutor(datos_tutor)
                tutor_creado = True
            
            vinculacion, vinculacion_creada = TutorService.vincular_tutor_institucion(
                tutor=tutor,
                institucion=institucion,
                rol=rol,
                usuario=usuario
            )
        
        return tutor, vinculacion, tutor_creado
    
    @staticmethod
    def registrar_tutor(
        institucion: Institucion,
        datos_tutor: dict,
        usuario_solicitante: Optional[User] = None
    ) -> Tutor:
        """
        Método legacy: Registra un tutor y lo vincula a una institución.
        
        DEPRECADO: Usar registrar_tutor_con_institucion() en su lugar.
        """
        tutor, vinculacion, tutor_creado = TutorService.registrar_tutor_con_institucion(
            institucion=institucion,
            datos_tutor=datos_tutor,
            rol='colaborador',
            usuario=usuario_solicitante
        )
        return tutor
    
    @staticmethod
    def asignar_tutor_a_grupo(
        tutor: Tutor,
        grupo: Grupo,
        usuario: Optional[User] = None
    ) -> None:
        """
        Asigna un tutor a un grupo específico.
        
        Valida que el tutor esté activo en la institución del grupo.
        """
        # Validar que el tutor esté vinculado activamente a la institución del grupo
        if grupo.institucion:
            vinculacion_activa = TutorInstitucion.objects.filter(
                tutor=tutor,
                institucion=grupo.institucion,
                status='activo'
            ).exists()
            
            if not vinculacion_activa:
                raise ValidationError(
                    f"El tutor '{tutor.get_nombre_completo()}' no está vinculado activamente "
                    f"a la institución '{grupo.institucion.nombre}'."
                )
        
        with transaction.atomic():
            grupo.tutores.add(tutor)
        
        logger.info(
            f"[Tutor] Tutor {tutor.get_nombre_completo()} asignado al grupo "
            f"{grupo.nombre} por: {usuario.username if usuario else 'Sistema'}"
        )
    
    @staticmethod
    def remover_tutor_de_grupo(
        tutor: Tutor,
        grupo: Grupo,
        usuario: Optional[User] = None
    ) -> None:
        """
        Remueve un tutor de un grupo específico.
        
        Valida que el grupo no quede sin tutores si está vinculado a un evento.
        
        Args:
            tutor: Tutor a remover.
            grupo: Grupo del que se removerá el tutor.
            usuario: Usuario que realiza la acción (para auditoría).
            
        Raises:
            ValidationError: Si el grupo está vinculado a un evento y quedaría sin tutores.
        """
        with transaction.atomic():
            # Verificar si el grupo está vinculado a un evento
            if grupo.evento_id:
                tutores_actuales = grupo.tutores.count()
                if tutores_actuales <= 1:
                    raise ValidationError(
                        "No se puede remover al tutor porque el grupo está vinculado "
                        "a un evento y debe tener al menos un tutor asignado."
                    )
            
            grupo.tutores.remove(tutor)
        
        logger.info(
            f"[Tutor] Tutor {tutor.get_nombre_completo()} removido del grupo "
            f"{grupo.nombre} por: {usuario.username if usuario else 'Sistema'}"
        )
    
    @staticmethod
    def validar_grupo_listo_para_evento(grupo: Grupo) -> bool:
        """
        Valida si un grupo está listo para vincularse a un evento.
        
        Un grupo está listo si tiene al menos un tutor asignado.
        
        Args:
            grupo: Grupo a validar.
            
        Returns:
            bool: True si el grupo está listo, False en caso contrario.
        """
        if not grupo.pk:
            return False
        
        return grupo.tutores.exists()
    
    @staticmethod
    def obtener_tutores_por_institucion(
        institucion: Institucion,
        solo_activos: bool = True
    ):
        """
        Obtiene los tutores de una institución.
        
        Returns:
            QuerySet: Vinculaciones TutorInstitucion de la institución.
        """
        queryset = TutorInstitucion.objects.select_related('tutor').filter(
            institucion=institucion
        )
        
        if solo_activos:
            queryset = queryset.filter(status='activo')
        
        return queryset.order_by('-fecha_vinculacion')
    
    @staticmethod
    def cambiar_estado_tutor(
        tutor: Tutor,
        institucion: Institucion,
        nuevo_status: str,
        usuario: Optional[User] = None
    ) -> TutorInstitucion:
        """
        Cambia el estado de un tutor en una institución específica.
        
        Returns:
            TutorInstitucion: La vinculación actualizada.
        """
        if nuevo_status not in ['activo', 'inactivo', 'suspendido']:
            raise ValidationError(
                f"Estado '{nuevo_status}' no válido. Use 'activo', 'inactivo' o 'suspendido'."
            )
        
        try:
            vinculacion = TutorInstitucion.objects.get(
                tutor=tutor,
                institucion=institucion
            )
        except TutorInstitucion.DoesNotExist:
            raise ValidationError(
                f"El tutor no está vinculado a la institución '{institucion.nombre}'."
            )
        
        with transaction.atomic():
            vinculacion.status = nuevo_status
            if nuevo_status == 'inactivo':
                vinculacion.fecha_desvinculacion = timezone.now()
            vinculacion.save(update_fields=['status', 'fecha_desvinculacion'])
        
        logger.info(
            f"[Tutor] Estado de tutor {tutor.get_nombre_completo()} en {institucion.nombre} "
            f"cambiado a {nuevo_status} por: {usuario.username if usuario else 'Sistema'}"
        )
        return vinculacion
