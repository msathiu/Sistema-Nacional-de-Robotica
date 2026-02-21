# Plan de Implementación: Clubes en Dashboards

## Información Recopilada

### Modelos Existentes
- `Club` en registry/models.py - Completo con status, coordinador, líneas de investigación, membresías
- `MembresiaClu` - Gestiona membresías de instituciones a clubes
- `Institucion` - Ya tiene relación con Clubes (`clubes_creados`)

### Roles de Usuario
- `participante` - Participante regular
- `institutional` - Usuario institucional (gestiona su institución)
- `fed_central` - Federación Central (Admin Nacional)
- `fed_regional` - Federación Regional
- `tecnologico` - Admin Tecnológico
- `superuser` - Superusuario Django

### Dashboards Actuales
- **dashboard_admin.html** - Ya tiene tarjeta de Clubes con `{{ total_clubes }}` ✅
- **dashboard_institucional.html** - NO tiene datos de clubes ❌

---

## Plan de Implementación

### Fase 1: Actualizar Vista dashboard_institucional (users/views.py)
**Objetivo:** Agregar métricas de clubes al contexto

**Cambios necesarios:**
1. Importar modelos `Club` y `MembresiaClu`
2. Agregar métricas:
   - `mis_clubes` - Clubes creados por la institución
   - `clubes_disponibles` - Clubes a los que puede postular
   - `membresias_activas` - Membresías aprobadas
   - `mis_membresias` - Todas las membresías de la institución

### Fase 2: Actualizar Template dashboard_institucional.html
**Objetivo:** Agregar tarjetas y secciones de clubes

**Cambios necesarios:**
1. Agregar fila de KPIs de clubes (similar a otros dashboards)
2. Agregar sección de "Mis Clubes" con lista reciente
3. Agregar acceso a "Clubes Disponibles"

### Fase 3: Verificar Links de Navegación
**Objetivo:** Asegurar que los menús tengan enlaces a clubes

**Cambios necesarios:**
- Verificar navbar para incluir enlace a клубы

---

## Archivos a Editar

| Archivo | Cambio |
|---------|--------|
| `SistemaRegistro/users/views.py` | Actualizar `dashboard_institucional()` |
| `SistemaRegistro/templates/users/dashboard_institucional.html` | Agregar KPIs de clubes |

---

## Dependencias
- No se necesitan nuevas dependencias
- Los modelos Club y MembresiaClu ya existen
- Las URLs ya están configuradas en registry/urls.py

---

## Pruebas Post-Implementación
1. Login como usuario institucional
2. Verificar que aparecen las tarjetas de clubes
3. Verificar que los enlaces funcionan
4. Verificar que no rompe otros dashboards

