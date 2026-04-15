# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0001_initial"),  # Ajustar al número de la última migración
    ]

    operations = [
        migrations.AddField(
            model_name="tutor",
            name="sexo",
            field=models.CharField(
                choices=[("M", "Masculino"), ("F", "Femenino"), ("O", "Otro")],
                default="M",
                max_length=1,
                verbose_name="Sexo",
            ),
        ),
    ]
