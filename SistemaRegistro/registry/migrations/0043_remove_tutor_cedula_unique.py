# Generated manually to remove unique constraint from Tutor.cedula

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0042_merge_20260308_1545"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tutor",
            name="cedula",
            field=models.CharField(
                db_index=True,
                help_text="Ingrese solo números, sin letras (V/E)",
                max_length=12,
                validators=[
                    django.core.validators.RegexValidator(
                        message="La cédula debe contener solo números (sin letras V/E)",
                        regex="^[0-9]+$",
                    )
                ],
                verbose_name="Cédula",
            ),
        ),
    ]
