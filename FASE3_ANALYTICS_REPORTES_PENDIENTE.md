# 📊 Fase 3: Analytics y Reportes de Clubes (PENDIENTE)

## 🎯 Objetivo

Implementar sistema de análisis y reportes para obtener insights sobre el proceso de revisión de clubes, identificar patrones de rechazo y medir la efectividad del sistema de reenvíos.

---

## 📋 Estado: ⏳ PENDIENTE DE IMPLEMENTACIÓN

**Prioridad**: Media  
**Complejidad**: Media-Alta  
**Tiempo Estimado**: 2-3 días  
**Dependencias**: Fase 1 y 2 completadas ✅

---

## 🎯 Funcionalidades a Implementar

### 1. Dashboard de Estadísticas de Reenvíos

**Objetivo**: Panel visual con métricas clave del proceso de revisión.

**Métricas a Mostrar**:
- Total de clubes rechazados
- Total de reenvíos realizados
- Tasa de aprobación por intento (1er, 2do, 3er intento)
- Clubes que alcanzaron límite de reenvíos
- Tiempo promedio entre rechazo y reenvío
- Instituciones con más reenvíos

**Ubicación**: `/admin/clubes/analytics/`

**Mockup**:
```
┌─────────────────────────────────────────────────────┐
│  📊 Analytics de Clubes                             │
├─────────────────────────────────────────────────────┤
│                                                      │
│  KPIs Principales                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 45       │ │ 78%      │ │ 12       │           │
│  │ Rechazos │ │ Aprobados│ │ Límite   │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│                                                      │
│  Tasa de Aprobación por Intento                    │
│  ┌────────────────────────────────────────┐        │
│  │ 1er Intento: ████████░░ 45%            │        │
│  │ 2do Intento: ██████████████ 72%        │        │
│  │ 3er Intento: ████████████████ 85%      │        │
│  └────────────────────────────────────────┘        │
│                                                      │
│  Top 5 Instituciones con Más Reenvíos             │
│  1. Instituto Tecnológico - 8 reenvíos            │
│  2. Universidad Central - 6 reenvíos              │
│  ...                                               │
└─────────────────────────────────────────────────────┘
```

---

### 2. Análisis de Motivos de Rechazo

**Objetivo**: Categorizar y analizar los motivos más comunes de rechazo.

**Funcionalidades**:
- Categorización automática de rechazos
- Ranking de motivos más frecuentes
- Tendencias de mejora por institución
- Sugerencias de capacitación

**Categorías Propuestas**:
```python
CATEGORIAS_RECHAZO = [
    'documentacion_incompleta',
    'lineas_investigacion_vagas',
    'descripcion_insuficiente',
    'objetivos_poco_claros',
    'recursos_inadecuados',
    'otro'
]
```

**Implementación Sugerida**:
```python
# registry/models.py
class HistorialClub(models.Model):
    # ... campos existentes ...
    categoria_rechazo = models.CharField(
        max_length=50,
        choices=CATEGORIAS_RECHAZO,
        blank=True,
        null=True
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['categoria_rechazo']),
        ]

# registry/views_admin.py
def analytics_motivos_rechazo(request):
    """Análisis de motivos de rechazo."""
    rechazos = HistorialClub.objects.filter(
        estado_nuevo='rechazado'
    ).values('categoria_rechazo').annotate(
        total=Count('id')
    ).order_by('-total')
    
    context = {
        'rechazos_por_categoria': rechazos,
        'total_rechazos': sum(r['total'] for r in rechazos)
    }
    return render(request, 'registry/analytics_rechazos.html', context)
```

---

### 3. Reportes Exportables

**Objetivo**: Generar reportes en PDF/Excel para análisis offline.

**Tipos de Reportes**:

1. **Reporte de Clubes Rechazados**
   - Lista de clubes rechazados en período
   - Motivos de rechazo
   - Estado actual
   - Número de reenvíos

2. **Reporte de Instituciones**
   - Clubes por institución
   - Tasa de aprobación
   - Tiempo promedio de corrección
   - Recomendaciones

3. **Reporte de Tendencias**
   - Evolución mensual de aprobaciones
   - Mejora en tasa de aprobación
   - Categorías de rechazo por mes

**Implementación Sugerida**:
```python
# registry/views_admin.py
from django.http import HttpResponse
from reportlab.pdfgen import canvas
import openpyxl

def exportar_reporte_rechazos(request, formato='pdf'):
    """Exporta reporte de clubes rechazados."""
    clubes = Club.objects.filter(status='rechazado')
    
    if formato == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="rechazos.pdf"'
        
        p = canvas.Canvas(response)
        # ... generar PDF ...
        p.save()
        return response
    
    elif formato == 'excel':
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="rechazos.xlsx"'
        
        wb = openpyxl.Workbook()
        ws = wb.active
        # ... generar Excel ...
        wb.save(response)
        return response
```

---

### 4. Tiempo de Corrección

**Objetivo**: Medir eficiencia de instituciones en corregir clubes rechazados.

**Métricas**:
- Tiempo promedio entre rechazo y reenvío
- Instituciones más rápidas
- Instituciones más lentas
- Alertas para clubes sin reenvío > 30 días

**Implementación Sugerida**:
```python
# registry/models.py
class Club(models.Model):
    # ... campos existentes ...
    
    def calcular_tiempo_correccion(self):
        """Calcula tiempo promedio de corrección en días."""
        rechazos = self.historial.filter(estado_nuevo='rechazado')
        reenvios = self.historial.filter(
            estado_anterior='rechazado',
            estado_nuevo='pendiente'
        )
        
        tiempos = []
        for rechazo in rechazos:
            reenvio = reenvios.filter(fecha__gt=rechazo.fecha).first()
            if reenvio:
                delta = (reenvio.fecha - rechazo.fecha).days
                tiempos.append(delta)
        
        return sum(tiempos) / len(tiempos) if tiempos else None

# registry/views_admin.py
def analytics_tiempo_correccion(request):
    """Análisis de tiempos de corrección."""
    instituciones = Institucion.objects.annotate(
        tiempo_promedio=Avg(
            F('clubes__historial__fecha') - F('clubes__historial__fecha')
        )
    ).order_by('tiempo_promedio')
    
    context = {'instituciones': instituciones}
    return render(request, 'registry/analytics_tiempos.html', context)
```

---

## 📁 Archivos a Crear/Modificar

### Nuevos Archivos

```
registry/
├── views_analytics.py          # Vistas de analytics (nuevo)
├── templates/registry/
│   ├── analytics_dashboard.html    # Dashboard principal
│   ├── analytics_rechazos.html     # Análisis de rechazos
│   ├── analytics_tiempos.html      # Análisis de tiempos
│   └── reportes/
│       ├── reporte_rechazos.html   # Template PDF rechazos
│       └── reporte_instituciones.html  # Template PDF instituciones
└── static/registry/
    └── js/
        └── analytics_charts.js     # Gráficos con Chart.js
```

### Archivos a Modificar

```
registry/
├── models.py                   # Agregar campo categoria_rechazo
├── urls.py                     # Rutas de analytics
└── templates/users/
    └── base_dashboard.html     # Agregar menú Analytics
```

---

## 🛠 Dependencias Técnicas

### Librerías Necesarias

```bash
# requirements.txt
reportlab==4.0.7        # Generación de PDFs
openpyxl==3.1.2         # Generación de Excel
pandas==2.1.4           # Análisis de datos
matplotlib==3.8.2       # Gráficos (opcional)
```

### Frontend

```html
<!-- Chart.js para gráficos -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
```

---

## 🎨 Diseño de UI

### Menú de Navegación

```django
<!-- users/base_dashboard.html -->
{% if user.is_staff %}
<li class="nav-item">
    <a class="nav-link" href="{% url 'analytics_dashboard' %}">
        <i class="bi bi-graph-up"></i> Analytics
    </a>
    <ul class="submenu">
        <li><a href="{% url 'analytics_rechazos' %}">Motivos de Rechazo</a></li>
        <li><a href="{% url 'analytics_tiempos' %}">Tiempos de Corrección</a></li>
        <li><a href="{% url 'analytics_instituciones' %}">Por Institución</a></li>
        <li><a href="{% url 'reportes_exportar' %}">Exportar Reportes</a></li>
    </ul>
</li>
{% endif %}
```

---

## 📊 Queries SQL Optimizadas

```python
# Tasa de aprobación por intento
SELECT 
    intento,
    COUNT(*) as total,
    SUM(CASE WHEN aprobado = 1 THEN 1 ELSE 0 END) as aprobados,
    ROUND(SUM(CASE WHEN aprobado = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tasa
FROM (
    SELECT 
        club_id,
        ROW_NUMBER() OVER (PARTITION BY club_id ORDER BY fecha) as intento,
        CASE WHEN estado_nuevo = 'aprobado' THEN 1 ELSE 0 END as aprobado
    FROM registry_historialclub
    WHERE estado_anterior = 'rechazado' AND estado_nuevo IN ('pendiente', 'aprobado')
) subquery
GROUP BY intento;

# Top instituciones con más reenvíos
SELECT 
    i.nombre,
    COUNT(h.id) as total_reenvios,
    AVG(JULIANDAY(h2.fecha) - JULIANDAY(h.fecha)) as dias_promedio
FROM registry_institucion i
JOIN registry_club c ON c.institucion_creadora_id = i.id
JOIN registry_historialclub h ON h.club_id = c.id AND h.estado_nuevo = 'rechazado'
LEFT JOIN registry_historialclub h2 ON h2.club_id = c.id 
    AND h2.estado_anterior = 'rechazado' 
    AND h2.fecha > h.fecha
GROUP BY i.id
ORDER BY total_reenvios DESC
LIMIT 10;
```

---

## ✅ Checklist de Implementación

### Backend
- [ ] Agregar campo `categoria_rechazo` a modelo `HistorialClub`
- [ ] Crear migración para nuevo campo
- [ ] Implementar método `calcular_tiempo_correccion()` en modelo `Club`
- [ ] Crear archivo `views_analytics.py` con vistas de analytics
- [ ] Implementar función de exportación PDF
- [ ] Implementar función de exportación Excel
- [ ] Agregar rutas en `urls.py`
- [ ] Crear índices de base de datos para optimización

### Frontend
- [ ] Crear template `analytics_dashboard.html`
- [ ] Crear template `analytics_rechazos.html`
- [ ] Crear template `analytics_tiempos.html`
- [ ] Implementar gráficos con Chart.js
- [ ] Agregar menú "Analytics" en sidebar
- [ ] Diseño responsive para móviles

### Testing
- [ ] Test de cálculo de métricas
- [ ] Test de exportación PDF
- [ ] Test de exportación Excel
- [ ] Test de queries optimizadas
- [ ] Test de permisos (solo staff)

### Documentación
- [ ] Documentar nuevas vistas
- [ ] Documentar queries SQL
- [ ] Guía de uso para administradores
- [ ] Actualizar README.md

---

## 🎯 Beneficios Esperados

1. **Visibilidad**: Métricas claras del proceso de revisión
2. **Toma de Decisiones**: Datos para mejorar el proceso
3. **Identificación de Patrones**: Motivos comunes de rechazo
4. **Capacitación Dirigida**: Enfocar esfuerzos en áreas problemáticas
5. **Transparencia**: Reportes para stakeholders
6. **Mejora Continua**: Medir efectividad de cambios

---

## 📈 Métricas de Éxito

- ✅ Dashboard carga en < 2 segundos
- ✅ Reportes PDF generados en < 5 segundos
- ✅ 100% de rechazos categorizados
- ✅ Queries optimizadas con índices
- ✅ Interfaz responsive en móviles
- ✅ Exportación Excel funcional

---

**Prioridad**: Media  
**Estado**: ⏳ Pendiente  
**Próximo Paso**: Revisar con equipo y priorizar implementación
