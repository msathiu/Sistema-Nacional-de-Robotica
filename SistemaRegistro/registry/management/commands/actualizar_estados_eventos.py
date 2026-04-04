from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import logging

from registry.models import ESTADOS_FINALES, EstadoEvento, Evento

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Recalcula estados de eventos segun la fecha actual. Cumple con EVENTO.md."

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
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Muestra informacion detallada de cada evento revisado.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        incluir_pausados = options["incluir_pausados"]
        verbose = options["verbose"]
        hoy = timezone.localdate()

        self.stdout.write(self.style.HTTP_INFO(f"=== Inicio de actualizacion de estados ==="))
        self.stdout.write(f"Fecha actual: {hoy}")
        self.stdout.write(f" dry_run: {dry_run}")
        self.stdout.write(f" incluir_pausados: {incluir_pausados}")
        self.stdout.write("")

        candidatos = Evento.objects.exclude(
            estado_evento__in=ESTADOS_FINALES
        ).select_related("institucion", "club_organizador").order_by("fecha", "id")

        revisados = 0
        actualizados = 0
        errores = 0

        for evento in candidatos:
            revisados += 1
            fecha_inicio = evento.fecha
            fecha_fin = evento.fecha_hasta or evento.fecha
            
            if verbose:
                self.stdout.write(
                    f"[{evento.id}] '{evento.nombre[:40]}...' | "
                    f"estado={evento.estado_evento} | "
                    f"fecha={fecha_inicio} a {fecha_fin}"
                )

            nuevo_estado = self._calcular_nuevo_estado(
                evento,
                hoy=hoy,
                incluir_pausados=incluir_pausados,
            )

            if nuevo_estado == evento.estado_evento:
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"  -> Sin cambio"))
                continue

            actualizados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"[{evento.id}] {evento.nombre[:50]}: "
                    f"{evento.estado_evento} -> {nuevo_estado}"
                )
            )
            
            logger.info(
                f"Evento {evento.id} '{evento.nombre}': "
                f"cambio de estado de {evento.estado_evento} a {nuevo_estado}"
            )

            if dry_run:
                continue

            try:
                with transaction.atomic():
                    evento.estado_evento = nuevo_estado
                    evento.save(update_fields=["estado_evento"])
                    # Al iniciar el evento, generar registros de asistencia pendientes
                    if nuevo_estado == EstadoEvento.EN_PROCESO:
                        from users.services.evento_service import EventoService
                        EventoService.generar_asistencias_pendientes(evento)
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"  ERROR al actualizar: {str(e)}")
                )
                logger.error(f"Error al actualizar evento {evento.id}: {str(e)}")

        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("=== Resumen ==="))
        self.stdout.write(f"Eventos revisados: {revisados}")
        self.stdout.write(f"Eventos actualizados: {actualizados}")
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"Errores: {errores}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: No se persistieron cambios"))
        
        if not incluir_pausados:
            self.stdout.write(
                self.style.WARNING(
                    "Nota: Los eventos pausados con fecha vencida no se tocaron. "
                    "Usa --incluir-pausados si la politica lo permite."
                )
            )

        logger.info(
            f"Comando actualizar_estados_eventos completado: "
            f"revisados={revisados}, actualizados={actualizados}, errores={errores}"
        )

    def _calcular_nuevo_estado(self, evento, *, hoy, incluir_pausados):
        """
        Calcula el nuevo estado del evento segun las reglas de EVENTO.md:
        
        - abierto -> en_proceso: cuando fecha <= hoy <= fecha_hasta
        - abierto -> finalizado: cuando fecha_hasta < hoy
        - en_proceso -> finalizado: cuando fecha_hasta < hoy  
        - pausado -> finalizado: solo si incluir_pausados=True y fecha_hasta < hoy
        """
        fecha_fin = evento.fecha_hasta or evento.fecha

        if evento.estado_evento == EstadoEvento.ABIERTO:
            if evento.fecha <= hoy <= fecha_fin:
                return EstadoEvento.EN_PROCESO
            elif fecha_fin < hoy:
                return EstadoEvento.FINALIZADO

        if evento.estado_evento == EstadoEvento.EN_PROCESO:
            if fecha_fin < hoy:
                return EstadoEvento.FINALIZADO

        if evento.estado_evento == EstadoEvento.PAUSADO:
            if incluir_pausados and fecha_fin < hoy:
                return EstadoEvento.FINALIZADO

        return evento.estado_evento
