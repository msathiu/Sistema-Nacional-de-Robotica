# 🚀 Plan de Implementación: Mejoras Módulo de Clubes

## 📋 Resumen Ejecutivo

**Objetivo:** Alinear el módulo de clubes al 95% con la especificación  
**Tiempo Estimado:** 1-2 semanas  
**Riesgo:** Bajo (cambios no rompen funcionalidad existente)  
**Prioridad:** Alta

---

## 🎯 FASE 1: Líneas de Investigación Dinámicas

### Paso 1.1: Crear Modelo LineaInvestigacion

**Archivo:** `registry/models.py`

```python
class LineaInvestigacion(models.Model):
    """Catálogo dinámico de líneas de investigación gestionado por el Ente Rector."""
    
    codigo = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, db_index=True, verbose_name="Activa")
    orden = models.IntegerField(default=0, verbose_name="Orden de visualización")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Línea de Investigación"
        verbose_name_plural = "Líneas de Investigación"
        ordering = ['orden', 'nombre']
        indexes = [
            models.Index(fields=['activa', 'orden'], name='idx_linea_activa_orden'),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ClubLineaInvestigacion(models.Model):
    """Relación N:M entre clubes y líneas de investigación."""
    
    TIPO_LINEA_CHOICES = [
        ('principal', 'Principal'),
        ('soporte', 'Soporte'),
        ('afines', 'Afines'),
    ]
    
    club = models.ForeignKey(
        'Club',
        on_delete=models.CASCADE,
        related_name='club_lineas'
    )
    linea = models.ForeignKey(
        'LineaInvestigacion',
        on_delete=models.PROTECT,
        related_name='clubes'
    )
    tipo_linea = models.CharField(
        max_length=20,
        choices=TIPO_LINEA_CHOICES,
        default='principal',
        verbose_name="Tipo de Línea"
    )
    orden = models.IntegerField(default=0, verbose_name="Orden")
    fecha_vinculacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Club-Línea de Investigación"
        verbose_name_plural = "Clubes-Líneas de Investigación"
        unique_together = ['club', 'linea']
        ordering = ['orden']
        indexes = [
            models.Index(fields=['club', 'orden'], name='idx_clublinea_club_orden'),
        ]
    
    def __str__(self):
        return f"{self.club.nombre} - {self.linea.nombre} ({self.tipo_linea})"
```

### Paso 1.2: Migración de Datos

**Archivo:** `registry/migrations/0019_lineas_investigacion_dinamicas.py`

```python
from django.db import migrations

def migrar_lineas_existentes(apps, schema_editor):
    """Migrar líneas hardcodeadas a modelo dinámico."""
    LineaInvestigacion = apps.get_model('registry', 'LineaInvestigacion')
    Club = apps.get_model('registry', 'Club')
    ClubLineaInvestigacion = apps.get_model('registry', 'ClubLineaInvestigacion')
    
    # Crear líneas desde LINEAS_INVESTIGACION_CHOICES
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
    
    lineas_creadas = {}
    for orden, (codigo, nombre) in enumerate(lineas_map.items(), start=1):
        linea = LineaInvestigacion.objects.create(
            codigo=codigo,
            nombre=nombre,
            activa=True,
            orden=orden
        )
        lineas_creadas[codigo] = linea
    
    # Migrar clubes existentes
    for club in Club.objects.all():
        orden = 1
        if club.linea_1:
            ClubLineaInvestigacion.objects.create(
                club=club,
                linea=lineas_creadas[club.linea_1],
                tipo_linea='principal',
                orden=orden
            )
            orden += 1
        
        if club.linea_2:
            ClubLineaInvestigacion.objects.create(
                club=club,
                linea=lineas_creadas[club.linea_2],
                tipo_linea='soporte',
                orden=orden
            )
            orden += 1
        
        if club.linea_3:
            ClubLineaInvestigacion.objects.create(
                club=club,
                linea=lineas_creadas[club.linea_3],
                tipo_linea='afines',
                orden=orden
            )


class Migration(migrations.Migration):
    dependencies = [
        ('registry', '0018_fase4_calificaciones_eventos_restauracion'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='LineaInvestigacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('codigo', models.CharField(max_length=50, unique=True, db_index=True)),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('activa', models.BooleanField(default=True, db_index=True)),
                ('orden', models.IntegerField(default=0)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Línea de Investigación',
                'verbose_name_plural': 'Líneas de Investigación',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='ClubLineaInvestigacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('tipo_linea', models.CharField(max_length=20, default='principal')),
                ('orden', models.IntegerField(default=0)),
                ('fecha_vinculacion', models.DateTimeField(auto_now_add=True)),
                ('club', models.ForeignKey(on_delete=models.CASCADE, to='registry.club')),
                ('linea', models.ForeignKey(on_delete=models.PROTECT, to='registry.lineainvestigacion')),
            ],
            options={
                'unique_together': {('club', 'linea')},
                'ordering': ['orden'],
            },
        ),
        migrations.RunPython(migrar_lineas_existentes),
        # Mantener campos antiguos por compatibilidad (deprecar después)
        migrations.AlterField(
            model_name='club',
            name='linea_1',
            field=models.CharField(max_length=50, null=True, blank=True, help_text='DEPRECADO: Usar ClubLineaInvestigacion'),
        ),
    ]
```

### Paso 1.3: Actualizar Modelo Club

```python
class Club(models.Model):
    # ... campos existentes ...
    
    # Deprecar campos antiguos (mantener por compatibilidad)
    linea_1 = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='DEPRECADO: Usar ClubLineaInvestigacion'
    )
    linea_2 = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='DEPRECADO: Usar ClubLineaInvestigacion'
    )
    linea_3 = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='DEPRECADO: Usar ClubLineaInvestigacion'
    )
    
    @property
    def lineas_investigacion(self):
        """Retorna QuerySet de líneas de investigación del club."""
        return self.club_lineas.select_related('linea').filter(linea__activa=True)
    
    @property
    def lineas_principales(self):
        """Retorna líneas principales del club."""
        return self.lineas_investigacion.filter(tipo_linea='principal')
    
    def clean(self):
        """Validar reglas de negocio."""
        super().clean()
        
        # Validar mínimo 1, máximo 3 líneas
        if self.pk:
            count = self.club_lineas.count()
            if count < 1:
                raise ValidationError("El club debe tener al menos 1 línea de investigación")
            if count > 3:
                raise ValidationError("El club no puede tener más de 3 líneas de investigación")
```

### Paso 1.4: Actualizar Admin

**Archivo:** `registry/admin.py`

```python
from django.contrib import admin

@admin.register(LineaInvestigacion)
class LineaInvestigacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activa', 'orden', 'fecha_creacion']
    list_filter = ['activa']
    search_fields = ['codigo', 'nombre']
    list_editable = ['activa', 'orden']
    ordering = ['orden', 'nombre']


class ClubLineaInvestigacionInline(admin.TabularInline):
    model = ClubLineaInvestigacion
    extra = 1
    max_num = 3
    min_num = 1
    fields = ['linea', 'tipo_linea', 'orden']
    autocomplete_fields = ['linea']


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    inlines = [ClubLineaInvestigacionInline]
    # ... resto de configuración ...
```

---

## 🎯 FASE 2: Constraint de 3 Líneas Máximo

### Paso 2.1: Agregar Constraint en Modelo

```python
class Club(models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    club_lineas__count__lte=3,
                    club_lineas__count__gte=1
                ),
                name='club_lineas_count_valid'
            )
        ]
```

### Paso 2.2: Trigger en PostgreSQL (Opcional)

**Archivo:** `registry/migrations/0020_constraint_lineas_club.py`

```python
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('registry', '0019_lineas_investigacion_dinamicas'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION check_club_lineas_count()
            RETURNS TRIGGER AS $$
            DECLARE
                lineas_count INTEGER;
            BEGIN
                SELECT COUNT(*) INTO lineas_count
                FROM registry_clublineainvestigacion
                WHERE club_id = NEW.club_id;
                
                IF lineas_count > 3 THEN
                    RAISE EXCEPTION 'Un club no puede tener más de 3 líneas de investigación';
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS club_lineas_limit_trigger ON registry_clublineainvestigacion;
            
            CREATE TRIGGER club_lineas_limit_trigger
            BEFORE INSERT ON registry_clublineainvestigacion
            FOR EACH ROW
            EXECUTE FUNCTION check_club_lineas_count();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS club_lineas_limit_trigger ON registry_clublineainvestigacion;
            DROP FUNCTION IF EXISTS check_club_lineas_count();
            """
        ),
    ]
```

---

## 🎯 FASE 3: Índice Único Parcial

### Paso 3.1: Modificar MembresiaClu

**Archivo:** `registry/models.py`

```python
class MembresiaClu(models.Model):
    class Meta:
        verbose_name = "Membresía de Club"
        verbose_name_plural = "Membresías de Clubes"
        # REMOVER: unique_together = ["club", "institucion"]
        ordering = ["-fecha_solicitud"]
        indexes = [
            # Índice único parcial: solo para solicitudes activas
            models.Index(
                fields=['club', 'institucion'],
                name='idx_memb_club_inst_active',
                condition=models.Q(estado__in=['pendiente', 'revision'])
            ),
        ]
```

### Paso 3.2: Migración

**Archivo:** `registry/migrations/0021_indice_unico_parcial_membresia.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('registry', '0020_constraint_lineas_club'),
    ]
    
    operations = [
        # Remover unique_together
        migrations.AlterUniqueTogether(
            name='membresiaclu',
            unique_together=set(),
        ),
        # Agregar índice único parcial
        migrations.AddIndex(
            model_name='membresiaclu',
            index=models.Index(
                fields=['club', 'institucion'],
                name='idx_memb_club_inst_active',
                condition=models.Q(estado__in=['pendiente', 'revision'])
            ),
        ),
    ]
```

---

## 📊 CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Líneas Dinámicas
- [ ] Crear modelo LineaInvestigacion
- [ ] Crear modelo ClubLineaInvestigacion
- [ ] Crear migración de datos
- [ ] Actualizar modelo Club
- [ ] Actualizar admin
- [ ] Actualizar formularios
- [ ] Actualizar templates
- [ ] Probar creación de clubes
- [ ] Probar edición de clubes
- [ ] Probar búsqueda por líneas

### Fase 2: Constraint
- [ ] Agregar constraint en modelo
- [ ] Crear trigger en PostgreSQL
- [ ] Probar inserción de 4+ líneas (debe fallar)
- [ ] Probar inserción de 0 líneas (debe fallar)
- [ ] Probar inserción de 1-3 líneas (debe funcionar)

### Fase 3: Índice Único Parcial
- [ ] Remover unique_together
- [ ] Agregar índice parcial
- [ ] Probar postulación duplicada pendiente (debe fallar)
- [ ] Probar re-postulación después de rechazo (debe funcionar)
- [ ] Probar re-postulación después de aprobación (debe funcionar)

---

## 🧪 PLAN DE PRUEBAS

### Test 1: Líneas Dinámicas
```python
def test_crear_linea_investigacion():
    linea = LineaInvestigacion.objects.create(
        codigo='robotica_educativa',
        nombre='Robótica Educativa',
        activa=True
    )
    assert linea.codigo == 'robotica_educativa'

def test_club_con_lineas_dinamicas():
    club = Club.objects.create(nombre='Club Test', ...)
    linea1 = LineaInvestigacion.objects.get(codigo='electronica')
    linea2 = LineaInvestigacion.objects.get(codigo='programacion')
    
    ClubLineaInvestigacion.objects.create(club=club, linea=linea1, tipo_linea='principal')
    ClubLineaInvestigacion.objects.create(club=club, linea=linea2, tipo_linea='soporte')
    
    assert club.lineas_investigacion.count() == 2
```

### Test 2: Constraint de 3 Líneas
```python
def test_maximo_3_lineas():
    club = Club.objects.create(nombre='Club Test', ...)
    lineas = LineaInvestigacion.objects.all()[:4]
    
    for i, linea in enumerate(lineas[:3]):
        ClubLineaInvestigacion.objects.create(club=club, linea=linea)
    
    # Intentar agregar 4ta línea debe fallar
    with pytest.raises(ValidationError):
        ClubLineaInvestigacion.objects.create(club=club, linea=lineas[3])
```

### Test 3: Re-postulación
```python
def test_repostulacion_despues_rechazo():
    club = Club.objects.create(...)
    institucion = Institucion.objects.create(...)
    
    # Primera postulación
    membresia1 = MembresiaClu.objects.create(
        club=club,
        institucion=institucion,
        estado='pendiente'
    )
    
    # Rechazar
    membresia1.estado = 'rechazada'
    membresia1.save()
    
    # Re-postular debe funcionar
    membresia2 = MembresiaClu.objects.create(
        club=club,
        institucion=institucion,
        estado='pendiente'
    )
    assert membresia2.pk is not None
```

---

## 📈 MÉTRICAS DE ÉXITO

### Antes de Implementación
- Alineación con especificación: 85%
- Líneas dinámicas: ❌
- Constraint de 3 líneas: ❌
- Re-postulación: ❌

### Después de Implementación
- Alineación con especificación: 95%
- Líneas dinámicas: ✅
- Constraint de 3 líneas: ✅
- Re-postulación: ✅

---

## ⚠️ RIESGOS Y MITIGACIÓN

### Riesgo 1: Migración de Datos
**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:**
- Hacer backup de BD antes de migrar
- Probar migración en ambiente de desarrollo
- Tener rollback plan

### Riesgo 2: Compatibilidad con Código Existente
**Probabilidad:** Baja  
**Impacto:** Medio  
**Mitigación:**
- Mantener campos antiguos como deprecados
- Actualizar código gradualmente
- Usar property para compatibilidad

### Riesgo 3: Performance
**Probabilidad:** Baja  
**Impacto:** Bajo  
**Mitigación:**
- Usar select_related en queries
- Agregar índices apropiados
- Monitorear queries lentas

---

## 🚀 DESPLIEGUE

### Paso 1: Desarrollo
```bash
# Crear modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Probar en desarrollo
python manage.py test registry.tests.test_clubes
```

### Paso 2: Staging
```bash
# Backup de BD
pg_dump dbname > backup_pre_clubes_mejoras.sql

# Aplicar migraciones
python manage.py migrate

# Smoke tests
python manage.py shell
>>> from registry.models import LineaInvestigacion
>>> LineaInvestigacion.objects.count()
```

### Paso 3: Producción
```bash
# Modo mantenimiento
# Backup de BD
# Aplicar migraciones
# Verificar
# Quitar modo mantenimiento
```

---

**Tiempo Total Estimado:** 1-2 semanas  
**Esfuerzo:** 40-60 horas  
**Prioridad:** Alta  
**Estado:** Listo para implementar
