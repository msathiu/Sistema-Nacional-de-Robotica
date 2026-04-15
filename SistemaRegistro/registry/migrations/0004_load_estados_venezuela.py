from django.db import migrations
from django.db import connection


def cargar_estados_venezuela(apps, schema_editor):
    # Obtenemos solo el modelo Estado
    Estado = apps.get_model("registry", "Estado")

    estados = [
        (1, "Amazonas", "VE-X"),
        (2, "Anzoátegui", "VE-B"),
        (3, "Apure", "VE-C"),
        (4, "Aragua", "VE-D"),
        (5, "Barinas", "VE-E"),
        (6, "Bolívar", "VE-F"),
        (7, "Carabobo", "VE-G"),
        (8, "Cojedes", "VE-H"),
        (9, "Delta Amacuro", "VE-Y"),
        (10, "Falcón", "VE-I"),
        (11, "Guárico", "VE-J"),
        (12, "Lara", "VE-K"),
        (13, "Mérida", "VE-L"),
        (14, "Miranda", "VE-M"),
        (15, "Monagas", "VE-N"),
        (16, "Nueva Esparta", "VE-O"),
        (17, "Portuguesa", "VE-P"),
        (18, "Sucre", "VE-R"),
        (19, "Táchira", "VE-S"),
        (20, "Trujillo", "VE-T"),
        (21, "La Guaira", "VE-W"),
        (22, "Yaracuy", "VE-U"),
        (23, "Zulia", "VE-V"),
        (24, "Distrito Capital", "VE-A"),
        (25, "Dependencias Federales", "VE-Z"),
    ]

    for estado_id, nombre, codigo in estados:
        # Se eliminó la referencia a 'pais' en los defaults
        Estado.objects.update_or_create(
            id=estado_id,
            defaults={
                "nombre": nombre,
                "codigo": codigo,
            },
        )
    # Esto sincroniza el contador de IDs de Postgres con los datos insertados
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT setval(pg_get_serial_sequence('registry_estado', 'id'),
            coalesce(max(id), 1)) FROM registry_estado;
        """
        )


class Migration(migrations.Migration):
    # Asegúrate de que esta dependencia sea la migración donde
    # se creó la tabla Estado sin el campo ForeignKey de Pais
    dependencies = [
        ("registry", "0003_institucion_dependencia"),
    ]

    operations = [
        migrations.RunPython(cargar_estados_venezuela),
    ]
