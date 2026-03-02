# Migración de Líneas de Investigación: linea_X → ClubLineaInvestigacion

## Resumen

Se ha completado la migración de los campos deprecados `linea_1`, `linea_2`, `linea_3` del modelo `Club` al nuevo sistema de relación N:M usando `ClubLineaInvestigacion`.

## Fecha de Completación
2026-02-24

## Cambios Realizados

### 1. Nueva Migración Creada
- **Archivo**: `SistemaRegistro/registry/migrations/0027_eliminar_campos_lineas_deprecados.py`
- **Función**: 
  - Verifica que todos los clubes tengan sus líneas migradas a `ClubLineaInvestigacion`
  - Migra cualquier dato pendiente antes de eliminar los campos
  - Elimina los campos `linea_1`, `linea_2`, `linea_3` de la base de datos

### 2. Modelo Club Actualizado
- **Archivo**: `SistemaRegistro/registry/models.py`
- **Cambios**:
  - Eliminada constante `LINEAS_INVESTIGACION_CHOICES`
  - Eliminados campos `linea_1`, `linea_2`, `linea_3`
  - Actualizada propiedad `lineas_investigacion` para usar exclusivamente `ClubLineaInvestigacion`

### 3. Admin Actualizado
- **Archivo**: `SistemaRegistro/registry/admin.py`
- **Cambios**:
  - Eliminado fieldset "Líneas de Investigación (DEPRECADO)"
  - Se mantiene `ClubLineaInvestigacionInline` para gestión de líneas

### 4. Formularios Limpiados
- **Archivo**: `SistemaRegistro/registry/forms.py`
- **Cambios**:
  - Eliminado código duplicado en `ClubForm`
  - El formulario ya usaba los campos nuevos `linea_investigacion_1`, `linea_investigacion_2`, `linea_investigacion_3`

## Arquitectura Final

### Modelo Club
```python
class Club(models.Model):
    # ... otros campos ...
    
    # Las líneas de investigación ahora se gestionan mediante:
    # - club_lineas (related_name) → ClubLineaInvestigacion
```

### Modelo ClubLineaInvestigacion
```python
class ClubLineaInvestigacion(models.Model):
    club = models.ForeignKey(Club, related_name='club_lineas')
    linea = models.ForeignKey(LineaInvestigacion, related_name='clubes')
    tipo_linea = models.CharField()  # principal, soporte, afines
    orden = models.IntegerField()
```

### Modelo LineaInvestigacion
```python
class LineaInvestigacion(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    activa = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)
```

## Beneficios

1. **Flexibilidad**: Las líneas de investigación son ahora dinámicas y gestionables desde el admin
2. **Escalabilidad**: No hay límite de 3 líneas por club
3. **Mantenibilidad**: Código más limpio sin campos deprecados
4. **Integridad**: Relaciones foreign key en lugar de choices hardcodeados

## Instrucciones de Despliegue

1. **Backup**: Realizar backup de la base de datos antes de aplicar la migración
2. **Aplicar migración**:
   ```bash
   cd SistemaRegistro
   python manage.py migrate registry
   ```
3. **Verificar**: Comprobar que los clubes tienen sus líneas asignadas correctamente

## Rollback

En caso de necesitar revertir:
1. Restaurar backup de base de datos
2. Revertir cambios en código a versión anterior

## Notas Técnicas

- La migración 0019 ya había realizado la migración inicial de datos
- La migración 0027 asegura que no queden datos sin migrar y elimina los campos
- Los formularios ya estaban preparados para el nuevo sistema
- No se requieren cambios en templates (no usaban los campos antiguos directamente)
