from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "1003_grupo_unique_nombre_evento_case_insensitive_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="evento",
            name="fecha_hasta",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.RunSQL(
            sql="""
                UPDATE registry_evento
                SET fecha_hasta = fecha
                WHERE fecha_hasta IS NULL AND fecha IS NOT NULL;
            """,
            reverse_sql="""
                UPDATE registry_evento
                SET fecha_hasta = NULL
                WHERE fecha_hasta = fecha;
            """,
        ),
    ]
