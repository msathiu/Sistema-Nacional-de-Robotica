# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0030_participante_nacionalidad_alter_participante_cedula_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='participante',
            name='nacionalidad_representante',
            field=models.CharField(
                choices=[('V', 'Venezolano'), ('E', 'Extranjero')],
                default='V',
                max_length=1,
                verbose_name='Nacionalidad Representante'
            ),
        ),
    ]
