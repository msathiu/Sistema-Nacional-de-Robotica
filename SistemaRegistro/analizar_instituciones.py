#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SistemaRegistro.settings")
django.setup()

from registry.models.institucion import Institucion

def analizar_instituciones():
    print("🔍 Analizando instituciones por tipo...")

    tipos = ['particular', 'educativa', 'publica', 'privada', 'otra']
    inconsistencias = []

    for tipo in tipos:
        print(f"\n--- Tipo: {tipo.upper()} ---")
        instituciones = Institucion.objects.filter(tipo_institucion=tipo, eliminado=False)

        print(f"Total instituciones: {instituciones.count()}")

        # Campos que deberían estar vacíos para 'particular'
        if tipo == 'particular':
            campos_vacios_esperados = ['naturaleza', 'subcategoria', 'categoria', 'dependencia', 'codigo_mppe', 'institucion_procedencia']
            for campo in campos_vacios_esperados:
                count_no_vacio = instituciones.exclude(**{campo: None}).exclude(**{campo: ''}).count()
                if count_no_vacio > 0:
                    print(f"  ⚠️  Campo '{campo}' tiene valores en {count_no_vacio} registros")
                    # Obtener ejemplos
                    ejemplos = instituciones.exclude(**{campo: None}).exclude(**{campo: ''}).values_list('id', 'nombre', campo)[:3]
                    for ej in ejemplos:
                        inconsistencias.append({
                            'tipo': tipo,
                            'campo': campo,
                            'id': ej[0],
                            'nombre': ej[1],
                            'valor': ej[2]
                        })

            # Campos que deberían tener valores para 'particular'
            campos_con_valor_esperados = ['particular_nombres', 'particular_apellidos', 'particular_cedula']
            for campo in campos_con_valor_esperados:
                count_vacio = instituciones.filter(**{campo: None}).filter(**{campo: ''}).count()
                if count_vacio > 0:
                    print(f"  ⚠️  Campo '{campo}' está vacío en {count_vacio} registros")
                    ejemplos = instituciones.filter(**{campo: None}).filter(**{campo: ''}).values_list('id', 'nombre')[:3]
                    for ej in ejemplos:
                        inconsistencias.append({
                            'tipo': tipo,
                            'campo': campo,
                            'id': ej[0],
                            'nombre': ej[1],
                            'valor': None
                        })

        # Para 'educativa', codigo_mppe debería tener valor
        elif tipo == 'educativa':
            count_sin_codigo_mppe = instituciones.filter(codigo_mppe__isnull=True).filter(codigo_mppe='').count()
            if count_sin_codigo_mppe > 0:
                print(f"  ⚠️  Campo 'codigo_mppe' está vacío en {count_sin_codigo_mppe} registros")
                ejemplos = instituciones.filter(codigo_mppe__isnull=True).filter(codigo_mppe='').values_list('id', 'nombre')[:3]
                for ej in ejemplos:
                    inconsistencias.append({
                        'tipo': tipo,
                        'campo': 'codigo_mppe',
                        'id': ej[0],
                        'nombre': ej[1],
                        'valor': None
                    })

        # Mostrar algunos campos clave
        campos_clave = ['naturaleza', 'subcategoria', 'categoria', 'dependencia', 'codigo_mppe', 'institucion_procedencia']
        for campo in campos_clave:
            valores_unicos = instituciones.exclude(**{campo: None}).exclude(**{campo: ''}).values_list(campo, flat=True).distinct()[:5]
            if valores_unicos:
                print(f"  {campo}: {list(valores_unicos)}")

    print("\n--- INCONSISTENCIAS ENCONTRADAS ---")
    if inconsistencias:
        for inc in inconsistencias[:20]:  # Limitar a 20 ejemplos
            print(f"Tipo: {inc['tipo']}, Campo: {inc['campo']}, ID: {inc['id']}, Nombre: {inc['nombre']}, Valor: {inc['valor']}")
    else:
        print("No se encontraron inconsistencias.")

if __name__ == "__main__":
    analizar_instituciones()