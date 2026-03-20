"""Vistas legacy de eventos para compatibilidad de rutas antiguas."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models import EstadoEvento, Evento


@staff_member_required
def admin_todos_eventos(request):
    """
    Ruta legacy: redirige al tablero operativo unificado del módulo.
    """
    return redirect("admin_eventos")


@staff_member_required
def aprobar_evento(request, evento_id):
    """
    Abre cualquier tipo de evento desde revisión.
    """
    evento = get_object_or_404(Evento, id=evento_id)

    if evento.estado_evento != EstadoEvento.REVISION:
        messages.error(request, "Solo se pueden aprobar eventos en estado revisión.")
        return redirect("admin_eventos")

    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()

        with transaction.atomic():
            evento.estado_evento = EstadoEvento.ABIERTO
            evento.aprobado_por = request.user
            evento.observaciones_aprobacion = observaciones
            evento.fecha_aprobacion = timezone.now()

            if evento.tipo_evento == "institucional":
                evento.es_publico = True
                evento.audiencia = "publica"

            evento.save(
                update_fields=[
                    "estado_evento",
                    "aprobado_por",
                    "observaciones_aprobacion",
                    "fecha_aprobacion",
                    "es_publico",
                    "audiencia",
                ]
            )

            messages.success(
                request,
                f'Evento "{evento.nombre}" abierto exitosamente. '
                f"Ahora visible para: {evento.get_audiencia_display()}",
            )

    return redirect("admin_eventos")


@staff_member_required
def rechazar_evento(request, evento_id):
    """
    Rechaza un evento en revisión y lo deja editable para la institución.
    """
    evento = get_object_or_404(Evento, id=evento_id)

    if evento.estado_evento != EstadoEvento.REVISION:
        messages.error(request, "Solo se pueden rechazar eventos en estado revisión.")
        return redirect("admin_eventos")

    if request.method == "POST":
        observaciones = request.POST.get("observaciones", "").strip()

        if not observaciones:
            messages.error(request, "Debes especificar el motivo del rechazo.")
            return redirect("admin_eventos")

        with transaction.atomic():
            evento.estado_evento = EstadoEvento.RECHAZADO
            evento.observaciones_aprobacion = observaciones
            evento.observacion_estado = observaciones
            evento.es_publico = False
            evento.save(
                update_fields=[
                    "estado_evento",
                    "observaciones_aprobacion",
                    "observacion_estado",
                    "es_publico",
                ]
            )

            messages.warning(
                request,
                f'Evento "{evento.nombre}" rechazado. La institución puede editarlo y enviarlo nuevamente.',
            )

    return redirect("admin_eventos")
