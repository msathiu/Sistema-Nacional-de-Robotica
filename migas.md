### FASE 1
Agrega un bloque llamado {% block breadcrumbs %} en mi base.html justo debajo de la barra de navegación. Usa clases de Bootstrap 5
Actúa como un desarrollador Senior de Django. Quiero implementar un sistema de Breadcrumbs automático basado en la URL.
Sigue estos pasos:
Crea un Context Processor en un nuevo archivo context_processors.py que convierta request.path en una lista de migas de pan.
Regístralo en settings.py dentro de la sección TEMPLATES > OPTIONS > context_processors.
Modifica mi base.html para incluir un snippet que recorra esa lista automáticamente usando estilos de Bootstrap (o el framework que uses).
Asegúrate de que el primer elemento sea siempre un icono de 'Home' o la palabra 'Inicio' apuntando a /.
Regla importante: Los nombres deben capitalizarse y reemplazar guiones por espacios (ej: 'club-guarico' -> 'Club Guarico')."