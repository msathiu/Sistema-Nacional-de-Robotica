# Generated migration for adding club events support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0020_add_salida_club_notification_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Agregar campo tipo_evento
        migrations.AddField(
            model_name='evento',
            name='tipo_evento',
            field=models.CharField(
                choices=[('institucional', 'Evento Institucional'), ('club', 'Evento de Club')],
                default='institucional',
                max_length=20,
                verbose_name='Tipo de Evento'
            ),
        ),
        
        # 2. Agregar relación con club
        migrations.AddField(
            model_name='evento',
            name='club_organizador',
            field=models.ForeignKey(
                blank=True,
                help_text='Para eventos de club',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='eventos',
                to='registry.club'
            ),
        ),
        
        # 3. Hacer institucion nullable (para eventos de club)
        migrations.AlterField(
            model_name='evento',
            name='institucion',
            field=models.ForeignKey(
                blank=True,
                help_text='Para eventos institucionales',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='registry.institucion'
            ),
        ),
        
        # 4. Agregar campos de aprobación
        migrations.AddField(
            model_name='evento',
            name='fecha_aprobacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evento',
            name='aprobado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='eventos_club_aprobados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='evento',
            name='observaciones_aprobacion',
            field=models.TextField(blank=True),
        ),
        
        # 5. Agregar campo creado_por
        migrations.AddField(
            model_name='evento',
            name='creado_por',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='eventos_creados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # 6. Actualizar estado_evento con nuevos estados
        migrations.AlterField(
            model_name='evento',
            name='estado_evento',
            field=models.CharField(
                choices=[
                    ('borrador', 'Borrador'),
                    ('pendiente', 'Pendiente Aprobación'),
                    ('aprobado', 'Aprobado'),
                    ('rechazado', 'Rechazado'),
                    ('abierto', 'Abierto'),
                    ('pausado', 'Pausado'),
                    ('cerrado', 'Cerrado'),
                    ('finalizado', 'Finalizado')
                ],
                db_index=True,
                default='abierto',
                max_length=20
            ),
        ),
        
        # 7. Agregar índices para performance
        migrations.AddIndex(
            model_name='evento',
            index=models.Index(fields=['tipo_evento', 'estado_evento'], name='idx_evt_tipo_estado'),
        ),
        migrations.AddIndex(
            model_name='evento',
            index=models.Index(fields=['club_organizador', 'estado_evento'], name='idx_evt_club_estado'),
        ),
        
        # 8. Agregar constraint para validar organizador
        migrations.AddConstraint(
            model_name='evento',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(tipo_evento='institucional', institucion__isnull=False, club_organizador__isnull=True) |
                    models.Q(tipo_evento='club', club_organizador__isnull=False, institucion__isnull=True)
                ),
                name='evento_organizador_valido'
            ),
        ),
    ]
