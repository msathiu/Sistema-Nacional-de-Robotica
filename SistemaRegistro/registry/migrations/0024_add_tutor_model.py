# Generated migration for Tutor model
# Implements: modelo_tutor.md - Registro de Tutores

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):
    """
    Migración para crear el modelo Tutor y agregar relación M2M al modelo Grupo.

    Cambios:
    - Crea el modelo Tutor con UUID, FK a Institucion, campos requeridos
    - Agrega relación M2M entre Grupo y Tutor (manteniendo campos legacy)
    """

    dependencies = [
        ("registry", "0023_workflow_federado_membresias"),
    ]

    operations = [
        # Crear modelo Tutor
        migrations.CreateModel(
            name="Tutor",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombres", models.CharField(max_length=100, verbose_name="Nombres")),
                (
                    "apellidos",
                    models.CharField(max_length=100, verbose_name="Apellidos"),
                ),
                (
                    "cedula",
                    models.CharField(
                        db_index=True,
                        max_length=20,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Cédula válida requerida (solo números y V/E)",
                                regex="^[VE0-9]+$",
                            )
                        ],
                        verbose_name="Cédula",
                    ),
                ),
                ("telefono", models.CharField(max_length=20, verbose_name="Teléfono")),
                (
                    "email",
                    models.EmailField(
                        max_length=254, verbose_name="Correo Electrónico"
                    ),
                ),
                (
                    "profesion",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Profesión"
                    ),
                ),
                (
                    "experiencia",
                    models.TextField(
                        blank=True, verbose_name="Experiencia en Robótica"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("activo", "Activo"), ("inactivo", "Inactivo")],
                        db_index=True,
                        default="activo",
                        max_length=10,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de Creación"
                    ),
                ),
                (
                    "institucion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tutores",
                        to="registry.institucion",
                        verbose_name="Institución",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tutor",
                "verbose_name_plural": "Tutores",
                "ordering": ["-created_at"],
            },
        ),
        # Agregar índices adicionales al modelo Tutor
        migrations.AddIndex(
            model_name="tutor",
            index=models.Index(fields=["cedula"], name="idx_tutor_cedula"),
        ),
        migrations.AddIndex(
            model_name="tutor",
            index=models.Index(
                fields=["status", "institucion"], name="idx_tutor_status_inst"
            ),
        ),
        # Agregar relación M2M tutores al modelo Grupo
        migrations.AddField(
            model_name="grupo",
            name="tutores",
            field=models.ManyToManyField(
                blank=True,
                related_name="grupos",
                to="registry.tutor",
                verbose_name="Tutores asignados",
            ),
        ),
    ]
