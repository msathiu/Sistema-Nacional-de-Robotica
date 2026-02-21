"""Utilidades para el sistema de notificaciones internas."""

from django.contrib.auth.models import User
from .models import Notificacion, Club


def crear_notificacion(destinatario, tipo, titulo, mensaje, club=None):
    """
    Crea una notificación interna para un usuario.
    
    Args:
        destinatario: Usuario que recibirá la notificación
        tipo: Tipo de notificación (ver Notificacion.TIPO_CHOICES)
        titulo: Título de la notificación
        mensaje: Mensaje completo
        club: Club relacionado (opcional)
    
    Returns:
        Notificacion: Objeto de notificación creado
    """
    return Notificacion.objects.create(
        destinatario=destinatario,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        club=club
    )


def notificar_club_aprobado(club):
    """Notifica a la institución que su club fue aprobado."""
    if club.coordinador:
        crear_notificacion(
            destinatario=club.coordinador,
            tipo='club_aprobado',
            titulo=f'✅ Club "{club.nombre}" Aprobado',
            mensaje=f'Tu club "{club.nombre}" ha sido aprobado por la federación y ahora está visible públicamente.',
            club=club
        )


def notificar_club_rechazado(club, observaciones=''):
    """Notifica a la institución que su club fue rechazado."""
    if club.coordinador:
        mensaje = f'Tu club "{club.nombre}" ha sido rechazado por la federación.'
        if observaciones:
            mensaje += f'\n\nObservaciones: {observaciones}'
        
        crear_notificacion(
            destinatario=club.coordinador,
            tipo='club_rechazado',
            titulo=f'❌ Club "{club.nombre}" Rechazado',
            mensaje=mensaje,
            club=club
        )


def notificar_solicitud_eliminacion(solicitud):
    """Notifica a la federación sobre una solicitud de eliminación."""
    # Notificar a todos los staff members
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    
    for staff in staff_users:
        crear_notificacion(
            destinatario=staff,
            tipo='solicitud_eliminacion',
            titulo=f'🗑️ Solicitud de Eliminación: {solicitud.club.nombre}',
            mensaje=f'La institución "{solicitud.institucion_solicitante.nombre}" solicita eliminar el club "{solicitud.club.nombre}".\n\nMotivo: {solicitud.motivo}',
            club=solicitud.club
        )


def notificar_eliminacion_aprobada(solicitud):
    """Notifica a la institución que su solicitud de eliminación fue aprobada."""
    if solicitud.club.coordinador:
        crear_notificacion(
            destinatario=solicitud.club.coordinador,
            tipo='eliminacion_aprobada',
            titulo=f'✅ Eliminación Aprobada: {solicitud.club.nombre}',
            mensaje=f'Tu solicitud de eliminación del club "{solicitud.club.nombre}" ha sido aprobada por la federación. El club ha sido eliminado del sistema.',
            club=solicitud.club
        )


def notificar_eliminacion_rechazada(solicitud):
    """Notifica a la institución que su solicitud de eliminación fue rechazada."""
    if solicitud.club.coordinador:
        mensaje = f'Tu solicitud de eliminación del club "{solicitud.club.nombre}" ha sido rechazada por la federación.'
        if solicitud.observaciones_federacion:
            mensaje += f'\n\nObservaciones: {solicitud.observaciones_federacion}'
        
        crear_notificacion(
            destinatario=solicitud.club.coordinador,
            tipo='eliminacion_rechazada',
            titulo=f'❌ Eliminación Rechazada: {solicitud.club.nombre}',
            mensaje=mensaje,
            club=solicitud.club
        )


def notificar_salida_club(membresia, motivo=''):
    """Notifica al propietario del club que una institución se retiró.
    
    Args:
        membresia: Objeto MembresiaClu con la información de la salida
        motivo: Motivo opcional proporcionado por la institución
    """
    club = membresia.club
    institucion_saliente = membresia.institucion
    
    # Notificar al coordinador del club (propietario)
    if club.coordinador:
        mensaje = f'La institución "{institucion_saliente.nombre}" se ha retirado del club "{club.nombre}".'
        
        if motivo:
            mensaje += f'\n\n📝 Motivo: {motivo}'
        else:
            mensaje += '\n\n(No se proporcionó motivo específico)'
        
        # Información adicional sobre cupos
        miembros_actuales = club.membresias.filter(estado="aprobada").count()
        mensaje += f'\n\n📊 Miembros actuales: {miembros_actuales}'
        if club.cupo_maximo:
            cupos_disponibles = club.cupo_maximo - miembros_actuales
            mensaje += f' / {club.cupo_maximo} (Cupos disponibles: {cupos_disponibles})'
        
        crear_notificacion(
            destinatario=club.coordinador,
            tipo='salida_club',
            titulo=f'🚪 Salida de Miembro: {institucion_saliente.nombre}',
            mensaje=mensaje,
            club=club
        )


def notificar_reenvio_club(club, num_intento):
    """Notifica a la federación que un club rechazado ha sido reenviado.
    
    Args:
        club: Objeto Club que se reenvía
        num_intento: Número de intento de reenvío
    """
    # Notificar a todos los staff members (federación)
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    
    for staff in staff_users:
        mensaje = f'La institución "{club.institucion_creadora.nombre}" ha reenviado el club "{club.nombre}" para revisión.'
        mensaje += f'\n\n🔄 Intento de reenvío: #{num_intento}'
        mensaje += f'\n\n📝 El club fue corregido después del último rechazo y requiere una nueva revisión.'
        
        # Obtener último rechazo
        ultimo_rechazo = club.obtener_ultimo_rechazo()
        if ultimo_rechazo and ultimo_rechazo.observaciones:
            mensaje += f'\n\n⚠️ Motivo del último rechazo:\n{ultimo_rechazo.observaciones[:200]}...'
        
        crear_notificacion(
            destinatario=staff,
            tipo='sistema',
            titulo=f'🔄 Reenvío de Club: {club.nombre} (Intento #{num_intento})',
            mensaje=mensaje,
            club=club
        )

