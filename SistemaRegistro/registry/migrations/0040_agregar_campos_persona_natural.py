# Generated manually for persona natural fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0039_merge_20260307_0114'),
    ]

    operations = [
        migrations.AddField(
            model_name='institucion',
            name='particular_nombres',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Nombres'),
        ),
        migrations.AddField(
            model_name='institucion',
            name='particular_apellidos',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Apellidos'),
        ),
        migrations.AddField(
            model_name='institucion',
            name='particular_nacionalidad',
            field=models.CharField(blank=True, choices=[('V', 'V'), ('E', 'E')], max_length=1, null=True, verbose_name='Nacionalidad'),
        ),
        migrations.AddField(
            model_name='institucion',
            name='particular_cedula',
            field=models.CharField(blank=True, db_index=True, max_length=10, null=True, verbose_name='Cédula (solo números)'),
        ),
        migrations.AddIndex(
            model_name='institucion',
            index=models.Index(fields=['particular_cedula'], name='idx_inst_part_cedula'),
        ),
    ]
