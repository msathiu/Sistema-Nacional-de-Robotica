# Generated migration for Fase 4

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('registry', '0017_historial_comentarios_clubes'),
    ]

    operations = [
        # Modelo CalificacionClub
        migrations.CreateModel(
            name='CalificacionClub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntuacion', models.IntegerField(choices=[(1, '1 - Muy Malo'), (2, '2 - Malo'), (3, '3 - Regular'), (4, '4 - Bueno'), (5, '5 - Excelente')], verbose_name='Puntuación')),
                ('resena', models.TextField(blank=True, verbose_name='Reseña')),
                ('fecha', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calificaciones', to='registry.club')),
                ('institucion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registry.institucion')),
            ],
            options={
                'verbose_name': 'Calificación de Club',
                'verbose_name_plural': 'Calificaciones de Clubes',
                'ordering': ['-fecha'],
                'unique_together': {('club', 'institucion')},
            },
        ),
        
        # Modelo ClubEvento
        migrations.CreateModel(
            name='ClubEvento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(choices=[('organizador', 'Organizador'), ('colaborador', 'Colaborador'), ('participante', 'Participante')], default='participante', max_length=20, verbose_name='Rol del Club')),
                ('fecha_vinculacion', models.DateTimeField(auto_now_add=True)),
                ('activo', models.BooleanField(db_index=True, default=True)),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eventos_vinculados', to='registry.club')),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clubes_vinculados', to='registry.evento')),
            ],
            options={
                'verbose_name': 'Club-Evento',
                'verbose_name_plural': 'Clubes-Eventos',
                'ordering': ['-fecha_vinculacion'],
                'unique_together': {('club', 'evento')},
            },
        ),
        
        # Índices
        migrations.AddIndex(
            model_name='calificacionclub',
            index=models.Index(fields=['club', '-fecha'], name='idx_calif_club_fecha'),
        ),
        migrations.AddIndex(
            model_name='clubevento',
            index=models.Index(fields=['evento', 'activo'], name='idx_clubevt_evt_act'),
        ),
    ]
