"""
Comando de gestión para crear líneas de investigación iniciales.
Uso: python manage.py crear_lineas_investigacion
"""
from django.core.management.base import BaseCommand
from registry.models import LineaInvestigacion


class Command(BaseCommand):
    help = "Crea las líneas de investigación iniciales del sistema"

    def handle(self, *args, **options):
        lineas_data = [
            {
                "codigo": "electronica",
                "nombre": "Electrónica y Circuitos",
                "descripcion": "Diseño y construcción de circuitos electrónicos, placas PCB, sensores y sistemas embebidos.",
                "orden": 1,
            },
            {
                "codigo": "programacion",
                "nombre": "Programación y Algoritmos",
                "descripcion": "Desarrollo de software, algoritmos, estructuras de datos y lenguajes de programación.",
                "orden": 2,
            },
            {
                "codigo": "mecanica",
                "nombre": "Mecánica y Estructuras",
                "descripcion": "Diseño mecánico, estructuras, mecanismos, impresión 3D y fabricación digital.",
                "orden": 3,
            },
            {
                "codigo": "ia",
                "nombre": "Inteligencia Artificial",
                "descripcion": "Machine learning, deep learning, visión por computadora y sistemas inteligentes.",
                "orden": 4,
            },
            {
                "codigo": "iot",
                "nombre": "Internet de las Cosas (IoT)",
                "descripcion": "Conectividad de dispositivos, domótica, redes de sensores y comunicación M2M.",
                "orden": 5,
            },
            {
                "codigo": "automatizacion",
                "nombre": "Automatización Industrial",
                "descripcion": "Sistemas de control automático, PLCs, robótica industrial y procesos automatizados.",
                "orden": 6,
            },
            {
                "codigo": "diseno_3d",
                "nombre": "Diseño e Impresión 3D",
                "descripcion": "Modelado 3D, diseño CAD, manufactura aditiva y prototipado rápido.",
                "orden": 7,
            },
            {
                "codigo": "telecom",
                "nombre": "Telecomunicaciones",
                "descripcion": "Sistemas de comunicación, redes, transmisión de datos y tecnologías wireless.",
                "orden": 8,
            },
            {
                "codigo": "robotica",
                "nombre": "Robótica General",
                "descripcion": "Diseño y construcción de robots, brazos robóticos, drones y sistemas mecatrónicos.",
                "orden": 9,
            },
            {
                "codigo": "energia",
                "nombre": "Energías Renovables",
                "descripcion": "Sistemas de energía solar, eólica,hidrógeno y soluciones sostenibles.",
                "orden": 10,
            },
        ]

        creadas = 0
        actualizadas = 0

        for data in lineas_data:
            linea, created = LineaInvestigacion.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "nombre": data["nombre"],
                    "descripcion": data["descripcion"],
                    "activa": True,
                    "orden": data["orden"],
                },
            )

            if created:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Creada: {linea.nombre}"))
            else:
                actualizadas += 1
                self.stdout.write(self.style.WARNING(f"↻ Actualizada: {linea.nombre}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Comando completado: {creadas} creadas, {actualizadas} actualizadas"
            )
        )

        # Mostrar resumen
        total = LineaInvestigacion.objects.count()
        activas = LineaInvestigacion.objects.filter(activa=True).count()
        self.stdout.write(f"Total de líneas: {total} ({activas} activas)")
