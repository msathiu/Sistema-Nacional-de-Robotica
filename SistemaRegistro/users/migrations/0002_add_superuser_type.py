# Generated migration for adding superuser type

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="user_type",
            field=models.CharField(
                choices=[
                    ("participante", "Participante"),
                    ("institucional", "Usuario Institucional"),
                    ("admin", "Administrador (Ministerio)"),
                    ("superuser", "Superusuario"),
                ],
                default="participante",
                max_length=20,
            ),
        ),
    ]
