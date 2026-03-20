from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from registry.models import ESTADOS_FINALES, EstadoEvento, Evento


class Command(BaseCommand):
    help = "Recalcula estados de eventos segun la fecha actual."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los cambios sin persistirlos.",
        )
        parser.add_argument(
            "--incluir-pausados",
            action="store_true",
            help=(
                "Finaliza automaticamente eventos pausados cuya fecha ya vencio. "
                "Por defecto no altera pausados vencidos."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        incluir_pausados = options["incluir_pausados"]
        hoy = timezone.localdate()

        candidatos = Evento.objects.exclude(
            estado_evento__in=ESTADOS_FINALES
        ).order_by("fecha", "id")

        revisados = 0
        actualizados = 0

        for evento in candidatos:
            revisados += 1
            nuevo_estado = self._calcular_nuevo_estado(
                evento,
                hoy=hoy,
                incluir_pausados=incluir_pausados,
            )

            if nuevo_estado == evento.estado_evento:
                continue

            actualizados += 1
            self.stdout.write(
                f"[{evento.id}] {evento.nombre}: {evento.estado_evento} -> {nuevo_estado}"
            )

            if dry_run:
                continue

            with transaction.atomic():
                evento.estado_evento = nuevo_estado
                evento.save(update_fields=["estado_evento"])

        resumen = (
            f"Eventos revisados: {revisados}. "
            f"Eventos {'a actualizar' if dry_run else 'actualizados'}: {actualizados}."
        )
        self.stdout.write(self.style.SUCCESS(resumen))

        if not incluir_pausados:
            self.stdout.write(
                self.style.WARNING(
                    "Los eventos pausados con fecha vencida no se tocaron. "
                    "Usa --incluir-pausados si la politica del negocio lo permite."
                )
            )

    def _calcular_nuevo_estado(self, evento, *, hoy, incluir_pausados):
        if evento.estado_evento == EstadoEvento.ABIERTO and evento.fecha == hoy:
            return EstadoEvento.EN_PROCESO

        if evento.fecha < hoy:
            if evento.estado_evento in [EstadoEvento.ABIERTO, EstadoEvento.EN_PROCESO]:
                return EstadoEvento.FINALIZADO
            if incluir_pausados and evento.estado_evento == EstadoEvento.PAUSADO:
                return EstadoEvento.FINALIZADO

        return evento.estado_evento
