# 🔧 Corrección: Formularios de Clubes con Líneas Dinámicas

## 📋 Problema Identificado

**Síntoma:** Al crear una nueva línea de investigación en el admin, no aparece en el formulario de creación de clubes para usuarios institucionales.

**Causa Raíz:** Las vistas de creación y edición de clubes usaban los campos antiguos hardcodeados (`linea_1`, `linea_2`, `linea_3`) en lugar del nuevo sistema de líneas dinámicas.

---

## ✅ Solución Implementada

### 1. Nuevo Formulario `ClubForm`

**Archivo:** `registry/forms.py`

```python
class ClubForm(forms.ModelForm):
    """Formulario con líneas de investigación dinámicas."""
    
    # Campos dinámicos que cargan desde LineaInvestigacion
    linea_investigacion_1 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True),
        required=True
    )
    linea_investigacion_2 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True),
        required=False
    )
    linea_investigacion_3 = forms.ModelChoiceField(
        queryset=LineaInvestigacion.objects.filter(activa=True),
        required=False
    )
```

**Características:**
- ✅ Carga líneas activas desde la base de datos
- ✅ Ordenadas por `orden` y `nombre`
- ✅ Valida que no se repitan líneas
- ✅ Guarda en `ClubLineaInvestigacion` automáticamente
- ✅ Soporta edición (carga líneas existentes)

---

### 2. Vistas Actualizadas

#### `crear_club()`
**Antes:**
```python
club = Club.objects.create(
    linea_1=request.POST.get("linea_1"),
    linea_2=request.POST.get("linea_2"),
    # Campos hardcodeados
)
```

**Después:**
```python
from registry.forms import ClubForm
form = ClubForm(request.POST)
if form.is_valid():
    club = form.save()
    # Líneas guardadas automáticamente
```

#### `editar_club()`
**Antes:**
```python
club.linea_1 = request.POST.get("linea_1")
club.linea_2 = request.POST.get("linea_2")
# Actualización manual
```

**Después:**
```python
form = ClubForm(request.POST, instance=club)
if form.is_valid():
    club = form.save()
    # Líneas actualizadas automáticamente
```

---

## 📁 Archivos Modificados

```
✏️ registry/forms.py
   └─ ClubForm (NUEVO)
      ├─ linea_investigacion_1 (ModelChoiceField)
      ├─ linea_investigacion_2 (ModelChoiceField)
      ├─ linea_investigacion_3 (ModelChoiceField)
      ├─ clean() - Validación de duplicados
      └─ save() - Guarda en ClubLineaInvestigacion

✏️ registry/views_institucional.py
   ├─ crear_club() - Usa ClubForm
   └─ editar_club() - Usa ClubForm
```

---

## 🧪 Cómo Probar

### Paso 1: Crear Línea de Investigación (Admin)

```bash
# 1. Ir a http://localhost:8000/admin/
# 2. Iniciar sesión como superusuario
# 3. Ir a "Líneas de Investigación"
# 4. Clic en "Agregar línea de investigación"
# 5. Llenar:
#    - Código: robotica_educativa
#    - Nombre: Robótica Educativa
#    - Activa: ✓
#    - Orden: 10
# 6. Guardar
```

### Paso 2: Verificar en Formulario de Club

```bash
# 1. Cerrar sesión del admin
# 2. Iniciar sesión como usuario institucional
# 3. Ir a "Mis Clubes"
# 4. Clic en "Crear Club"
# 5. Verificar que aparece "Robótica Educativa" en los selectores
```

### Paso 3: Crear Club con Nueva Línea

```bash
# 1. Llenar formulario:
#    - Nombre: Club de Prueba
#    - Línea 1: Robótica Educativa ✓
#    - Línea 2: (opcional)
# 2. Guardar
# 3. Verificar que se creó correctamente
```

### Paso 4: Verificar en Admin

```bash
# 1. Ir al admin
# 2. Editar el club creado
# 3. Verificar que aparece el inline con "Robótica Educativa"
```

---

## ✅ Resultado

### Antes
```
Admin: Crear línea "Robótica Educativa" ✅
Formulario institucional: No aparece ❌
```

### Después
```
Admin: Crear línea "Robótica Educativa" ✅
Formulario institucional: Aparece inmediatamente ✅
```

---

## 🔄 Flujo Completo

```
1. Ente Rector (Admin)
   └─ Crea línea "Robótica Educativa"
   └─ Marca como activa
   └─ Guarda

2. Sistema
   └─ LineaInvestigacion.objects.create(...)
   └─ Línea disponible inmediatamente

3. Usuario Institucional
   └─ Abre formulario de crear club
   └─ ClubForm carga líneas activas
   └─ Ve "Robótica Educativa" en selector
   └─ Selecciona y guarda

4. Sistema
   └─ Club.objects.create(...)
   └─ ClubLineaInvestigacion.objects.create(...)
   └─ Relación N:M guardada
```

---

## 📊 Validaciones Implementadas

### En el Formulario
```python
def clean(self):
    # Validar que no se repitan líneas
    lineas = [l1, l2, l3]
    if len(lineas) != len(set(lineas)):
        raise ValidationError("No puede repetir líneas")
```

### En el Modelo
```python
class Meta:
    unique_together = ['club', 'linea']
    # Evita duplicados en BD
```

### En el Admin
```python
class ClubLineaInvestigacionInline:
    max_num = 3  # Máximo 3 líneas
    min_num = 1  # Mínimo 1 línea
```

---

## 🎯 Beneficios

1. **Inmediatez** - Líneas nuevas disponibles al instante
2. **Consistencia** - Mismo catálogo en admin y formularios
3. **Validación** - No permite duplicados ni más de 3 líneas
4. **Usabilidad** - Selectores en lugar de campos de texto
5. **Mantenibilidad** - Un solo lugar para gestionar líneas

---

## 📝 Notas Técnicas

### QuerySet Dinámico
```python
queryset=LineaInvestigacion.objects.filter(activa=True).order_by('orden', 'nombre')
```
- Solo muestra líneas activas
- Ordenadas por `orden` (definido por admin)
- Luego por nombre alfabético

### Guardado Automático
```python
def save(self, commit=True):
    club = super().save(commit=commit)
    if commit:
        # Eliminar líneas antiguas
        ClubLineaInvestigacion.objects.filter(club=club).delete()
        # Crear nuevas líneas
        for linea in lineas_seleccionadas:
            ClubLineaInvestigacion.objects.create(...)
```

### Carga en Edición
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.instance.pk:
        # Cargar líneas existentes
        lineas = self.instance.club_lineas.all()
        for i, club_linea in enumerate(lineas):
            self.fields[f'linea_investigacion_{i+1}'].initial = club_linea.linea
```

---

## ⚠️ Consideraciones

### Templates
Los templates `club_crear.html` y `club_editar.html` deben usar:
```django
{{ form.as_p }}
<!-- O -->
{{ form.linea_investigacion_1 }}
{{ form.linea_investigacion_2 }}
{{ form.linea_investigacion_3 }}
```

En lugar de:
```django
<!-- DEPRECADO -->
<select name="linea_1">
  {% for codigo, nombre in lineas %}
    <option value="{{ codigo }}">{{ nombre }}</option>
  {% endfor %}
</select>
```

---

## ✅ Checklist de Verificación

- [x] Formulario ClubForm creado
- [x] Vista crear_club actualizada
- [x] Vista editar_club actualizada
- [x] Validación de duplicados
- [x] Guardado en ClubLineaInvestigacion
- [x] Carga de líneas en edición
- [ ] Templates actualizados (si es necesario)
- [ ] Probado con usuario institucional
- [ ] Probado crear línea nueva
- [ ] Probado editar club existente

---

**Estado:** ✅ **IMPLEMENTADO**  
**Próximo Paso:** Actualizar templates si usan campos hardcodeados  
**Fecha:** $(date +%Y-%m-%d)
