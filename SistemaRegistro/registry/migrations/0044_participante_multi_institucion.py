# Generated manually for multi-institution participant architecture

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("registry", "0043_remove_tutor_cedula_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParticipanteInstitucion",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("activo", "Activo"),
                            ("inactivo", "Inactivo"),
                            ("suspendido", "Suspendido"),
                            ("egresado", "Egresado"),
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
                    "grupo_actual",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="participantes_actuales",
                        to="registry.grupo",
                        verbose_name="Grupo Actual",
                    ),
                ),
                (
                    "institucion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participantes_vinculados",
                        to="registry.institucion",
                        verbose_name="Institución",
                    ),
                ),
                (
                    "participante",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vinculaciones",
                        to="registry.participante",
                        verbose_name="Participante",
                    ),
                ),
                (
                    "registrado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="participantes_registrados",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Registrado Por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vinculación Participante-Institución",
                "verbose_name_plural": "Vinculaciones Participante-Institución",
                "ordering": ["-fecha_vinculacion"],
                "unique_together": {("participante", "institucion")},
            },
        ),
        migrations.CreateModel(
            name="ParticipanteGrupo",
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
                ("fecha_ingreso", models.DateTimeField(auto_now_add=True)),
                ("fecha_salida", models.DateTimeField(blank=True, null=True)),
                ("activo", models.BooleanField(db_index=True, default=True)),
                (
                    "grupo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historial_participantes",
                        to="registry.grupo",
                    ),
                ),
                (
                    "participante",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historial_grupos",
                        to="registry.participante",
                    ),
                ),
            ],
            options={
                "verbose_name": "Participante-Grupo",
                "verbose_name_plural": "Participantes-Grupos",
                "ordering": ["-fecha_ingreso"],
                "unique_together": {("participante", "grupo")},
            },
        ),
        migrations.AddIndex(
            model_name="participanteinstitucion",
            index=models.Index(
                fields=["participante", "status"], name="idx_partinst_part_st"
            ),
        ),
        migrations.AddIndex(
            model_name="participanteinstitucion",
            index=models.Index(
                fields=["institucion", "status"], name="idx_partinst_inst_st"
            ),
        ),
        migrations.AddIndex(
            model_name="participanteinstitucion",
            index=models.Index(
                fields=["status", "-fecha_vinculacion"], name="idx_partinst_st_fecha"
            ),
        ),
        migrations.AddIndex(
            model_name="participanteinstitucion",
            index=models.Index(fields=["grupo_actual"], name="idx_partinst_grupo"),
        ),
        migrations.AddIndex(
            model_name="participantegrupo",
            index=models.Index(
                fields=["participante", "activo"], name="idx_partgrp_part_act"
            ),
        ),
        migrations.AddIndex(
            model_name="participantegrupo",
            index=models.Index(fields=["grupo", "activo"], name="idx_partgrp_grp_act"),
        ),
    ]
