# Generated migration for TutorInstitucion model

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0036_tutor_nacionalidad_tutor_telefono_codigo_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TutorInstitucion",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "rol",
                    models.CharField(
                        choices=[
                            ("coordinador", "Coordinador"),
                            ("asistente", "Asistente"),
                            ("colaborador", "Colaborador"),
                        ],
                        default="colaborador",
                        max_length=20,
                        verbose_name="Rol",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("activo", "Activo"),
                            ("inactivo", "Inactivo"),
                            ("suspendido", "Suspendido"),
                        ],
                        db_index=True,
                        default="activo",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "fecha_vinculacion",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de Vinculación"
                    ),
                ),
                (
                    "fecha_desvinculacion",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Fecha de Desvinculación"
                    ),
                ),
                (
                    "observaciones",
                    models.TextField(blank=True, verbose_name="Observaciones"),
                ),
                (
                    "institucion",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="tutores_vinculados",
                        to="registry.institucion",
                        verbose_name="Institución",
                    ),
                ),
                (
                    "tutor",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="vinculaciones",
                        to="registry.tutor",
                        verbose_name="Tutor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vinculación Tutor-Institución",
                "verbose_name_plural": "Vinculaciones Tutor-Institución",
                "ordering": ["-fecha_vinculacion"],
            },
        ),
        migrations.AddIndex(
            model_name="tutorinstitucion",
            index=models.Index(fields=["tutor", "status"], name="idx_tutinst_tutor_st"),
        ),
        migrations.AddIndex(
            model_name="tutorinstitucion",
            index=models.Index(
                fields=["institucion", "status"], name="idx_tutinst_inst_st"
            ),
        ),
        migrations.AddIndex(
            model_name="tutorinstitucion",
            index=models.Index(
                fields=["status", "-fecha_vinculacion"], name="idx_tutinst_st_fecha"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="tutorinstitucion",
            unique_together={("tutor", "institucion")},
        ),
    ]
