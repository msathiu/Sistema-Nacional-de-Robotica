# Generated manually to migrate existing participant data

from django.db import migrations


def migrate_existing_participants(apps, schema_editor):
    """
    Migra participantes existentes a la arquitectura multi-institución.

    Para cada participante con institución asignada:
    1. Crea vinculación ParticipanteInstitucion
    2. Crea historial ParticipanteGrupo si tiene grupo
    """
    Participante = apps.get_model("registry", "Participante")
    ParticipanteInstitucion = apps.get_model("registry", "ParticipanteInstitucion")
    ParticipanteGrupo = apps.get_model("registry", "ParticipanteGrupo")

    participantes_migrados = 0
    grupos_migrados = 0

    for participante in Participante.objects.all():
        if participante.institucion:
            # Crear vinculación
            vinculacion, created = ParticipanteInstitucion.objects.get_or_create(
                participante=participante,
                institucion=participante.institucion,
                defaults={
                    "grupo_actual": participante.grupo,
                    "status": participante.status if participante.status else "activo",
                    "registrado_por": None,  # Migración automática
                },
            )

            if created:
                participantes_migrados += 1

            # Crear historial de grupo si existe
            if participante.grupo:
                historial, created = ParticipanteGrupo.objects.get_or_create(
                    participante=participante,
                    grupo=participante.grupo,
                    defaults={"activo": True},
                )

                if created:
                    grupos_migrados += 1

    print(f"✅ Migración completada:")
    print(f"   - {participantes_migrados} vinculaciones creadas")
    print(f"   - {grupos_migrados} historiales de grupo creados")


def reverse_migration(apps, schema_editor):
    """Elimina las vinculaciones creadas durante la migración."""
    ParticipanteInstitucion = apps.get_model("registry", "ParticipanteInstitucion")
    ParticipanteGrupo = apps.get_model("registry", "ParticipanteGrupo")

    ParticipanteInstitucion.objects.all().delete()
    ParticipanteGrupo.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0044_participante_multi_institucion"),
    ]

    operations = [
        migrations.RunPython(migrate_existing_participants, reverse_migration),
    ]
