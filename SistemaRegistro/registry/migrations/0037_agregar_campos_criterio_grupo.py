# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0036_tutor_nacionalidad_tutor_telefono_codigo_and_more'),
    ]

    operations = [
        # Agregar campo institucion a Grupo
        migrations.AddField(
            model_name='grupo',
            name='institucion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='grupos_institucion',
                to='registry.institucion',
                verbose_name='Institución'
            ),
        ),
        # Agregar campos específicos por criterio
        migrations.AddField(
            model_name='grupo',
            name='edad_desde',
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Edad mínima (solo para criterio 'Por Edad')",
                null=True,
                verbose_name='Edad Desde'
            ),
        ),
        migrations.AddField(
            model_name='grupo',
            name='edad_hasta',
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Edad máxima (solo para criterio 'Por Edad')",
                null=True,
                verbose_name='Edad Hasta'
            ),
        ),
        migrations.AddField(
            model_name='grupo',
            name='nivel_educativo',
            field=models.CharField(
                blank=True,
                choices=[
                    ('NO', 'No estudia'),
                    ('P1', 'Preescolar Nivel 1'),
                    ('P2', 'Preescolar Nivel 2'),
                    ('PR1', '1er Grado Primaria'),
                    ('PR2', '2do Grado Primaria'),
                    ('PR3', '3er Grado Primaria'),
                    ('PR4', '4to Grado Primaria'),
                    ('PR5', '5to Grado Primaria'),
                    ('PR6', '6to Grado Primaria'),
                    ('L1', '1er Año Liceo'),
                    ('L2', '2do Año Liceo'),
                    ('L3', '3er Año Liceo'),
                    ('L4', '4to Año Liceo'),
                    ('L5', '5to Año Liceo'),
                    ('L6', '6to Año Liceo'),
                    ('U', 'Estudios Universitarios'),
                    ('OTRO', 'Otro/No especificado')
                ],
                help_text="Grado escolar (solo para criterio 'Por Nivel Educativo')",
                max_length=4,
                null=True,
                verbose_name='Nivel Educativo'
            ),
        ),
        migrations.AddField(
            model_name='grupo',
            name='nombre_proyecto',
            field=models.CharField(
                blank=True,
                help_text="Nombre del proyecto (solo para criterio 'Por Proyecto')",
                max_length=200,
                verbose_name='Nombre del Proyecto'
            ),
        ),
        # Modificar campo criterio para remover default
        migrations.AlterField(
            model_name='grupo',
            name='criterio',
            field=models.CharField(
                choices=[
                    ('edad', 'Por Edad'),
                    ('nivel', 'Por Nivel Educativo'),
                    ('proyecto', 'Por Proyecto')
                ],
                max_length=20
            ),
        ),
        # Modificar campo tutores para hacerlo no blank
        migrations.AlterField(
            model_name='grupo',
            name='tutores',
            field=models.ManyToManyField(
                related_name='grupos',
                to='registry.tutor',
                verbose_name='Tutores asignados'
            ),
        ),
        # Agregar índices
        migrations.AddIndex(
            model_name='grupo',
            index=models.Index(fields=['criterio'], name='idx_grupo_criterio'),
        ),
        migrations.AddIndex(
            model_name='grupo',
            index=models.Index(fields=['institucion'], name='idx_grupo_institucion'),
        ),
    ]
