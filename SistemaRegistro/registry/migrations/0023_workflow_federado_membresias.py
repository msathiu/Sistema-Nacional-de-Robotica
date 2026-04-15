# Generated migration for federated admission workflow
# Implements: permisos_clubes.md - Sección 6

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def migrar_estados_membresias(apps, schema_editor):
    """
    Migra los estados existentes de membresías al nuevo sistema federado.

    Mapeo de estados:
    - pendiente -> pendiente_filtro
    - revision -> pendiente_filtro (reinicia el proceso)
    - aprobada -> miembro_activo (con flags de auditoría)
    - rechazada -> rechazada (sin cambios)
    """
    MembresiaClu = apps.get_model("registry", "MembresiaClu")

    # Migrar pendientes y revisiones a pendiente_filtro
    MembresiaClu.objects.filter(estado="pendiente").update(estado="pendiente_filtro")
    MembresiaClu.objects.filter(estado="revision").update(estado="pendiente_filtro")

    # Migrar aprobadas a miembro_activo con flags de auditoría
    # Nota: Como no tenemos los datos de quién aprobó, marcamos los flags
    # pero dejamos los campos de usuario vacíos (null)
    MembresiaClu.objects.filter(estado="aprobada").update(
        estado="miembro_activo", visto_bueno_fundadora=True, aprobacion_ente_rector=True
    )

    print("✅ Migración de estados completada exitosamente.")


def revertir_estados_membresias(apps, schema_editor):
    """
    Revierte los estados al sistema anterior.
    """
    MembresiaClu = apps.get_model("registry", "MembresiaClu")

    MembresiaClu.objects.filter(estado="pendiente_filtro").update(estado="pendiente")
    MembresiaClu.objects.filter(estado="visto_bueno_fundadora").update(
        estado="revision"
    )
    MembresiaClu.objects.filter(estado="miembro_activo").update(estado="aprobada")

    print("✅ Reversión de estados completada.")


class Migration(migrations.Migration):
    """
    Migración para implementar el workflow federado de membresías.

    Cambios según permisos_clubes.md - Sección 6:
    1. Nuevos estados federados: pendiente_filtro, visto_bueno_fundadora, miembro_activo
    2. Campos de auditoría para trazabilidad por fase
    3. Migración de datos existentes
    """

    dependencies = [
        ("registry", "0022_alter_evento_estado_evento"),
    ]

    operations = [
        # === PASO 1: Agregar nuevos campos de auditoría ===
        # Fase 1: Visto bueno Fundadora
        migrations.AddField(
            model_name="membresiaclu",
            name="visto_bueno_fundadora",
            field=models.BooleanField(
                default=False, verbose_name="Visto Bueno Fundadora"
            ),
        ),
        migrations.AddField(
            model_name="membresiaclu",
            name="visto_bueno_fundadora_por",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="membresias_visto_bueno",
                to="auth.user",
                verbose_name="Visto bueno dado por",
            ),
        ),
        migrations.AddField(
            model_name="membresiaclu",
            name="visto_bueno_fundadora_fecha",
            field=models.DateTimeField(
                null=True, blank=True, verbose_name="Fecha visto bueno"
            ),
        ),
        migrations.AddField(
            model_name="membresiaclu",
            name="observaciones_fundadora",
            field=models.TextField(
                blank=True, verbose_name="Observaciones de la Fundadora"
            ),
        ),
        # Fase 2: Aprobación Ente Rector
        migrations.AddField(
            model_name="membresiaclu",
            name="aprobacion_ente_rector",
            field=models.BooleanField(
                default=False, verbose_name="Aprobación Ente Rector"
            ),
        ),
        migrations.AddField(
            model_name="membresiaclu",
            name="aprobacion_ente_rector_por",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="membresias_aprobadas_rector",
                to="auth.user",
                verbose_name="Aprobado por (Ente Rector)",
            ),
        ),
        migrations.AddField(
            model_name="membresiaclu",
            name="aprobacion_ente_rector_fecha",
            field=models.DateTimeField(
                null=True, blank=True, verbose_name="Fecha aprobación Ente Rector"
            ),
        ),
        migrations.AddField(
            model_name="membresiaclu",
            name="observaciones_rector",
            field=models.TextField(
                blank=True, verbose_name="Observaciones del Ente Rector"
            ),
        ),
        # === PASO 2: Migrar datos existentes ===
        migrations.RunPython(migrar_estados_membresias, revertir_estados_membresias),
        # === PASO 3: Actualizar campo estado con nuevos choices ===
        migrations.AlterField(
            model_name="membresiaclu",
            name="estado",
            field=models.CharField(
                choices=[
                    ("pendiente_filtro", "Pendiente de Filtro (Fundadora)"),
                    ("visto_bueno_fundadora", "Visto Bueno Fundadora"),
                    ("miembro_activo", "Miembro Activo"),
                    ("rechazada", "Rechazada"),
                ],
                db_index=True,
                default="pendiente_filtro",
                max_length=25,
            ),
        ),
        # === PASO 4: Actualizar índice parcial ===
        migrations.RemoveIndex(
            model_name="membresiaclu",
            name="idx_memb_club_inst_active",
        ),
        migrations.AddIndex(
            model_name="membresiaclu",
            index=models.Index(
                condition=models.Q(
                    ("estado__in", ["pendiente_filtro", "visto_bueno_fundadora"])
                ),
                fields=["club", "institucion"],
                name="idx_memb_club_inst_active",
            ),
        ),
    ]
