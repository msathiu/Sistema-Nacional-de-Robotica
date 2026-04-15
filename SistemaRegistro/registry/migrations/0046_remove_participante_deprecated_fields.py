# Generated manually

import uuid
from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0045_migrate_participant_data"),
    ]

    operations = [
        # Eliminar índices que referencian campos a eliminar
        migrations.RemoveIndex(
            model_name="participante",
            name="idx_part_inst",
        ),
        migrations.RemoveIndex(
            model_name="participante",
            name="idx_part_ubicacion",
        ),
        migrations.RemoveIndex(
            model_name="participante",
            name="idx_part_status",
        ),
        migrations.RemoveIndex(
            model_name="participante",
            name="idx_part_grupo",
        ),
        # Eliminar campos deprecados
        migrations.RemoveField(
            model_name="participante",
            name="institucion",
        ),
        migrations.RemoveField(
            model_name="participante",
            name="grupo",
        ),
        migrations.RemoveField(
            model_name="participante",
            name="registrado_por_federacion",
        ),
        migrations.RemoveField(
            model_name="participante",
            name="status",
        ),
        # Eliminar constraint UNIQUE de cedula
        migrations.AlterField(
            model_name="participante",
            name="cedula",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Solo números (ej: 19122516)",
                max_length=20,
                null=True,
                validators=[
                    RegexValidator(
                        regex="^[0-9]+$", message="Cédula debe contener solo números"
                    )
                ],
            ),
        ),
        # Cambiar PK a UUID
        migrations.RemoveField(
            model_name="participante",
            name="id",
        ),
        migrations.AddField(
            model_name="participante",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
            preserve_default=False,
        ),
    ]
