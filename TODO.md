# Plan para agregar campos adicionales al admin de Institucion

## Información Recopilada:

### Campos del formulario de registro (registrar_institucion.html):
1. tipo_institucion - Tipo de Institución
2. naturaleza - Naturaleza (pública/privada)
3. subcategoria - Subcategoría
4. dependencia_existente / nueva_dependencia - Dependencia
5. nombre - Razón Social
6. rif - RIF (letra + número)
7. codigo_mppe - Código MPPE
8. estado, municipio, parroquia - Ubicación
9. direccion - Dirección
10. email - Correo
11. telefono - Teléfono (código área + número)

### Campos ya existentes en el modelo Institucion:
- tipo_institucion, naturaleza, subcategoria
- dependencia, dependencia_rel
- codigo_mppe

### Campos actualmente en el admin.py:
- list_display: codigo, nombre, estado, email, activa
- fieldsets: Información básica

## Implementación Completada:

### Archivo: SistemaRegistro/registry/admin.py
- [x] 1. Agregar campos adicionales a list_display: codigo, nombre, tipo_institucion, naturaleza, rif, email, estado, activa, federado
- [x] 2. Actualizar fieldsets para mostrar más campos (nueva sección "Datos de Identificación Institucional")
- [x] 3. Actualizar exportar_excel para incluir los nuevos campos

### Campos agregados al admin y Excel:
1. tipo_institucion (Tipo de Institución)
2. naturaleza (Naturaleza)
3. subcategoria (Subcategoría)
4. dependencia (texto de dependencia)
5. codigo_mppe (Código MPPE)

### Campos adicionales en Excel:
- Dirección
- Estatus

## Resultado:
- El panel de administración ahora muestra más campos en la lista de instituciones
- Los filtros laterales ahora incluyen tipo_institucion y naturaleza
- La búsqueda ahora incluye rif y codigo_mppe
- La exportación a Excel ahora incluye 18 columnas con todos los datos de registro
