# Script para crear líneas de investigación de ejemplo
# Ejecutar desde Django shell: python manage.py shell < crear_lineas.py

from registry.models import LineaInvestigacion

lineas = [
    ("Robótica Educativa", "Desarrollo de proyectos de robótica para educación", 1),
    ("Inteligencia Artificial", "Aplicaciones de IA y Machine Learning", 2),
    ("Programación y Software", "Desarrollo de software y aplicaciones", 3),
    ("Electrónica y Hardware", "Diseño y construcción de circuitos electrónicos", 4),
    ("Mecatrónica", "Integración de mecánica, electrónica y control", 5),
    ("Internet de las Cosas (IoT)", "Dispositivos conectados y automatización", 6),
    ("Visión por Computadora", "Procesamiento de imágenes y reconocimiento", 7),
    ("Robótica Móvil", "Robots autónomos y navegación", 8),
]

for nombre, descripcion, orden in lineas:
    linea, created = LineaInvestigacion.objects.get_or_create(
        nombre=nombre,
        defaults={"descripcion": descripcion, "orden": orden, "activa": True},
    )
    if created:
        print(f"✅ Creada: {nombre}")
    else:
        print(f"ℹ️  Ya existe: {nombre}")

print(
    f"\n📊 Total de líneas activas: {LineaInvestigacion.objects.filter(activa=True).count()}"
)
