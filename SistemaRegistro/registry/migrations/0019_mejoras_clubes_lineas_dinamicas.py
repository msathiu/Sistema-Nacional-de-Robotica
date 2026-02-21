# Generated manually for mejoras críticas de clubes

from django.db import migrations, models
import django.db.models.deletion


def migrar_lineas_existentes(apps, schema_editor):
    """Migrar líneas hardcodeadas a modelo dinámico."""
    LineaInvestigacion = apps.get_model('registry', 'LineaInvestigacion')
    Club = apps.get_model('registry', 'Club')
    ClubLineaInvestigacion = apps.get_model('registry', 'ClubLineaInvestigacion')
    
    # Crear líneas desde LINEAS_INVESTIGACION_CHOICES
    lineas_map = {
        'electronica': 'Electrónica y Circuitos',
        'programacion': 'Programación y Algoritmos',
        'mecanica': 'Mecánica y Estructuras',
        'ia': 'Inteligencia Artificial',
        'iot': 'Internet de las Cosas (IoT)',
        'automatizacion': 'Automatización Industrial',
        'diseno_3d': 'Diseño e Impresión 3D',
        'telecom': 'Telecomunicaciones',
    }
    
    lineas_creadas = {}
    for orden, (codigo, nombre) in enumerate(lineas_map.items(), start=1):
        linea, created = LineaInvestigacion.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'activa': True,
                'orden': orden
            }
        )
        lineas_creadas[codigo] = linea
    
    # Migrar clubes existentes
    for club in Club.objects.all():
        orden = 1
        if club.linea_1 and club.linea_1 in lineas_creadas:
            ClubLineaInvestigacion.objects.get_or_create(
                club=club,
                linea=lineas_creadas[club.linea_1],
                defaults={
                    'tipo_linea': 'principal',
                    'orden': orden
                }
            )
            orden += 1
        
        if club.linea_2 and club.linea_2 in lineas_creadas:
            ClubLineaInvestigacion.objects.get_or_create(
                club=club,
                linea=lineas_creadas[club.linea_2],
                defaults={
                    'tipo_linea': 'soporte',
                    'orden': orden
                }
            )
            orden += 1
        
        if club.linea_3 and club.linea_3 in lineas_creadas:
            ClubLineaInvestigacion.objects.get_or_create(
                club=club,
                linea=lineas_creadas[club.linea_3],
                defaults={
                    'tipo_linea': 'afines',
                    'orden': orden
                }
            )


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0018_fase4_calificaciones_eventos_restauracion'),
    ]

    operations = [
        # 1. Crear modelo LineaInvestigacion
        migrations.CreateModel(
            name='LineaInvestigacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(db_index=True, max_length=50, unique=True, verbose_name='Código')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('activa', models.BooleanField(db_index=True, default=True, verbose_name='Activa')),
                ('orden', models.IntegerField(default=0, verbose_name='Orden de visualización')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Línea de Investigación',
                'verbose_name_plural': 'Líneas de Investigación',
                'ordering': ['orden', 'nombre'],
            },
        ),
        
        # 2. Agregar índice a LineaInvestigacion
        migrations.AddIndex(
            model_name='lineainvestigacion',
            index=models.Index(fields=['activa', 'orden'], name='idx_linea_activa_orden'),
        ),
        
        # 3. Crear modelo ClubLineaInvestigacion
        migrations.CreateModel(
            name='ClubLineaInvestigacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_linea', models.CharField(choices=[('principal', 'Principal'), ('soporte', 'Soporte'), ('afines', 'Afines')], default='principal', max_length=20, verbose_name='Tipo de Línea')),
                ('orden', models.IntegerField(default=0, verbose_name='Orden')),
                ('fecha_vinculacion', models.DateTimeField(auto_now_add=True)),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='club_lineas', to='registry.club')),
                ('linea', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='clubes', to='registry.lineainvestigacion')),
            ],
            options={
                'verbose_name': 'Club-Línea de Investigación',
                'verbose_name_plural': 'Clubes-Líneas de Investigación',
                'ordering': ['orden'],
            },
        ),
        
        # 4. Agregar unique_together a ClubLineaInvestigacion
        migrations.AlterUniqueTogether(
            name='clublineainvestigacion',
            unique_together={('club', 'linea')},
        ),
        
        # 5. Agregar índice a ClubLineaInvestigacion
        migrations.AddIndex(
            model_name='clublineainvestigacion',
            index=models.Index(fields=['club', 'orden'], name='idx_clublinea_club_orden'),
        ),
        
        # 6. Modificar campos de Club (hacerlos opcionales)
        migrations.AlterField(
            model_name='club',
            name='linea_1',
            field=models.CharField(blank=True, choices=[('electronica', 'Electrónica y Circuitos'), ('programacion', 'Programación y Algoritmos'), ('mecanica', 'Mecánica y Estructuras'), ('ia', 'Inteligencia Artificial'), ('iot', 'Internet de las Cosas (IoT)'), ('automatizacion', 'Automatización Industrial'), ('diseno_3d', 'Diseño e Impresión 3D'), ('telecom', 'Telecomunicaciones')], help_text='DEPRECADO: Usar ClubLineaInvestigacion', max_length=50, null=True, verbose_name='Línea de investigación 1'),
        ),
        migrations.AlterField(
            model_name='club',
            name='linea_2',
            field=models.CharField(blank=True, choices=[('electronica', 'Electrónica y Circuitos'), ('programacion', 'Programación y Algoritmos'), ('mecanica', 'Mecánica y Estructuras'), ('ia', 'Inteligencia Artificial'), ('iot', 'Internet de las Cosas (IoT)'), ('automatizacion', 'Automatización Industrial'), ('diseno_3d', 'Diseño e Impresión 3D'), ('telecom', 'Telecomunicaciones')], help_text='DEPRECADO: Usar ClubLineaInvestigacion', max_length=50, null=True, verbose_name='Línea de investigación 2'),
        ),
        migrations.AlterField(
            model_name='club',
            name='linea_3',
            field=models.CharField(blank=True, choices=[('electronica', 'Electrónica y Circuitos'), ('programacion', 'Programación y Algoritmos'), ('mecanica', 'Mecánica y Estructuras'), ('ia', 'Inteligencia Artificial'), ('iot', 'Internet de las Cosas (IoT)'), ('automatizacion', 'Automatización Industrial'), ('diseno_3d', 'Diseño e Impresión 3D'), ('telecom', 'Telecomunicaciones')], help_text='DEPRECADO: Usar ClubLineaInvestigacion', max_length=50, null=True, verbose_name='Línea de investigación 3'),
        ),
        
        # 7. Modificar MembresiaClu - Remover unique_together
        migrations.AlterUniqueTogether(
            name='membresiaclu',
            unique_together=set(),
        ),
        
        # 8. Agregar índice a estado en MembresiaClu
        migrations.AlterField(
            model_name='membresiaclu',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('revision', 'En Revisión'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')], db_index=True, default='pendiente', max_length=20),
        ),
        
        # 9. Agregar índice único parcial a MembresiaClu
        migrations.AddIndex(
            model_name='membresiaclu',
            index=models.Index(condition=models.Q(('estado__in', ['pendiente', 'revision'])), fields=['club', 'institucion'], name='idx_memb_club_inst_active'),
        ),
        
        # 10. Migrar datos existentes
        migrations.RunPython(migrar_lineas_existentes, reverse_code=migrations.RunPython.noop),
    ]
