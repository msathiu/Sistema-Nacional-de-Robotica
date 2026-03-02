# 🔄 Guía de Migración: Cédulas Solo Números

## 📋 Resumen

Esta guía te ayudará a migrar las cédulas existentes en la base de datos para que guarden **solo números** sin prefijos (V-, E-).

---

## ⚠️ IMPORTANTE: Antes de Comenzar

### 1. Hacer Backup de la Base de Datos

```bash
# Para SQLite
cp SistemaRegistro/db.sqlite3 SistemaRegistro/db.sqlite3.backup

# Para PostgreSQL
pg_dump nombre_base_datos > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🔧 Pasos de Migración

### Paso 1: Ejecutar el Script de Limpieza

```bash
cd SistemaRegistro
python manage.py shell < limpiar_cedulas_existentes.py
```

**Salida esperada:**
```
Procesando 150 participantes...
Actualizando: V-19122516 → 19122516
Actualizando: E-12345678 → 12345678
...

✅ Proceso completado:
   Total procesados: 150
   Actualizados: 150
   Errores: 0
   Sin cambios: 0
```

---

### Paso 2: Verificar los Cambios

```bash
python manage.py shell
```

```python
from registry.models import Participante

# Ver algunos ejemplos
participantes = Participante.objects.all()[:5]
for p in participantes:
    print(f"ID: {p.id}, Cédula: {p.cedula}, Escolar: {p.cedula_escolar}")

# Verificar que no haya cédulas con V- o E-
con_prefijo = Participante.objects.filter(cedula__startswith='V-') | Participante.objects.filter(cedula__startswith='E-')
print(f"Cédulas con prefijo: {con_prefijo.count()}")  # Debe ser 0
```

---

### Paso 3: Probar el Registro de Nuevos Participantes

1. Ir a la página de registro: http://localhost:8000/registro/participante/
2. Ingresar una cédula con formato: "12.345.678"
3. Verificar que se limpie automáticamente a: "12345678"
4. Guardar y verificar en la base de datos

```python
# En Django shell
from registry.models import Participante
ultimo = Participante.objects.last()
print(f"Última cédula guardada: {ultimo.cedula}")  # Debe ser solo números
```

---

## 🔍 Verificación de Integridad

### Script de Verificación

```python
from registry.models import Participante
import re

def verificar_cedulas():
    """Verifica que todas las cédulas sean solo números."""
    
    participantes = Participante.objects.all()
    problemas = []
    
    for p in participantes:
        # Verificar cédula personal
        if p.cedula and not p.cedula.isdigit():
            problemas.append({
                'id': p.id,
                'nombre': f"{p.nombres} {p.apellidos}",
                'cedula': p.cedula,
                'tipo': 'personal'
            })
        
        # Verificar cédula escolar
        if p.cedula_escolar and not p.cedula_escolar.isdigit():
            problemas.append({
                'id': p.id,
                'nombre': f"{p.nombres} {p.apellidos}",
                'cedula': p.cedula_escolar,
                'tipo': 'escolar'
            })
    
    if problemas:
        print(f"⚠️ Se encontraron {len(problemas)} problemas:")
        for prob in problemas:
            print(f"  - ID {prob['id']}: {prob['nombre']} - {prob['tipo']}: {prob['cedula']}")
    else:
        print("✅ Todas las cédulas están correctas (solo números)")
    
    return problemas

# Ejecutar verificación
verificar_cedulas()
```

---

## 🐛 Solución de Problemas

### Problema 1: Error de Unicidad

**Error:**
```
IntegrityError: UNIQUE constraint failed: registry_participante.cedula
```

**Causa:** Dos participantes con la misma cédula (uno con V- y otro sin)

**Solución:**
```python
from registry.models import Participante
from django.db.models import Count

# Encontrar duplicados
duplicados = Participante.objects.values('cedula').annotate(
    count=Count('id')
).filter(count__gt=1)

for dup in duplicados:
    print(f"Cédula duplicada: {dup['cedula']}")
    participantes = Participante.objects.filter(cedula=dup['cedula'])
    for p in participantes:
        print(f"  - ID: {p.id}, Nombre: {p.nombres} {p.apellidos}")
```

---

### Problema 2: Cédulas con Caracteres Especiales

**Síntoma:** Algunas cédulas tienen puntos, guiones, etc.

**Solución:**
```python
from registry.models import Participante
import re

participantes = Participante.objects.all()
for p in participantes:
    if p.cedula:
        cedula_limpia = re.sub(r'[^0-9]', '', p.cedula)
        if cedula_limpia != p.cedula:
            print(f"Limpiando: {p.cedula} → {cedula_limpia}")
            p.cedula = cedula_limpia
            p.save(update_fields=['cedula'])
```

---

## 📊 Cambios en el Sistema

### Antes de la Migración

```
Base de Datos:
  cedula = "V-19122516"
  cedula_escolar = "123456"

Username:
  username = "V-19122516"
```

### Después de la Migración

```
Base de Datos:
  cedula = "19122516"  ✅ Solo números
  cedula_escolar = "123456"  ✅ Solo números

Username:
  username = "V-19122516"  ✅ Se mantiene con V- para login
```

**Nota:** El username se mantiene con el formato V- para que los usuarios puedan seguir iniciando sesión con su cédula completa.

---

## 🔄 Rollback (Si es Necesario)

Si algo sale mal, puedes restaurar el backup:

```bash
# Para SQLite
cp SistemaRegistro/db.sqlite3.backup SistemaRegistro/db.sqlite3

# Para PostgreSQL
psql nombre_base_datos < backup_YYYYMMDD_HHMMSS.sql
```

---

## ✅ Checklist de Migración

- [ ] Backup de base de datos creado
- [ ] Script de limpieza ejecutado
- [ ] Verificación de integridad completada
- [ ] Prueba de registro de nuevo participante
- [ ] Verificación de login existente
- [ ] Búsquedas funcionando correctamente
- [ ] Reportes generando datos correctos

---

## 📞 Soporte

Si encuentras problemas durante la migración:

1. **No elimines el backup**
2. Documenta el error exacto
3. Verifica los logs: `SistemaRegistro/logs/`
4. Contacta al equipo de desarrollo

---

## 🎯 Resultado Esperado

Después de la migración:

✅ Todas las cédulas en BD: solo números  
✅ Nuevos registros: solo números  
✅ Login: funciona con V-cedula  
✅ Búsquedas: más rápidas y precisas  
✅ Reportes: datos consistentes  

---

**Fecha**: 2024  
**Versión**: 1.0  
**Estado**: Listo para ejecutar
