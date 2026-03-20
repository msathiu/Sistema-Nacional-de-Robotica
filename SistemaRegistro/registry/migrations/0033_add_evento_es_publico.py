# Generated migration for adding es_publico field to Evento model
# Also modifies the constraint to allow public events without institution

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0032_agregar_contacto_evento'),
    ]

    operations = [
        # Agregar campo es_publico
        migrations.AddField(
            model_name='evento',
            name='es_publico',
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text='Si es True, el evento es público para todas las instituciones. Si es False, requiere aprobación.'
            ),
        ),
        # Modificar la constraint para permitir eventos públicos sin institución
        migrations.RemoveConstraint(
            model_name='evento',
            name='evento_organizador_valido',
        ),
        migrations.AddConstraint(
            model_name='evento',
            constraint=models.CheckConstraint(
                check=(
                    # Eventos institucionales públicos (fed_central): sin necesidad de institución
                    models.Q(tipo_evento='institucional', es_publico=True, club_organizador__isnull=True) |
                    # Eventos institucionales de instituciones: requieren institución
                    models.Q(tipo_evento='institucional', es_publico=False, institucion__isnull=False, club_organizador__isnull=True) |
                    # Eventos de club
                    models.Q(tipo_evento='club', club_organizador__isnull=False, institucion__isnull=True)
                ),
                name='evento_organizador_valido'
            ),
        ),
    ]
