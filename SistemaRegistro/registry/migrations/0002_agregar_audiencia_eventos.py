# Generated manually for adding audiencia field to Evento model

from django.db import migrations, models


def migrar_audiencia_eventos(apps, schema_editor):
    """Migra datos existentes al nuevo campo audiencia."""
    Evento = apps.get_model('registry', 'Evento')
    
    for evento in Evento.objects.all():
        if evento.tipo_evento == 'club':
            # Eventos de club son exclusivos por defecto
            evento.audiencia = 'club_exclusivo'
        elif evento.es_publico:
            # Eventos públicos (creados por fed_central)
            evento.audiencia = 'publica'
        else:
            # Eventos institucionales privados
            evento.audiencia = 'institucional_privado'
        
        evento.save(update_fields=['audiencia'])


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0001_initial'),  # Ajustar según última migración
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='audiencia',
            field=models.CharField(
                choices=[
                    ('publica', 'Pública - Todas las instituciones'),
                    ('club_exclusivo', 'Exclusivo para miembros del club'),
                    ('institucional_privado', 'Privado - Solo mi institución'),
                ],
                default='publica',
                help_text='Define quién puede ver e inscribirse al evento',
                max_length=25,
                verbose_name='Audiencia del Evento',
                db_index=True,
            ),
        ),
        migrations.RunPython(migrar_audiencia_eventos, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name='evento',
            index=models.Index(fields=['audiencia', 'estado_evento'], name='idx_evt_audiencia_estado'),
        ),
    ]
