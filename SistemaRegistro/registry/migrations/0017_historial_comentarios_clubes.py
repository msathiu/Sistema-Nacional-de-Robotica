from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('registry', '0016_sistema_eliminacion_notificaciones'),
    ]

    operations = [
        # Crear modelo HistorialClub para auditoría
        migrations.CreateModel(
            name='HistorialClub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_anterior', models.CharField(max_length=20)),
                ('estado_nuevo', models.CharField(max_length=20)),
                ('observaciones', models.TextField(blank=True)),
                ('fecha', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('club', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historial',
                    to='registry.club'
                )),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Historial de Club',
                'verbose_name_plural': 'Historiales de Clubes',
                'ordering': ['-fecha'],
            },
        ),
        
        # Crear modelo ComentarioClub para revisión
        migrations.CreateModel(
            name='ComentarioClub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comentario', models.TextField()),
                ('es_federacion', models.BooleanField(default=False)),
                ('fecha', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('club', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comentarios',
                    to='registry.club'
                )),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Comentario de Club',
                'verbose_name_plural': 'Comentarios de Clubes',
                'ordering': ['fecha'],
            },
        ),
        
        # Agregar índices
        migrations.AddIndex(
            model_name='historialclub',
            index=models.Index(fields=['club', '-fecha'], name='idx_hist_club_fecha'),
        ),
        migrations.AddIndex(
            model_name='comentarioclub',
            index=models.Index(fields=['club', 'fecha'], name='idx_com_club_fecha'),
        ),
    ]
