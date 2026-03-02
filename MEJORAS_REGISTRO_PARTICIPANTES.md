# Mejoras en el Registro de Participantes

## 📋 Resumen de Implementación

Se han implementado mejoras significativas en el formulario de registro de participantes (`register.html`) para cumplir con los requisitos de validación y experiencia de usuario solicitados.

---

## ✅ Funcionalidades Implementadas

### 1. **Separación de Cédulas (Personal y Escolar)**

#### Antes:
- Un solo campo de cédula que causaba confusión

#### Ahora:
- **Cédula Personal**: Campo independiente para mayores de 10 años
- **Cédula Escolar**: Campo independiente que aparece solo para menores o iguales a 10 años
- Validación automática según la edad del participante

**Lógica implementada:**
```javascript
// Si edad <= 10 años
- Mostrar campo de cédula escolar (requerido)
- Cédula personal opcional

// Si edad > 10 años
- Mostrar campo de cédula personal (requerido)
- Ocultar campo de cédula escolar
```

---

### 2. **Validación Atómica de Duplicados**

Se implementó un sistema de verificación en tiempo real que busca participantes existentes por:

1. **Cédula Personal** (formato: V-12345678 o E-12345678)
2. **Cédula Escolar** (si está presente)
3. **Combinación de**: Nombres + Apellidos + Fecha de Nacimiento

**Endpoint creado:**
```
POST /verificar-participante/
```

**Flujo de validación:**
```
Usuario completa formulario
    ↓
Presiona "Guardar"
    ↓
JavaScript intercepta el submit
    ↓
Envía datos a /verificar-participante/
    ↓
¿Existe duplicado?
    ├─ SÍ → Muestra modal con datos existentes
    │         ├─ "Es el mismo" → Redirige a editar
    │         └─ "No es el mismo" → Continúa registro
    └─ NO → Procede con el registro normal
```

---

### 3. **Modal de Registro Duplicado**

Se agregó un modal Bootstrap que se muestra cuando se detecta un posible duplicado:

**Características:**
- Muestra los datos del participante existente
- Dos opciones claras:
  - **"Sí, ir a editar"**: Redirige a la vista de edición del participante existente
  - **"No, continuar registro"**: Cierra el modal y permite continuar con el nuevo registro

**Datos mostrados en el modal:**
- Nombres completos
- Apellidos
- Fecha de nacimiento
- Cédula (personal o escolar)

---

### 4. **Representante Legal (Mejora Existente)**

La funcionalidad de mostrar el representante legal para menores de 18 años ya existía y se mantiene:

```javascript
if (edad >= 3 && edad < 18) {
    // Mostrar sección de representante
    // Hacer campos obligatorios
}
```

---

## 🔧 Archivos Modificados

### 1. **Template: `register.html`**
```html
<!-- Campos separados de cédula -->
<div id="cedula_personal_container">
    <label>Cédula Personal</label>
    <input type="text" name="cedula_personal" id="id_cedula_personal">
</div>

<div id="cedula_escolar_container" style="display: none;">
    <label>Cédula Escolar</label>
    <input type="text" name="cedula_escolar" id="id_cedula_escolar">
</div>

<!-- Modal de duplicados -->
<div class="modal" id="modalDuplicado">
    <!-- Contenido del modal -->
</div>
```

**JavaScript agregado:**
- Lógica de mostrar/ocultar cédula escolar según edad
- Validación AJAX antes de submit
- Manejo del modal de duplicados

---

### 2. **Vista: `views.py`**

#### Nueva vista: `verificar_participante_duplicado`
```python
@login_required
@require_http_methods(["POST", "GET"])
def verificar_participante_duplicado(request):
    """
    Verifica si existe un participante con datos similares.
    Busca por: cédula personal, cédula escolar, o 
    combinación de nombres+apellidos+fecha_nacimiento
    """
    # Lógica de búsqueda
    # Retorna JSON con resultado
```

#### Modificación: `crear_participante`
```python
# Manejo de cédulas separadas
cedula_personal = request.POST.get('cedula_personal', '').strip()
cedula_escolar = request.POST.get('cedula_escolar', '').strip()

# Determinar cédula principal
if cedula_personal:
    cedula_completa = f"{nacionalidad}-{cedula_personal}"
elif cedula_escolar:
    cedula_completa = f"E-{cedula_escolar}"

# Asignar ambas cédulas al modelo
participante.cedula = cedula_completa
if cedula_escolar:
    participante.cedula_escolar = cedula_escolar
```

---

### 3. **Formulario: `forms.py`**

```python
class ParticipanteRegistrationForm(forms.ModelForm):
    # Nuevos campos
    cedula_personal = forms.CharField(required=False, ...)
    cedula_escolar_input = forms.CharField(required=False, ...)
    
    def clean(self):
        # Validar que tenga al menos una cédula
        if not cedula_personal and not cedula_escolar:
            raise ValidationError("Debe proporcionar al menos una cédula")
        
        # Validar cédula escolar para <= 10 años
        if edad <= 10 and not cedula_escolar:
            raise ValidationError("Cédula escolar obligatoria para menores de 10 años")
        
        # Validar cédula personal para > 10 años
        if edad > 10 and not cedula_personal:
            raise ValidationError("Cédula personal obligatoria para mayores de 10 años")
```

---

### 4. **URLs: `urls.py`**

```python
urlpatterns = [
    # ... otras URLs
    path(
        "verificar-participante/",
        views.verificar_participante_duplicado,
        name="verificar_participante_duplicado",
    ),
    # ...
]
```

---

## 🎯 Validaciones Implementadas

### Validaciones del Cliente (JavaScript)

1. **Edad mínima**: 3 años
2. **Cédula escolar**: Obligatoria si edad ≤ 10 años
3. **Cédula personal**: Obligatoria si edad > 10 años
4. **Representante legal**: Obligatorio si edad < 18 años
5. **Verificación de duplicados**: Antes de enviar el formulario

### Validaciones del Servidor (Python)

1. **Al menos una cédula**: Personal o escolar debe estar presente
2. **Formato de cédula**: Validación con regex
3. **Edad mínima**: 3 años (en el modelo)
4. **Campos de representante**: Obligatorios para menores de 18 años
5. **Unicidad**: Verificación de duplicados en base de datos

---

## 📊 Flujo Completo del Registro

```
1. Usuario abre formulario de registro
   ↓
2. Completa datos personales
   ↓
3. Selecciona fecha de nacimiento
   ↓
4. Sistema calcula edad automáticamente
   ↓
5. Si edad ≤ 10 años:
   - Muestra campo de cédula escolar (obligatorio)
   - Cédula personal opcional
   ↓
6. Si edad > 10 años:
   - Muestra campo de cédula personal (obligatorio)
   - Oculta cédula escolar
   ↓
7. Si edad < 18 años:
   - Muestra sección de representante legal
   - Todos los campos del representante son obligatorios
   ↓
8. Usuario presiona "Guardar"
   ↓
9. JavaScript valida campos requeridos
   ↓
10. Envía petición AJAX a /verificar-participante/
    ↓
11. ¿Existe duplicado?
    ├─ SÍ → Muestra modal
    │   ├─ Usuario confirma que es el mismo → Redirige a editar
    │   └─ Usuario dice que no es el mismo → Continúa registro
    └─ NO → Envía formulario al servidor
        ↓
12. Servidor valida datos
    ↓
13. Crea usuario y participante
    ↓
14. Redirige a lista de participantes con mensaje de éxito
```

---

## 🔐 Seguridad

1. **CSRF Token**: Todas las peticiones AJAX incluyen el token CSRF
2. **Autenticación**: Solo usuarios autenticados pueden registrar participantes
3. **Permisos**: Validación de roles (institucional, federación)
4. **Sanitización**: Uso de `.strip()` en todos los inputs
5. **Validación de formato**: Regex para cédulas y teléfonos

---

## 🧪 Casos de Prueba Recomendados

### Caso 1: Registro de menor de 10 años
- Fecha de nacimiento: 2020-01-01
- Debe mostrar campo de cédula escolar
- Debe mostrar sección de representante
- Debe validar que cédula escolar no esté vacía

### Caso 2: Registro de mayor de 10 años
- Fecha de nacimiento: 2010-01-01
- Debe mostrar campo de cédula personal
- Debe mostrar sección de representante
- Debe validar que cédula personal no esté vacía

### Caso 3: Registro de mayor de edad
- Fecha de nacimiento: 2000-01-01
- Debe mostrar campo de cédula personal
- NO debe mostrar sección de representante
- Debe validar que cédula personal no esté vacía

### Caso 4: Detección de duplicado por cédula
- Registrar participante con cédula V-12345678
- Intentar registrar otro con la misma cédula
- Debe mostrar modal de duplicado

### Caso 5: Detección de duplicado por datos personales
- Registrar: Juan Pérez, 2010-01-01
- Intentar registrar: Juan Pérez, 2010-01-01 (con cédula diferente)
- Debe mostrar modal de duplicado

---

## 📝 Notas Técnicas

### Compatibilidad con el Modelo Existente

El modelo `Participante` ya tenía el campo `cedula_escolar`, por lo que no fue necesario crear migraciones:

```python
class Participante(models.Model):
    cedula = models.CharField(max_length=20, unique=True)  # Cédula principal
    cedula_escolar = models.CharField(max_length=20, blank=True)  # Ya existía
    # ... otros campos
```

### Manejo de Username

El username del usuario Django se crea con la cédula principal:
- Si tiene cédula personal: `V-12345678` o `E-12345678`
- Si solo tiene cédula escolar: `E-{cedula_escolar}`

---

## 🚀 Próximas Mejoras Sugeridas

1. **Validación de cédula en tiempo real**: Verificar formato mientras el usuario escribe
2. **Autocompletado**: Sugerir datos si se encuentra un duplicado parcial
3. **Historial de cambios**: Registrar quién y cuándo modificó un participante
4. **Exportación de duplicados**: Reporte de posibles duplicados en el sistema
5. **Validación con SAIME**: Integración con API del SAIME para validar cédulas reales

---

## 📞 Soporte

Para dudas o problemas con esta implementación, revisar:
- Logs del servidor: `/var/log/django/`
- Consola del navegador: Para errores de JavaScript
- Base de datos: Verificar integridad de datos

---

**Fecha de implementación**: 2024
**Versión del sistema**: SNR-PRO v2.0
**Arquitecto responsable**: Sistema Nacional de Robótica
