# Generated manually for unique constraints on Participante model

from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '1000_merge_20260308_1825'),
    ]

    operations = [
        # Agregar unique=True a cedula
        migrations.AlterField(
            model_name='participante',
            name='cedula',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Solo números (ej: 19122516)',
                max_length=20,
                null=True,
                unique=True,
                validators=[
                    RegexValidator(
                        regex='^[0-9]+$',
                        message='Cédula debe contener solo números'
                    )
                ],
            ),
        ),
        # Agregar unique=True a cedula_escolar
        migrations.AlterField(
            model_name='participante',
            name='cedula_escolar',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Cédula escolar del participante (solo números)',
                max_length=20,
                null=True,
                unique=True,
                validators=[
                    RegexValidator(
                        regex='^[0-9]*$',
                        message='La cédula escolar debe contener solo números'
                    )
                ],
                verbose_name='Cédula Escolar'
            ),
        ),
        # Agregar índice compuesto para nombres+apellidos+fecha_nacimiento
        migrations.AddIndex(
            model_name='participante',
            index=models.Index(
                fields=['nombres', 'apellidos', 'fecha_nacimiento'],
                name='idx_part_nombre_fn'
            ),
        ),
        # Agregar constraint de unicidad para nombres+apellidos+fecha_nacimiento
        migrations.AddConstraint(
            model_name='participante',
            constraint=models.UniqueConstraint(
                fields=['nombres', 'apellidos', 'fecha_nacimiento'],
                name='unique_participante_datos_personales',
                violation_error_message='Ya existe un participante con estos nombres, apellidos y fecha de nacimiento.'
            ),
        ),
    ]
