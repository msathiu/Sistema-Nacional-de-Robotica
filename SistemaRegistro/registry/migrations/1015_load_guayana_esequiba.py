from django.db import migrations
from django.db import connection


def cargar_guayana_esequiba(apps, schema_editor):
    Estado = apps.get_model("registry", "Estado")
    Municipio = apps.get_model("registry", "Municipio")
    Parroquia = apps.get_model("registry", "Parroquia")

    estado, _ = Estado.objects.update_or_create(
        id=26,
        defaults={"nombre": "Guayana Esequiba", "codigo": "VE-EQ"},
    )

    # Municipios históricos reclamados por Venezuela
    municipios_data = [
        (463, "Barima-Waini"),
        (464, "Cuyuní-Mazaruní"),
        (465, "Demerara-Mahaica"),
        (466, "East Berbice-Corentyne"),
        (467, "Essequibo Islands-West Demerara"),
        (468, "Mahaica-Berbice"),
        (469, "Pomeroon-Supenaam"),
        (470, "Potaro-Siparuni"),
        (471, "Upper Demerara-Berbice"),
        (472, "Upper Takutu-Upper Essequibo"),
    ]

    municipio_objs = {}
    for mun_id, nombre in municipios_data:
        obj, _ = Municipio.objects.update_or_create(
            id=mun_id,
            defaults={"nombre": nombre, "estado": estado},
        )
        municipio_objs[mun_id] = obj

    # Una parroquia representativa por municipio
    parroquias_data = [
        (1139, 463, "Mabaruma"),
        (1140, 464, "Bartica"),
        (1141, 465, "Georgetown"),
        (1142, 466, "New Amsterdam"),
        (1143, 467, "Vreed-en-Hoop"),
        (1144, 468, "Mahaicony"),
        (1145, 469, "Anna Regina"),
        (1146, 470, "Mahdia"),
        (1147, 471, "Linden"),
        (1148, 472, "Lethem"),
    ]

    for par_id, mun_id, nombre in parroquias_data:
        Parroquia.objects.update_or_create(
            id=par_id,
            defaults={"nombre": nombre, "municipio": municipio_objs[mun_id]},
        )

    # Resetear secuencias para PostgreSQL
    for modelo, campo in [
        (Estado, "registry_estado"),
        (Municipio, "registry_municipio"),
        (Parroquia, "registry_parroquia"),
    ]:
        tabla = modelo._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                f"coalesce(max(id), 1)) FROM {tabla};"
            )


def revertir_guayana_esequiba(apps, schema_editor):
    Estado = apps.get_model("registry", "Estado")
    Municipio = apps.get_model("registry", "Municipio")
    Parroquia = apps.get_model("registry", "Parroquia")

    Parroquia.objects.filter(id__in=range(1139, 1149)).delete()
    Municipio.objects.filter(id__in=range(463, 473)).delete()
    Estado.objects.filter(id=26).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "1014_alter_asistenciaevento_participante"),
    ]

    operations = [
        migrations.RunPython(cargar_guayana_esequiba, revertir_guayana_esequiba),
    ]
