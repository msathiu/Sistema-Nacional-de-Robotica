from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0010_alter_club_fecha_creacion_and_more"),
    ]

    operations = [
        # Agregar campos a Evento
        migrations.AddField(
            model_name="evento",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("competencia", "Competencia"),
                    ("taller", "Taller"),
                    ("seminario", "Seminario"),
                    ("exhibicion", "Exhibición"),
                ],
                default="competencia",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="evento",
            name="modalidad",
            field=models.CharField(
                choices=[
                    ("presencial", "Presencial"),
                    ("virtual", "Virtual"),
                    ("hibrido", "Híbrido"),
                ],
                default="presencial",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="evento",
            name="ubicacion",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="evento",
            name="estado_evento",
            field=models.CharField(
                choices=[
                    ("abierto", "Abierto"),
                    ("pausado", "Pausado"),
                    ("cerrado", "Cerrado"),
                    ("finalizado", "Finalizado"),
                ],
                db_index=True,
                default="abierto",
                max_length=20,
            ),
        ),
        # Agregar campos a Grupo
        migrations.AddField(
            model_name="grupo",
            name="codigo",
            field=models.CharField(
                default="GRP-00000000", editable=False, max_length=20
            ),
        ),
        migrations.AddField(
            model_name="grupo",
            name="criterio",
            field=models.CharField(
                choices=[
                    ("edad", "Por Edad"),
                    ("nivel", "Por Nivel Educativo"),
                    ("proyecto", "Por Proyecto"),
                    ("mixto", "Mixto"),
                ],
                default="mixto",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="grupo",
            name="estado_grupo",
            field=models.CharField(
                choices=[
                    ("editable", "Editable"),
                    ("inscrito", "Inscrito"),
                    ("bloqueado", "Bloqueado"),
                ],
                db_index=True,
                default="editable",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="grupo",
            name="tutor_apellidos",
            field=models.CharField(default="", max_length=200),
        ),
        # Agregar campos a Club
        migrations.AddField(
            model_name="club",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="clubes/logos/"),
        ),
        migrations.AddField(
            model_name="club",
            name="siglas",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="club",
            name="fecha_fundacion",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="club",
            name="institucion_creadora",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="clubes_creados",
                to="registry.institucion",
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="estado_vinculacion",
            field=models.CharField(
                choices=[
                    ("abierto", "Abierto"),
                    ("cerrado", "Cerrado"),
                    ("invitacion", "Bajo Invitación"),
                ],
                default="abierto",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="cupo_maximo",
            field=models.IntegerField(
                default=10, verbose_name="Cupo máximo de instituciones"
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="requisitos",
            field=models.TextField(blank=True),
        ),
        # Crear modelo MembresiaClu
        migrations.CreateModel(
            name="MembresiaClu",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("carta_intencion", models.TextField()),
                ("propuesta_tecnica", models.TextField()),
                ("representante_legal", models.CharField(max_length=200)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("revision", "En Revisión"),
                            ("aprobada", "Aprobada"),
                            ("rechazada", "Rechazada"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("fecha_solicitud", models.DateTimeField(auto_now_add=True)),
                ("fecha_respuesta", models.DateTimeField(blank=True, null=True)),
                ("observaciones", models.TextField(blank=True)),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="membresias",
                        to="registry.club",
                    ),
                ),
                (
                    "institucion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registry.institucion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Membresía de Club",
                "verbose_name_plural": "Membresías de Clubes",
                "ordering": ["-fecha_solicitud"],
                "unique_together": {("club", "institucion")},
            },
        ),
        # Crear modelo InscripcionGrupoEvento
        migrations.CreateModel(
            name="InscripcionGrupoEvento",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "rol_participacion",
                    models.CharField(
                        choices=[
                            ("participante", "Participante"),
                            ("expositor", "Expositor"),
                            ("competidor", "Competidor"),
                        ],
                        default="participante",
                        max_length=20,
                    ),
                ),
                ("fecha_inscripcion", models.DateTimeField(auto_now_add=True)),
                ("activo", models.BooleanField(default=True)),
                (
                    "evento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inscripciones_grupo",
                        to="registry.evento",
                    ),
                ),
                (
                    "grupo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inscripciones",
                        to="registry.grupo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Inscripción Grupo-Evento",
                "verbose_name_plural": "Inscripciones Grupo-Evento",
                "ordering": ["-fecha_inscripcion"],
                "unique_together": {("evento", "grupo")},
            },
        ),
    ]
