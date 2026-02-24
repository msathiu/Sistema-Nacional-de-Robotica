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

from ..models import Tutor, Grupo, Institucion

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
    def registrar_tutor(
        institucion: Institucion,
        datos_tutor: dict,
        usuario_solicitante: Optional[User] = None
    ) -> Tutor:
        """
        Registra un nuevo tutor validando que la cédula no esté duplicada.
        
        Args:
            institucion: Institución donde trabaja el tutor.
            datos_tutor: Diccionario con nombres, apellidos, cedula, telefono,
                        email, profesion, experiencia, status.
            usuario_solicitante: Usuario que registra (para auditoría).
            
        Returns:
            Tutor: El tutor creado.
            
        Raises:
            ValidationError: Si la cédula ya existe o faltan datos obligatorios.
            
        Example:
            >>> datos = {
            ...     'nombres': 'Juan',
            ...     'apellidos': 'Pérez',
            ...     'cedula': 'V12345678',
            ...     'telefono': '0414-1234567',
            ...     'email': 'juan@example.com',
            ...     'profesion': 'Ingeniero',
            ...     'experiencia': '5 años en robótica educativa',
            ...     'status': 'activo'
            ... }
            >>> tutor = TutorService.registrar_tutor(institucion, datos)
        """
        # Validar que la cédula no exista
        cedula = datos_tutor.get('cedula')
        if not cedula:
            raise ValidationError("La cédula es obligatoria.")
        
        if Tutor.objects.filter(cedula=cedula).exists():
            raise ValidationError(
                f"Ya existe un tutor registrado con la cédula '{cedula}'."
            )
        
        # Validar campos obligatorios
        campos_obligatorios = ['nombres', 'apellidos', 'telefono', 'email']
        for campo in campos_obligatorios:
            if not datos_tutor.get(campo):
                raise ValidationError(f"El campo '{campo}' es obligatorio.")
        
        with transaction.atomic():
            tutor = Tutor.objects.create(
                institucion=institucion,
                nombres=datos_tutor['nombres'],
                apellidos=datos_tutor['apellidos'],
                cedula=cedula,
                telefono=datos_tutor['telefono'],
                email=datos_tutor['email'],
                profesion=datos_tutor.get('profesion', ''),
                experiencia=datos_tutor.get('experiencia', ''),
                status=datos_tutor.get('status', 'activo'),
            )
        
        logger.info(
            f"[Tutor] Tutor registrado: {tutor.get_nombre_completo()} "
            f"(Cédula: {tutor.cedula}) por usuario: "
            f"{usuario_solicitante.username if usuario_solicitante else 'Sistema'}"
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
        
        Usa transaction.atomic para garantizar integridad.
        
        Args:
            tutor: Tutor a asignar.
            grupo: Grupo al que se asignará el tutor.
            usuario: Usuario que realiza la asignación (para auditoría).
            
        Raises:
            ValidationError: Si el tutor está inactivo.
            
        Example:
            >>> TutorService.asignar_tutor_a_grupo(tutor, grupo, request.user)
        """
        # Validar que el tutor esté activo
        if tutor.status != 'activo':
            raise ValidationError(
                f"El tutor '{tutor.get_nombre_completo()}' está inactivo "
                "y no puede ser asignado a grupos."
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
        
        Args:
            institucion: Institución para filtrar tutores.
            solo_activos: Si True, solo retorna tutores activos.
            
        Returns:
            QuerySet: Tutores de la institución.
        """
        queryset = Tutor.objects.select_related('institucion').filter(
            institucion=institucion
        )
        
        if solo_activos:
            queryset = queryset.filter(status='activo')
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def cambiar_estado_tutor(
        tutor: Tutor,
        nuevo_status: str,
        usuario: Optional[User] = None
    ) -> Tutor:
        """
        Cambia el estado de un tutor (activo/inactivo).
        
        Args:
            tutor: Tutor a actualizar.
            nuevo_status: Nuevo estado ('activo' o 'inactivo').
            usuario: Usuario que realiza el cambio (para auditoría).
            
        Returns:
            Tutor: El tutor actualizado.
            
        Raises:
            ValidationError: Si el estado no es válido.
        """
        if nuevo_status not in ['activo', 'inactivo']:
            raise ValidationError(
                f"Estado '{nuevo_status}' no válido. Use 'activo' o 'inactivo'."
            )
        
        with transaction.atomic():
            tutor.status = nuevo_status
            tutor.save(update_fields=['status'])
        
        logger.info(
            f"[Tutor] Estado de tutor {tutor.get_nombre_completo()} cambiado a "
            f"{nuevo_status} por: {usuario.username if usuario else 'Sistema'}"
        )
        return tutor
