"""
Servicio de Admisión para Clubes.

Este módulo implementa el workflow de aprobación federado definido en permisos_clubes.md.

Reglas de Negocio Implementadas:
- Sección 6, Paso 1: El Solicitante crea registro con estado PENDIENTE_FILTRO.
- Sección 6, Paso 2: Solo la Institución Fundadora puede dar visto bueno.
- Sección 6, Paso 3: Solo el Ente Rector puede aprobar finalmente.
- Sección 6, Regla: Ninguna institución puede ser MIEMBRO_ACTIVO sin ambos checks.

Autor: Sistema de Registro
Fecha: 2026
"""

import logging
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.contrib.auth.models import User

from ..models import MembresiaClu, Club, Institucion
from ..notificaciones import (
    notificar_visto_bueno_fundadora,
    notificar_membresia_aprobada,
    notificar_membresia_rechazada,
)

logger = logging.getLogger(__name__)


class AdmissionService:
    """
    Servicio que maneja la transición de estados del proceso de admisión.
    
    Garantiza la integridad de datos y separación de responsabilidades
    entre la Institución Fundadora y el Ente Rector.
    
    Usage:
        >>> from registry.services import AdmissionService
        >>> # Crear solicitud
        >>> membresia = AdmissionService.crear_solicitud(club, institucion, datos)
        >>> # Dar visto bueno (Fundadora)
        >>> AdmissionService.dar_visto_bueno_fundadora(membresia, usuario)
        >>> # Aprobación final (Ente Rector)
        >>> AdmissionService.aprobar_ente_rector(membresia, usuario_rector)
    """
    
    @staticmethod
    def crear_solicitud(
        club: Club, 
        institucion_solicitante: Institucion, 
        datos_solicitud: dict,
        usuario_solicitante: User = None
    ) -> MembresiaClu:
        """
        Crea una nueva solicitud de membresía.
        
        Regla: permisos_clubes.md - Sección 6, Paso 1
        "Solicitante crea registro con estado PENDIENTE_FILTRO"
        
        Args:
            club: Club al que se desea unir.
            institucion_solicitante: Institución que solicita unirse.
            datos_solicitud: Diccionario con carta_intencion, propuesta_tecnica, 
                           representante_legal, tipo_linea.
            usuario_solicitante: Usuario que realiza la solicitud (opcional, para auditoría).
            
        Returns:
            MembresiaClu: La membresía creada con estado 'pendiente_filtro'.
            
        Raises:
            ValidationError: Si ya existe una solicitud activa o el club no acepta miembros.
            
        Example:
            >>> datos = {
            ...     'carta_intencion': 'Deseamos unirnos...',
            ...     'propuesta_tecnica': 'Nuestra propuesta...',
            ...     'representante_legal': 'Juan Pérez',
            ...     'tipo_linea': 'soporte'
            ... }
            >>> membresia = AdmissionService.crear_solicitud(club, institucion, datos)
        """
        # Validar que el club esté activo y aprobado
        if club.status != 'aprobado':
            raise ValidationError(
                f"El club '{club.nombre}' no está activo para recibir solicitudes."
            )
        
        # Validar que el club tenga cupos disponibles
        if club.cupo_maximo:
            miembros_actuales = club.membresias.filter(
                estado='miembro_activo'
            ).count()
            if miembros_actuales >= club.cupo_maximo:
                raise ValidationError(
                    f"El club '{club.nombre}' no tiene cupos disponibles."
                )
        
        # Validar que no exista solicitud activa
        if MembresiaClu.objects.filter(
            club=club,
            institucion=institucion_solicitante,
            estado__in=['pendiente_filtro', 'visto_bueno_fundadora']
        ).exists():
            raise ValidationError(
                f"Ya existe una solicitud activa para el club '{club.nombre}'."
            )
        
        # Validar que no sea ya miembro activo
        if MembresiaClu.objects.filter(
            club=club,
            institucion=institucion_solicitante,
            estado='miembro_activo'
        ).exists():
            raise ValidationError(
                f"La institución '{institucion_solicitante.nombre}' ya es miembro activo "
                f"del club '{club.nombre}'."
            )
        
        # Validar que no sea la institución fundadora (ya es miembro por defecto)
        if club.institucion_creadora == institucion_solicitante:
            raise ValidationError(
                "La institución fundadora no necesita solicitar membresía a su propio club."
            )
        
        with transaction.atomic():
            membresia = MembresiaClu.objects.create(
                club=club,
                institucion=institucion_solicitante,
                estado='pendiente_filtro',
                **datos_solicitud
            )
            
        logger.info(
            f"[Admisión] Solicitud creada: {institucion_solicitante.nombre} -> {club.nombre} "
            f"(Usuario: {usuario_solicitante.username if usuario_solicitante else 'Sistema'})"
        )
        return membresia
    
    @staticmethod
    def dar_visto_bueno_fundadora(
        membresia: MembresiaClu, 
        usuario: User, 
        observaciones: str = ""
    ) -> MembresiaClu:
        """
        La Institución Fundadora da visto bueno a la solicitud.
        
        Regla: permisos_clubes.md - Sección 6, Paso 2
        "Solo usuarios con rol Institucional y FUNDADORA pueden ejecutar este paso"
        "Cambio de estado: de PENDIENTE_FILTRO a VISTO_BUENO_FUNDADORA"
        
        Args:
            membresia: Membresía a aprobar.
            usuario: Usuario que da el visto bueno (debe ser de la Institución Fundadora).
            observaciones: Comentarios opcionales de la fundadora.
            
        Returns:
            MembresiaClu: La membresía actualizada con estado 'visto_bueno_fundadora'.
            
        Raises:
            PermissionDenied: Si el usuario no pertenece a la Institución Fundadora.
            ValidationError: Si el estado no permite esta acción.
            
        Example:
            >>> AdmissionService.dar_visto_bueno_fundadora(
            ...     membresia, 
            ...     request.user,
            ...     "Documentación completa, procede a revisión del Ente Rector."
            ... )
        """
        # Validación de permisos - Regla Sección 6
        if not AdmissionService._es_institucion_fundadora(membresia, usuario):
            raise PermissionDenied(
                "Solo la Institución Fundadora del club puede dar visto bueno a las solicitudes."
            )
        
        # Validación de estado
        if membresia.estado != 'pendiente_filtro':
            raise ValidationError(
                f"La membresía está en estado '{membresia.get_estado_display()}', "
                "no puede recibir visto bueno. Debe estar en 'Pendiente de Filtro'."
            )
        
        with transaction.atomic():
            membresia.visto_bueno_fundadora = True
            membresia.visto_bueno_fundadora_por = usuario
            membresia.visto_bueno_fundadora_fecha = timezone.now()
            membresia.observaciones_fundadora = observaciones
            membresia.estado = 'visto_bueno_fundadora'
            membresia.save()
        
        # Notificar al Ente Rector
        notificar_visto_bueno_fundadora(membresia)
            
        logger.info(
            f"[Admisión] Visto bueno fundadora otorgado por {usuario.username} "
            f"para {membresia.institucion.nombre} en {membresia.club.nombre}"
        )
        return membresia
    
    @staticmethod
    def rechazar_fundadora(
        membresia: MembresiaClu,
        usuario: User,
        motivo: str
    ) -> MembresiaClu:
        """
        La Institución Fundadora rechaza la solicitud.
        
        Regla: permisos_clubes.md - Sección 6, Paso 2 (alternativa)
        "Si rechaza, el estado cambia a RECHAZADO"
        
        Args:
            membresia: Membresía a rechazar.
            usuario: Usuario que rechaza (debe ser de la Fundadora).
            motivo: Motivo obligatorio del rechazo.
            
        Returns:
            MembresiaClu: La membresía actualizada con estado 'rechazada'.
            
        Raises:
            PermissionDenied: Si el usuario no pertenece a la Institución Fundadora.
            ValidationError: Si el estado no permite esta acción o falta el motivo.
            
        Example:
            >>> AdmissionService.rechazar_fundadora(
            ...     membresia,
            ...     request.user,
            ...     "La documentación presentada es insuficiente."
            ... )
        """
        if not AdmissionService._es_institucion_fundadora(membresia, usuario):
            raise PermissionDenied(
                "Solo la Institución Fundadora puede rechazar solicitudes."
            )
        
        if membresia.estado != 'pendiente_filtro':
            raise ValidationError(
                f"La membresía está en estado '{membresia.get_estado_display()}', "
                "no puede ser rechazada en este momento."
            )
        
        if not motivo or not motivo.strip():
            raise ValidationError(
                "El motivo de rechazo es obligatorio."
            )
        
        with transaction.atomic():
            membresia.estado = 'rechazada'
            membresia.visto_bueno_fundadora_por = usuario
            membresia.visto_bueno_fundadora_fecha = timezone.now()
            membresia.observaciones_fundadora = f"RECHAZADO: {motivo}"
            membresia.fecha_respuesta = timezone.now()
            membresia.save()
        
        # Notificar a la institución solicitante
        notificar_membresia_rechazada(membresia, motivo)
            
        logger.info(
            f"[Admisión] Membresía rechazada por fundadora ({usuario.username}): "
            f"{membresia.institucion.nombre} -> {membresia.club.nombre}. "
            f"Motivo: {motivo}"
        )
        return membresia
    
    @staticmethod
    def aprobar_ente_rector(
        membresia: MembresiaClu,
        usuario: User,
        observaciones: str = ""
    ) -> MembresiaClu:
        """
        El Ente Rector aprueba finalmente la membresía.
        
        Regla: permisos_clubes.md - Sección 6, Paso 3
        "Solo usuarios con rol RECTORA pueden ejecutar este paso"
        "Cambio de estado: de VISTO_BUENO_FUNDADORA a MIEMBRO_ACTIVO"
        
        Args:
            membresia: Membresía a aprobar.
            usuario: Usuario del Ente Rector (user_type='fed_central').
            observaciones: Comentarios opcionales del Ente Rector.
            
        Returns:
            MembresiaClu: La membresía actualizada con estado 'miembro_activo'.
            
        Raises:
            PermissionDenied: Si el usuario no es del Ente Rector.
            ValidationError: Si no tiene visto bueno de la fundadora o no hay cupos.
            
        Example:
            >>> AdmissionService.aprobar_ente_rector(
            ...     membresia,
            ...     request.user,
            ...     "Cumple con todos los requisitos normativos."
            ... )
        """
        # Validación de permisos - Regla Sección 6
        if not AdmissionService._es_ente_rector(usuario):
            raise PermissionDenied(
                "Solo el Ente Rector (Federación Central) puede dar la aprobación final."
            )
        
        # Validación de estado previo - Debe tener visto bueno
        if membresia.estado != 'visto_bueno_fundadora':
            raise ValidationError(
                "La membresía debe tener el visto bueno de la Institución Fundadora "
                "antes de ser aprobada por el Ente Rector. "
                f"Estado actual: {membresia.get_estado_display()}"
            )
        
        # Validar cupos disponibles (doble verificación)
        club = membresia.club
        if club.cupo_maximo:
            miembros_actuales = club.membresias.filter(
                estado='miembro_activo'
            ).count()
            if miembros_actuales >= club.cupo_maximo:
                raise ValidationError(
                    f"El club '{club.nombre}' ha alcanzado su cupo máximo de "
                    f"{club.cupo_maximo} miembros."
                )
        
        with transaction.atomic():
            membresia.aprobacion_ente_rector = True
            membresia.aprobacion_ente_rector_por = usuario
            membresia.aprobacion_ente_rector_fecha = timezone.now()
            membresia.observaciones_rector = observaciones
            membresia.estado = 'miembro_activo'
            membresia.fecha_respuesta = timezone.now()
            membresia.save()
            
            # Actualizar estado del club (puede cerrar cupos automáticamente)
            club.save()
        
        # Notificar a la institución solicitante
        notificar_membresia_aprobada(membresia)
            
        logger.info(
            f"[Admisión] Membresía APROBADA por Ente Rector ({usuario.username}): "
            f"{membresia.institucion.nombre} -> {membresia.club.nombre}"
        )
        return membresia
    
    @staticmethod
    def rechazar_ente_rector(
        membresia: MembresiaClu,
        usuario: User,
        motivo: str
    ) -> MembresiaClu:
        """
        El Ente Rector rechaza una solicitud con visto bueno.
        
        Regla: permisos_clubes.md - Sección 6, Paso 3 (alternativa)
        "El Ente Rector tiene visibilidad de todas las membresías en cualquier estado"
        
        Args:
            membresia: Membresía a rechazar.
            usuario: Usuario del Ente Rector.
            motivo: Motivo obligatorio del rechazo.
            
        Returns:
            MembresiaClu: La membresía actualizada con estado 'rechazada'.
            
        Raises:
            PermissionDenied: Si el usuario no es del Ente Rector.
            ValidationError: Si no tiene visto bueno o falta el motivo.
            
        Example:
            >>> AdmissionService.rechazar_ente_rector(
            ...     membresia,
            ...     request.user,
            ...     "No cumple con los requisitos normativos vigentes."
            ... )
        """
        if not AdmissionService._es_ente_rector(usuario):
            raise PermissionDenied(
                "Solo el Ente Rector puede realizar esta acción."
            )
        
        # El Ente Rector puede rechazar en cualquier estado del flujo federado
        if membresia.estado not in ['pendiente_filtro', 'visto_bueno_fundadora']:
            raise ValidationError(
                "Solo se pueden rechazar solicitudes que estén en proceso. "
                f"Estado actual: {membresia.get_estado_display()}"
            )
        
        if not motivo or not motivo.strip():
            raise ValidationError(
                "El motivo de rechazo es obligatorio."
            )
        
        with transaction.atomic():
            membresia.estado = 'rechazada'
            membresia.aprobacion_ente_rector_por = usuario
            membresia.aprobacion_ente_rector_fecha = timezone.now()
            membresia.observaciones_rector = f"RECHAZADO: {motivo}"
            membresia.fecha_respuesta = timezone.now()
            membresia.save()
        
        # Notificar a la institución solicitante
        notificar_membresia_rechazada(membresia, motivo)
            
        logger.info(
            f"[Admisión] Membresía RECHAZADA por Ente Rector ({usuario.username}): "
            f"{membresia.institucion.nombre} -> {membresia.club.nombre}. "
            f"Motivo: {motivo}"
        )
        return membresia
    
    @staticmethod
    def retirar_solicitud(
        membresia: MembresiaClu,
        usuario: User,
        motivo: str = ""
    ) -> MembresiaClu:
        """
        El solicitante retira su solicitud antes de ser procesada.
        
        Args:
            membresia: Membresía a retirar.
            usuario: Usuario solicitante.
            motivo: Motivo opcional del retiro.
            
        Returns:
            MembresiaClu: La membresía actualizada.
            
        Raises:
            PermissionDenied: Si el usuario no es de la institución solicitante.
            ValidationError: Si la solicitud ya fue procesada.
        """
        if not AdmissionService._es_institucion_solicitante(membresia, usuario):
            raise PermissionDenied(
                "Solo la institución solicitante puede retirar su solicitud."
            )
        
        if membresia.estado not in ['pendiente_filtro', 'visto_bueno_fundadora']:
            raise ValidationError(
                "No se puede retirar una solicitud que ya fue procesada."
            )
        
        with transaction.atomic():
            membresia.estado = 'rechazada'
            membresia.observaciones = f"RETIRADA POR SOLICITANTE: {motivo}" if motivo else "RETIRADA POR SOLICITANTE"
            membresia.fecha_respuesta = timezone.now()
            membresia.save()
            
        logger.info(
            f"[Admisión] Solicitud retirada por {usuario.username}: "
            f"{membresia.institucion.nombre} -> {membresia.club.nombre}"
        )
        return membresia
    
    # === Métodos de validación de permisos ===
    
    @staticmethod
    def _es_institucion_fundadora(membresia: MembresiaClu, usuario: User) -> bool:
        """
        Verifica si el usuario pertenece a la Institución Fundadora del club.
        
        Regla: permisos_clubes.md - Sección 6, Regla de Negocio
        "Solo usuarios con rol Institucional y FUNDADORA pueden ejecutar el paso 2"
        
        Args:
            membresia: Membresía en cuestión.
            usuario: Usuario a verificar.
            
        Returns:
            bool: True si el usuario pertenece a la institución fundadora.
        """
        if not hasattr(usuario, 'userprofile'):
            return False
        
        if not usuario.userprofile.institution:
            return False
        
        institucion_usuario = usuario.userprofile.institution
        return institucion_usuario == membresia.club.institucion_creadora
    
    @staticmethod
    def _es_ente_rector(usuario: User) -> bool:
        """
        Verifica si el usuario tiene rol de Ente Rector.
        
        Regla: permisos_clubes.md - Sección 6, Regla de Negocio
        "Solo usuarios con rol RECTORA ente rector pueden ejecutar el paso 3"
        
        Args:
            usuario: Usuario a verificar.
            
        Returns:
            bool: True si el usuario es del Ente Rector (fed_central).
        """
        if not hasattr(usuario, 'userprofile'):
            return False
        
        return usuario.userprofile.user_type == 'fed_central'
    
    @staticmethod
    def _es_institucion_solicitante(membresia: MembresiaClu, usuario: User) -> bool:
        """
        Verifica si el usuario pertenece a la institución solicitante.
        
        Args:
            membresia: Membresía en cuestión.
            usuario: Usuario a verificar.
            
        Returns:
            bool: True si el usuario pertenece a la institución solicitante.
        """
        if not hasattr(usuario, 'userprofile'):
            return False
        
        if not usuario.userprofile.institution:
            return False
        
        return usuario.userprofile.institution == membresia.institucion
    
    # === Métodos de consulta ===
    
    @staticmethod
    def obtener_solicitudes_pendientes_fundadora(usuario: User) -> list:
        """
        Obtiene las solicitudes pendientes de visto bueno para los clubes de la fundadora.
        
        Args:
            usuario: Usuario de la institución fundadora.
            
        Returns:
            QuerySet: Membresías pendientes de filtro.
        """
        if not hasattr(usuario, 'userprofile') or not usuario.userprofile.institution:
            return MembresiaClu.objects.none()
        
        return MembresiaClu.objects.filter(
            club__institucion_creadora=usuario.userprofile.institution,
            estado='pendiente_filtro'
        ).select_related('club', 'institucion')
    
    @staticmethod
    def obtener_solicitudes_pendientes_rector() -> list:
        """
        Obtiene todas las solicitudes con visto bueno pendientes del Ente Rector.
        
        Regla: permisos_clubes.md - Sección 6
        "El Ente Rector tiene visibilidad de todas las membresías en cualquier estado"
        
        Returns:
            QuerySet: Membresías con visto bueno pendientes de aprobación final.
        """
        return MembresiaClu.objects.filter(
            estado='visto_bueno_fundadora'
        ).select_related('club', 'institucion', 'visto_bueno_fundadora_por')
    
    @staticmethod
    def obtener_todas_solicitudes_rector() -> list:
        """
        Obtiene TODAS las solicitudes para supervisión del Ente Rector.
        
        Regla: permisos_clubes.md - Sección 6
        "El Ente Rector tiene visibilidad de todas las membresías en cualquier estado para supervisión"
        
        Returns:
            QuerySet: Todas las membresías.
        """
        return MembresiaClu.objects.all().select_related(
            'club', 'institucion',
            'visto_bueno_fundadora_por',
            'aprobacion_ente_rector_por'
        )
