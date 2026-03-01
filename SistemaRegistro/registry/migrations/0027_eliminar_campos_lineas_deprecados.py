# Generated manually para eliminar campos deprecados de líneas de investigación
# Esta migración es parte de la transición de linea_X → ClubLineaInvestigacion

from django.db import migrations, models


def verificar_migracion_lineas(apps, schema_editor):
    """
    Verifica que todos los clubes tengan sus líneas migradas a ClubLineaInvestigacion.
    Migra cualquier dato pendiente antes de eliminar los campos.
    """
    Club = apps.get_model('registry', 'Club')
    LineaInvestigacion = apps.get_model('registry', 'LineaInvestigacion')
    ClubLineaInvestigacion = apps.get_model('registry', 'ClubLineaInvestigacion')
    
    # Mapeo de códigos antiguos a líneas existentes
    lineas_map = {
        'electronica': 'Electrónica y Circuitos',
        'programacion': 'Programación y Algoritmos',
        'mecanica': 'Mecánica y Estructuras',
        'ia': 'Inteligencia Artificial',
        'iot': 'Internet de las Cosas (IoT)',
        'automatizacion': 'Automatización Industrial',
        'diseno_3d': 'Diseño e Impresión 3D',
        'telecom': 'Telecomunicaciones',
    }
    
    # Obtener o crear líneas de investigación
    lineas_creadas = {}
    for codigo, nombre in lineas_map.items():
        try:
            linea = LineaInvestigacion.objects.get(codigo=codigo)
            lineas_creadas[codigo] = linea
        except LineaInvestigacion.DoesNotExist:
            # Si no existe, crear la línea
            linea = LineaInvestigacion.objects.create(
                codigo=codigo,
                nombre=nombre,
                activa=True,
                orden=list(lineas_map.keys()).index(codigo) + 1
            )
            lineas_creadas[codigo] = linea
    
    # Verificar si los campos existen en el modelo (puede que ya hayan sido eliminados)
    club_fields = Club._meta.get_fields()
    campos_existen = any(f.name == 'linea_1' for f in club_fields)
    
    if not campos_existen:
        print("Los campos linea_1, linea_2, linea_3 ya fueron eliminados del modelo.")
        print("Verificando que todos los clubes tengan líneas en el nuevo sistema...")
        
        # Solo verificar que las líneas existan, no migrar desde campos antiguos
        clubes_sin_lineas = 0
        for club in Club.objects.all():
            tiene_lineas = ClubLineaInvestigacion.objects.filter(club=club).exists()
            if not tiene_lineas:
                print(f"Club {club.id} no tiene líneas de investigación asignadas.")
                clubes_sin_lineas += 1
        
        if clubes_sin_lineas > 0:
            print(f"Advertencia: {clubes_sin_lineas} clubes no tienen líneas de investigación.")
        else:
            print("Todos los clubes tienen líneas de investigación correctamente configuradas.")
        return
    
    # Migrar cualquier club que aún tenga datos en campos antiguos
    clubes_migrados = 0
    for club in Club.objects.all():
        # Verificar si ya tiene líneas en el nuevo sistema
        tiene_lineas_nuevas = ClubLineaInvestigacion.objects.filter(club=club).exists()
        
        if not tiene_lineas_nuevas:
            # Migrar desde campos antiguos (solo si los campos existen)
            orden = 1
            
            # Usar getattr para safely obtener los valores de los campos
            linea_1 = getattr(club, 'linea_1', None)
            linea_2 = getattr(club, 'linea_2', None)
            linea_3 = getattr(club, 'linea_3', None)
            
            if linea_1 and linea_1 in lineas_creadas:
                ClubLineaInvestigacion.objects.get_or_create(
                    club=club,
                    linea=lineas_creadas[linea_1],
                    defaults={'tipo_linea': 'principal', 'orden': orden}
                )
                orden += 1
            
            if linea_2 and linea_2 in lineas_creadas:
                ClubLineaInvestigacion.objects.get_or_create(
                    club=club,
                    linea=lineas_creadas[linea_2],
                    defaults={'tipo_linea': 'soporte', 'orden': orden}
                )
                orden += 1
            
            if linea_3 and linea_3 in lineas_creadas:
                ClubLineaInvestigacion.objects.get_or_create(
                    club=club,
                    linea=lineas_creadas[linea_3],
                    defaults={'tipo_linea': 'afines', 'orden': orden}
                )
            
            clubes_migrados += 1
    
    if clubes_migrados > 0:
        print(f"Migración completada: {clubes_migrados} clubes migrados a ClubLineaInvestigacion")
    else:
        print("Todos los clubes ya tenían sus líneas migradas correctamente")


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0026_remove_membresiaclu_idx_memb_club_inst_active_and_more'),
    ]

    operations = [
        # 1. Verificar y migrar cualquier dato pendiente
        migrations.RunPython(
            verificar_migracion_lineas,
            reverse_code=migrations.RunPython.noop
        ),
        
        # 2. Eliminar campos deprecados del modelo Club
        migrations.RemoveField(
            model_name='club',
            name='linea_1',
        ),
        migrations.RemoveField(
            model_name='club',
            name='linea_2',
        ),
        migrations.RemoveField(
            model_name='club',
            name='linea_3',
        ),
    ]
