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
        destinatario=destinatario, tipo=tipo, titulo=titulo, mensaje=mensaje, club=club
    )


def notificar_club_aprobado(club):
    """Notifica a la institución que su club fue aprobado."""
    if club.coordinador:
        crear_notificacion(
            destinatario=club.coordinador,
            tipo="club_aprobado",
            titulo=f'✅ Club "{club.nombre}" Aprobado',
            mensaje=f'Tu club "{club.nombre}" ha sido aprobado por la federación y ahora está visible públicamente.',
            club=club,
        )


def notificar_club_rechazado(club, observaciones=""):
    """Notifica a la institución que su club fue rechazado."""
    if club.coordinador:
        mensaje = f'Tu club "{club.nombre}" ha sido rechazado por la federación.'
        if observaciones:
            mensaje += f"\n\nObservaciones: {observaciones}"

        crear_notificacion(
            destinatario=club.coordinador,
            tipo="club_rechazado",
            titulo=f'❌ Club "{club.nombre}" Rechazado',
            mensaje=mensaje,
            club=club,
        )


def notificar_solicitud_eliminacion(solicitud):
    """Notifica a la federación sobre una solicitud de eliminación."""
    # Notificar a todos los staff members
    staff_users = User.objects.filter(is_staff=True, is_active=True)

    for staff in staff_users:
        crear_notificacion(
            destinatario=staff,
            tipo="solicitud_eliminacion",
            titulo=f"🗑️ Solicitud de Eliminación: {solicitud.club.nombre}",
            mensaje=f'La institución "{solicitud.institucion_solicitante.nombre}" solicita eliminar el club "{solicitud.club.nombre}".\n\nMotivo: {solicitud.motivo}',
            club=solicitud.club,
        )


def notificar_eliminacion_aprobada(solicitud):
    """Notifica a la institución que su solicitud de eliminación fue aprobada."""
    if solicitud.club.coordinador:
        crear_notificacion(
            destinatario=solicitud.club.coordinador,
            tipo="eliminacion_aprobada",
            titulo=f"✅ Eliminación Aprobada: {solicitud.club.nombre}",
            mensaje=f'Tu solicitud de eliminación del club "{solicitud.club.nombre}" ha sido aprobada por la federación. El club ha sido eliminado del sistema.',
            club=solicitud.club,
        )


def notificar_eliminacion_rechazada(solicitud):
    """Notifica a la institución que su solicitud de eliminación fue rechazada."""
    if solicitud.club.coordinador:
        mensaje = f'Tu solicitud de eliminación del club "{solicitud.club.nombre}" ha sido rechazada por la federación.'
        if solicitud.observaciones_federacion:
            mensaje += f"\n\nObservaciones: {solicitud.observaciones_federacion}"

        crear_notificacion(
            destinatario=solicitud.club.coordinador,
            tipo="eliminacion_rechazada",
            titulo=f"❌ Eliminación Rechazada: {solicitud.club.nombre}",
            mensaje=mensaje,
            club=solicitud.club,
        )


def notificar_transferencia_propietario(club, antigua_institucion, nueva_institucion):
    """Notifica sobre transferencia de propiedad del club.

    Args:
        club: Objeto Club que fue transferido
        antigua_institucion: Institución que era propietaria
        nueva_institucion: Nueva institución propietaria
    """
    # Notificar a la nueva institución
    if hasattr(nueva_institucion, "usuario") and nueva_institucion.usuario:
        crear_notificacion(
            destinatario=nueva_institucion.usuario,
            tipo="sistema",
            titulo=f"👑 Nuevo Propietario: {club.nombre}",
            mensaje=f'La federación te ha asignado como nuevo propietario del club "{club.nombre}".\n\n'
            f"Anteriormente eras miembro del club. Ahoratendrás acceso completo a la gestión del club.",
            club=club,
        )

    # Notificar a los demás miembros
    miembros = club.membresias.filter(estado="miembro_activo").exclude(
        institucion=nueva_institucion
    )
    for membresia in miembros:
        if hasattr(membresia.institucion, "usuario") and membresia.institucion.usuario:
            crear_notificacion(
                destinatario=membresia.institucion.usuario,
                tipo="sistema",
                titulo=f"👑 Cambio de Propietario: {club.nombre}",
                mensaje=f'La federación ha aprobado un cambio de propietario en el club "{club.nombre}".\n\n'
                f"El nuevo propietario es: {nueva_institucion.nombre}",
                club=club,
            )


def notificar_salida_club(membresia, motivo=""):
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
            mensaje += f"\n\n📝 Motivo: {motivo}"
        else:
            mensaje += "\n\n(No se proporcionó motivo específico)"

        # Información adicional sobre cupos
        miembros_actuales = club.membresias.filter(estado="miembro_activo").count()
        mensaje += f"\n\n📊 Miembros actuales: {miembros_actuales}"
        if club.cupo_maximo:
            cupos_disponibles = club.cupo_maximo - miembros_actuales
            mensaje += f" / {club.cupo_maximo} (Cupos disponibles: {cupos_disponibles})"

        crear_notificacion(
            destinatario=club.coordinador,
            tipo="salida_club",
            titulo=f"🚪 Salida de Miembro: {institucion_saliente.nombre}",
            mensaje=mensaje,
            club=club,
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
        mensaje += f"\n\n🔄 Intento de reenvío: #{num_intento}"
        mensaje += f"\n\n📝 El club fue corregido después del último rechazo y requiere una nueva revisión."

        # Obtener último rechazo
        ultimo_rechazo = club.obtener_ultimo_rechazo()
        if ultimo_rechazo and ultimo_rechazo.observaciones:
            mensaje += f"\n\n⚠️ Motivo del último rechazo:\n{ultimo_rechazo.observaciones[:200]}..."

        crear_notificacion(
            destinatario=staff,
            tipo="sistema",
            titulo=f"🔄 Reenvío de Club: {club.nombre} (Intento #{num_intento})",
            mensaje=mensaje,
            club=club,
        )


def notificar_visto_bueno_fundadora(membresia):
    """Notifica que una fundadora ha dado visto bueno a una membresía.

    Args:
        membresia: Objeto MembresiaClu con el visto bueno
    """
    club = membresia.club
    institucion = membresia.institucion

    # Notificar al coordinador del club
    if club.coordinador:
        mensaje = (
            f'La institución fundadora "{institucion.nombre}" ha dado visto bueno '
        )
        mensaje += f'para unirse al club "{club.nombre}".'
        mensaje += f"\n\n📊 La membresía está lista para ser procesada."

        crear_notificacion(
            destinatario=club.coordinador,
            tipo="membresia_aprobada",
            titulo=f"✅ Visto Bueno de Fundadora: {institucion.nombre}",
            mensaje=mensaje,
            club=club,
        )


def notificar_membresia_aprobada(membresia):
    """Notifica a la institución que su membresía fue aprobada.

    Args:
        membresia: Objeto MembresiaClu aprobado
    """
    club = membresia.club
    institucion = membresia.institucion

    # Notificar al usuario representante de la institución
    if hasattr(institucion, "usuario") and institucion.usuario:
        mensaje = f'Tu solicitud de membresía al club "{club.nombre}" ha sido aprobada.'
        mensaje += f"\n\n🎉 ¡Bienvenido al club!"

        crear_notificacion(
            destinatario=institucion.usuario,
            tipo="membresia_aprobada",
            titulo=f"✅ Membresía Aprobada: {club.nombre}",
            mensaje=mensaje,
            club=club,
        )


def notificar_membresia_rechazada(membresia, motivo=""):
    """Notifica a la institución que su membresía fue rechazada.

    Args:
        membresia: Objeto MembresiaClu rechazado
        motivo: Motivo del rechazo (opcional)
    """
    club = membresia.club
    institucion = membresia.institucion

    # Notificar al usuario representante de la institución
    if hasattr(institucion, "usuario") and institucion.usuario:
        mensaje = (
            f'Tu solicitud de membresía al club "{club.nombre}" ha sido rechazada.'
        )

        if motivo:
            mensaje += f"\n\n📝 Motivo: {motivo}"

        crear_notificacion(
            destinatario=institucion.usuario,
            tipo="membresia_rechazada",
            titulo=f"❌ Membresía Rechazada: {club.nombre}",
            mensaje=mensaje,
            club=club,
        )


def notificar_institucion_activada(institucion):
    """Notifica a la institución que su cuenta ha sido activada y aprobada.

    Args:
        institucion: Objeto Institucion activado
    """
    if hasattr(institucion, "usuario") and institucion.usuario:
        mensaje = f'Tu institución "{institucion.nombre}" ha sido aprobada y activada exitosamente.'
        mensaje += f"\n\n✅ Tu código RNR oficial es: {institucion.codigo}"
        mensaje += f"\n\n🔑 Bienvenido."

        crear_notificacion(
            destinatario=institucion.usuario,
            tipo="sistema",
            titulo=f"✅ Institución Activada: {institucion.nombre}",
            mensaje=mensaje,
        )
