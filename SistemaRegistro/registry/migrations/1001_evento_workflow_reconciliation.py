# Generated manually to reconcile Evento schema with the current workflow model.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0054_alter_evento_estado_evento_alter_participante_id_and_more"),
        ("registry", "1000_merge_20260308_1825"),
    ]

    operations = [
        migrations.AddField(
            model_name="evento",
            name="observacion_estado",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Motivo de pausa, rechazo o cancelación",
            ),
        ),
        migrations.AlterField(
            model_name="evento",
            name="estado_evento",
            field=models.CharField(
                choices=[
                    ("borrador", "Borrador"),
                    ("revision", "En Revisión"),
                    ("abierto", "Abierto para Inscripción"),
                    ("rechazado", "Rechazado"),
                    ("cancelado", "Cancelado"),
                    ("pausado", "Pausado"),
                    ("en_proceso", "En Proceso"),
                    ("finalizado", "Finalizado"),
                ],
                db_index=True,
                default="borrador",
                max_length=20,
            ),
        ),
    ]
