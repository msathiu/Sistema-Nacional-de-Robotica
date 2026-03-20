from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '1000_merge_20260308_1825'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- Corregir registry_asistenciaevento.participante_id
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'registry_asistenciaevento' 
                    AND column_name = 'participante_id'
                    AND data_type != 'uuid'
                ) THEN
                    ALTER TABLE registry_asistenciaevento 
                    ALTER COLUMN participante_id TYPE uuid USING participante_id::text::uuid;
                END IF;
                
                -- Corregir registry_participantegrupo.participante_id
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'registry_participantegrupo' 
                    AND column_name = 'participante_id'
                    AND data_type != 'uuid'
                ) THEN
                    ALTER TABLE registry_participantegrupo 
                    ALTER COLUMN participante_id TYPE uuid USING participante_id::text::uuid;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
