from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('registry', '0015_club_mejorado'),
    ]

    operations = [
        # Agregar campos al modelo Club para eliminación
        migrations.AddField(
            model_name='club',
            name='eliminado',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='club',
            name='fecha_eliminacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='club',
            name='motivo_eliminacion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='club',
            name='eliminado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='clubes_eliminados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Crear modelo SolicitudEliminacionClub
        migrations.CreateModel(
            name='SolicitudEliminacionClub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.TextField(verbose_name='Motivo de la solicitud')),
                ('estado', models.CharField(
                    choices=[
                        ('pendiente', 'Pendiente'),
                        ('aprobada', 'Aprobada'),
                        ('rechazada', 'Rechazada')
                    ],
                    default='pendiente',
                    max_length=20,
                    db_index=True
                )),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('fecha_respuesta', models.DateTimeField(blank=True, null=True)),
                ('observaciones_federacion', models.TextField(blank=True)),
                ('club', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='solicitudes_eliminacion',
                    to='registry.club'
                )),
                ('institucion_solicitante', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='registry.institucion'
                )),
                ('revisado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='solicitudes_eliminacion_revisadas',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Solicitud de Eliminación de Club',
                'verbose_name_plural': 'Solicitudes de Eliminación de Clubes',
                'ordering': ['-fecha_solicitud'],
            },
        ),
        
        # Crear modelo Notificacion (Buzón de mensajes)
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[
                        ('club_aprobado', 'Club Aprobado'),
                        ('club_rechazado', 'Club Rechazado'),
                        ('solicitud_eliminacion', 'Solicitud de Eliminación'),
                        ('eliminacion_aprobada', 'Eliminación Aprobada'),
                        ('eliminacion_rechazada', 'Eliminación Rechazada'),
                        ('membresia_aprobada', 'Membresía Aprobada'),
                        ('membresia_rechazada', 'Membresía Rechazada'),
                        ('sistema', 'Notificación del Sistema'),
                    ],
                    max_length=30,
                    db_index=True
                )),
                ('titulo', models.CharField(max_length=200)),
                ('mensaje', models.TextField()),
                ('leida', models.BooleanField(default=False, db_index=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('destinatario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notificaciones',
                    to=settings.AUTH_USER_MODEL
                )),
                ('club', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='registry.club'
                )),
            ],
            options={
                'verbose_name': 'Notificación',
                'verbose_name_plural': 'Notificaciones',
                'ordering': ['-fecha_creacion'],
            },
        ),
        
        # Agregar índices
        migrations.AddIndex(
            model_name='solicitudeliminacionclub',
            index=models.Index(fields=['estado', 'fecha_solicitud'], name='idx_sol_elim_estado'),
        ),
        migrations.AddIndex(
            model_name='notificacion',
            index=models.Index(fields=['destinatario', 'leida'], name='idx_notif_dest_leida'),
        ),
    ]
