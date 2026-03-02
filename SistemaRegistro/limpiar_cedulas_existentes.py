#!/usr/bin/env python
"""
Script para limpiar cédulas existentes en la base de datos.
Remueve los prefijos V-, E- de las cédulas personales.

Uso:
    python manage.py shell < limpiar_cedulas_existentes.py
"""

from registry.models import Participante
import re

def limpiar_cedulas():
    """Limpia las cédulas existentes removiendo prefijos V- o E-."""
    
    participantes = Participante.objects.all()
    total = participantes.count()
    actualizados = 0
    errores = 0
    
    print(f"Procesando {total} participantes...")
    
    for participante in participantes:
        try:
            # Limpiar cédula personal
            if participante.cedula:
                # Remover V-, E- y cualquier carácter no numérico
                cedula_limpia = re.sub(r'[^0-9]', '', participante.cedula)
                
                if cedula_limpia != participante.cedula:
                    print(f"Actualizando: {participante.cedula} → {cedula_limpia}")
                    participante.cedula = cedula_limpia
                    participante.save(update_fields=['cedula'])
                    actualizados += 1
            
            # Limpiar cédula escolar (si tiene)
            if participante.cedula_escolar:
                cedula_escolar_limpia = re.sub(r'[^0-9]', '', participante.cedula_escolar)
                
                if cedula_escolar_limpia != participante.cedula_escolar:
                    print(f"Actualizando cédula escolar: {participante.cedula_escolar} → {cedula_escolar_limpia}")
                    participante.cedula_escolar = cedula_escolar_limpia
                    participante.save(update_fields=['cedula_escolar'])
                    actualizados += 1
                    
        except Exception as e:
            print(f"Error procesando participante {participante.id}: {e}")
            errores += 1
    
    print(f"\n✅ Proceso completado:")
    print(f"   Total procesados: {total}")
    print(f"   Actualizados: {actualizados}")
    print(f"   Errores: {errores}")
    print(f"   Sin cambios: {total - actualizados - errores}")

if __name__ == '__main__':
    limpiar_cedulas()
