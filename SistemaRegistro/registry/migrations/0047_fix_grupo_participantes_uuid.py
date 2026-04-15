# Generated manually

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0046_remove_participante_deprecated_fields"),
    ]

    operations = [
        # Eliminar la relación ManyToMany antigua
        migrations.RemoveField(
            model_name="grupo",
            name="participantes",
        ),
        # Recrear la relación ManyToMany con UUID
        migrations.AddField(
            model_name="grupo",
            name="participantes",
            field=models.ManyToManyField(
                related_name="grupos",
                to="registry.participante",
                verbose_name="Integrantes del Grupo",
            ),
        ),
    ]
