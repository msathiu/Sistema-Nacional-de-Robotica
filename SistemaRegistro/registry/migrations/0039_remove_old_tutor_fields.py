# Migration to remove old fields from Tutor model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0038_migrate_existing_tutors'),
    ]

    operations = [
        # Eliminar campo status (ahora en TutorInstitucion)
        migrations.RemoveField(
            model_name='tutor',
            name='status',
        ),
        # Eliminar FK institucion (ahora M:N via TutorInstitucion)
        migrations.RemoveField(
            model_name='tutor',
            name='institucion',
        ),
        # Eliminar índice antiguo
        migrations.RemoveIndex(
            model_name='tutor',
            name='idx_tutor_status_inst',
        ),
    ]
