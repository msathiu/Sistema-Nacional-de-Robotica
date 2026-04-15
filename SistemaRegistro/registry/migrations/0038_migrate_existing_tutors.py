# Migration to transfer existing tutors to new structure

from django.db import migrations


def migrar_tutores_existentes(apps, schema_editor):
    """Migra tutores existentes a la nueva estructura M:N."""
    Tutor = apps.get_model("registry", "Tutor")
    TutorInstitucion = apps.get_model("registry", "TutorInstitucion")

    tutores_migrados = 0
    tutores_sin_institucion = 0

    for tutor in Tutor.objects.all():
        if tutor.institucion_id:
            # Crear vinculación con la institución actual
            TutorInstitucion.objects.create(
                tutor=tutor,
                institucion_id=tutor.institucion_id,
                status=tutor.status if hasattr(tutor, "status") else "activo",
                rol="colaborador",
            )
            tutores_migrados += 1
        else:
            tutores_sin_institucion += 1

    print(f"✅ Migrados: {tutores_migrados} tutores")
    if tutores_sin_institucion > 0:
        print(f"⚠️ Sin institución: {tutores_sin_institucion} tutores")


def revertir_migracion(apps, schema_editor):
    """Revierte la migración eliminando vinculaciones."""
    TutorInstitucion = apps.get_model("registry", "TutorInstitucion")
    TutorInstitucion.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0037_tutorinstitucion"),
    ]

    operations = [
        migrations.RunPython(migrar_tutores_existentes, revertir_migracion),
    ]
