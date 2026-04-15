"""
Comando de Django para verificar instituciones pendientes
Uso: python manage.py verificar_instituciones
"""
from django.core.management.base import BaseCommand
from registry.models import Institucion


class Command(BaseCommand):
    help = "Verifica el estado de las instituciones"

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("VERIFICACIÓN DE INSTITUCIONES")
        self.stdout.write("=" * 70)

        # Todas las instituciones no eliminadas
        instituciones = Institucion.objects.filter(eliminado=False)
        self.stdout.write(
            f"\nTotal instituciones (no eliminadas): {instituciones.count()}"
        )

        # Agrupar por estatus
        self.stdout.write("\n--- Por estatus ---")
        for estatus in ["pendiente", "aprobado", "rechazado"]:
            count = instituciones.filter(estatus=estatus).count()
            self.stdout.write(f"  {estatus}: {count}")

        # Agrupar por activa
        self.stdout.write("\n--- Por campo activa ---")
        self.stdout.write(f"  activa=True: {instituciones.filter(activa=True).count()}")
        self.stdout.write(
            f"  activa=False: {instituciones.filter(activa=False).count()}"
        )

        # Consulta actual del dashboard: pendiente Y no activa
        pendientes_y_no_activas = instituciones.filter(
            estatus="pendiente", activa=False
        )
        self.stdout.write(f"\n--- Consulta actual del dashboard ---")
        self.stdout.write(
            f'  instituciones.filter(estatus="pendiente", activa=False): {pendientes_y_no_activas.count()}'
        )

        # alternative: solo por estatus="pendiente"
        solo_pendientes = instituciones.filter(estatus="pendiente")
        self.stdout.write(
            f'  instituciones.filter(estatus="pendiente"): {solo_pendientes.count()}'
        )

        # alternativa: por activa=False
        no_activas = instituciones.filter(activa=False)
        self.stdout.write(f"  instituciones.filter(activa=False): {no_activas.count()}")

        # Mostrar detalle de cada institución
        self.stdout.write("\n--- Detalle de instituciones ---")
        for inst in instituciones[:20]:
            self.stdout.write(f"\n  {inst.nombre}")
            self.stdout.write(f"    estatus: {inst.estatus}")
            self.stdout.write(f"    activa: {inst.activa}")
            self.stdout.write(f"    eliminado: {inst.eliminado}")
            self.stdout.write(f"    código: {inst.codigo}")

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("VERIFICACIÓN COMPLETADA")
        self.stdout.write("=" * 70)
