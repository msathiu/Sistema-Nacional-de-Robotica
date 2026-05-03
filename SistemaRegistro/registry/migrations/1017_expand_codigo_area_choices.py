from django.db import migrations, models

CODIGO_AREA_CHOICES = [
    ("0424", "0424"),
    ("0414", "0414"),
    ("0422", "0422"),
    ("0412", "0412"),
    ("0426", "0426"),
    ("0416", "0416"),
    ("0212", "0212"),
    ("0241", "0241"),
    ("0251", "0251"),
    ("0281", "0281"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "1016_institucion_unique_codigo_mppe_educativas_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evento",
            name="telefono_codigo",
            field=models.CharField(
                blank=True,
                choices=CODIGO_AREA_CHOICES,
                help_text="Código de área teléfono de contacto",
                max_length=4,
                verbose_name="Código de Área",
            ),
        ),
        migrations.AlterField(
            model_name="participante",
            name="codigo_area",
            field=models.CharField(
                choices=CODIGO_AREA_CHOICES,
                default="0424",
                max_length=4,
                verbose_name="Código de Área",
            ),
        ),
        migrations.AlterField(
            model_name="participante",
            name="codigo_area_representante",
            field=models.CharField(
                blank=True,
                choices=CODIGO_AREA_CHOICES,
                max_length=4,
                verbose_name="Cód. área Rep.",
            ),
        ),
        migrations.AlterField(
            model_name="tutor",
            name="telefono_codigo",
            field=models.CharField(
                blank=True,
                choices=CODIGO_AREA_CHOICES,
                help_text="Código de área del teléfono de contacto",
                max_length=4,
                verbose_name="Código de Área",
            ),
        ),
    ]
