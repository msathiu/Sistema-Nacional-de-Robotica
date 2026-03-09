from django.core.management.base import BaseCommand
from registry.models import Institucion, Estado, Municipio

class Command(BaseCommand):
    help = 'Carga instituciones de ejemplo para el sistema de robótica'

    def handle(self, *args, **kwargs):
        # Obtener estados y municipios
        try:
            dc = Estado.objects.get(nombre='Distrito Capital')
            miranda = Estado.objects.get(nombre='Miranda')
            carabobo = Estado.objects.get(nombre='Carabobo')
            zulia = Estado.objects.get(nombre='Zulia')
            
            libertador = Municipio.objects.get(estado=dc, nombre='Libertador')
            chacao = Municipio.objects.get(estado=miranda, nombre='Chacao')
            baruta = Municipio.objects.get(estado=miranda, nombre='Baruta')
            valencia = Municipio.objects.get(estado=carabobo, nombre='Valencia')
            maracaibo = Municipio.objects.get(estado=zulia, nombre='Maracaibo')
        except (Estado.DoesNotExist, Municipio.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            self.stdout.write(self.style.WARNING('Ejecuta primero: python manage.py load_venezuela_data'))
            return

        instituciones = [
            # Instituciones Educativas
            {'nombre': 'Universidad Central de Venezuela', 'tipo': 'EDUCATIVA', 'estado': dc, 'municipio': libertador},
            {'nombre': 'Universidad Simón Bolívar', 'tipo': 'EDUCATIVA', 'estado': dc, 'municipio': libertador},
            {'nombre': 'Universidad Metropolitana', 'tipo': 'EDUCATIVA', 'estado': miranda, 'municipio': baruta},
            {'nombre': 'Universidad de Carabobo', 'tipo': 'EDUCATIVA', 'estado': carabobo, 'municipio': valencia},
            {'nombre': 'Universidad del Zulia', 'tipo': 'EDUCATIVA', 'estado': zulia, 'municipio': maracaibo},
            {'nombre': 'Colegio San Ignacio de Loyola', 'tipo': 'EDUCATIVA', 'estado': dc, 'municipio': libertador},
            {'nombre': 'Liceo Andrés Bello', 'tipo': 'EDUCATIVA', 'estado': miranda, 'municipio': baruta},
            
            # Grupos de Robótica
            {'nombre': 'Club de Robótica UCV', 'tipo': 'GRUPO', 'estado': dc, 'municipio': libertador},
            {'nombre': 'Robótica Educativa USB', 'tipo': 'GRUPO', 'estado': dc, 'municipio': libertador},
            {'nombre': 'Grupo Robótica Juvenil Caracas', 'tipo': 'GRUPO', 'estado': dc, 'municipio': libertador},
            {'nombre': 'TecnoKids Venezuela', 'tipo': 'GRUPO', 'estado': miranda, 'municipio': chacao},
            {'nombre': 'Robotica Miranda', 'tipo': 'GRUPO', 'estado': miranda, 'municipio': baruta},
            {'nombre': 'Club de Robótica Valencia', 'tipo': 'GRUPO', 'estado': carabobo, 'municipio': valencia},
            {'nombre': 'Zulia Bots', 'tipo': 'GRUPO', 'estado': zulia, 'municipio': maracaibo},
            {'nombre': 'Programadores del Futuro', 'tipo': 'GRUPO', 'estado': dc, 'municipio': libertador},
            
            # Registro Individual
            {'nombre': 'Registro Individual - Estudiante', 'tipo': 'INDIVIDUAL', 'estado': dc, 'municipio': libertador},
            {'nombre': 'Registro Individual - Profesional', 'tipo': 'INDIVIDUAL', 'estado': miranda, 'municipio': chacao},
        ]

        count = 0
        for inst_data in instituciones:
            institucion, created = Institucion.objects.get_or_create(
                nombre=inst_data['nombre'],
                tipo=inst_data['tipo'],
                estado=inst_data['estado'],
                municipio=inst_data['municipio'],
                defaults={
                    'direccion': f'Dirección de {inst_data["nombre"]}',
                    'telefono': '+58 412-0000000'
                }
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ {inst_data["tipo"]}: {inst_data["nombre"]}'))

        self.stdout.write(self.style.SUCCESS(f'\n🎉 Se crearon {count} instituciones de ejemplo'))