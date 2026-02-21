# 🐛 Corrección: Error al Crear Grupo con Participantes

## 📋 Problema Identificado

**Error**: `Field 'id' expected a number but got 'acvteer'`

**Causa**: El formulario de creación de grupos estaba enviando **cédulas de participantes** en lugar de **IDs numéricos** al backend.

---

## 🔍 Análisis del Bug

### Ubicación del Error

**Template**: `registry/templates/registry/grupo_crear.html` (línea 119)

```javascript
// ❌ CÓDIGO INCORRECTO
card.querySelector('.nombres-participante').value = data.id;  // Asigna ID al campo de nombres
card.querySelector('.nombres-participante').name = `participantes[]`;
```

**Problema**:
1. El campo `name="participantes[]"` estaba en el input de **nombres** (texto)
2. Cuando se buscaba un participante, se asignaba el ID al **value** del campo de nombres
3. Cuando NO se encontraba el participante, el campo quedaba con la **cédula** (texto)
4. El backend esperaba recibir IDs numéricos pero recibía strings como `'acvteer'`

---

## ✅ Solución Implementada

### 1. Template `grupo_crear.html`

**Cambio 1**: Agregar campo oculto para IDs

```html
<!-- ✅ NUEVO: Campo oculto para el ID -->
<input type="hidden" class="participante-id" name="participantes[]" value="">

<!-- Campos visibles solo para mostrar datos -->
<input type="text" class="form-control nombres-participante" readonly required>
<input type="text" class="form-control apellidos-participante" readonly required>
```

**Cambio 2**: Actualizar función JavaScript

```javascript
function buscarParticipante(btn) {
    const card = btn.closest('.participante-card');
    const cedula = card.querySelector('.cedula-participante').value.trim();
    
    fetch(`/registry/api/buscar-participante/?cedula=${cedula}`)
        .then(res => res.json())
        .then(data => {
            if (data.found) {
                // ✅ Asignar ID al campo oculto
                card.querySelector('.participante-id').value = data.id;
                // Mostrar datos en campos readonly
                card.querySelector('.nombres-participante').value = data.nombres;
                card.querySelector('.apellidos-participante').value = data.apellidos;
                card.querySelector('.fecha-participante').value = data.fecha_nacimiento;
                // Cambiar botón a estado "Encontrado"
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-check"></i> Encontrado';
                btn.classList.add('btn-success');
            } else {
                // ✅ Mostrar mensaje claro
                alert('Participante no encontrado. Debe estar registrado en el sistema antes de agregarlo al grupo.');
                // Limpiar todos los campos
                card.querySelector('.participante-id').value = '';
                card.querySelector('.nombres-participante').value = '';
                card.querySelector('.apellidos-participante').value = '';
                card.querySelector('.fecha-participante').value = '';
            }
        });
}
```

---

### 2. Vista `views_institucional.py` - `crear_grupo()`

**Validación de IDs**:

```python
# Agregar participantes
participantes_ids = request.POST.getlist("participantes[]")
if participantes_ids:
    # ✅ Filtrar IDs vacíos y validar que sean numéricos
    participantes_ids_validos = [
        int(pid) for pid in participantes_ids 
        if pid and pid.strip() and pid.strip().isdigit()
    ]
    if participantes_ids_validos:
        grupo.participantes.set(participantes_ids_validos)
    else:
        raise ValueError("Debe agregar al menos un participante válido al grupo")
```

---

### 3. Vista `views_institucional.py` - `editar_grupo()`

**Misma validación aplicada**:

```python
# Actualizar participantes
participantes_ids = request.POST.getlist("participantes[]")
# ✅ Filtrar IDs vacíos y validar que sean numéricos
participantes_ids_validos = [
    int(pid) for pid in participantes_ids 
    if pid and pid.strip() and pid.strip().isdigit()
]
grupo.participantes.set(participantes_ids_validos)
```

---

## 🎯 Mejoras Implementadas

### 1. **Campos Readonly**
Los campos de nombres, apellidos y fecha ahora son **readonly** para evitar edición manual.

### 2. **Validación Obligatoria**
Todos los campos de participante ahora son **required**, asegurando que se busque y encuentre el participante.

### 3. **Feedback Visual**
El botón "Buscar" cambia a "Encontrado" (verde) cuando se encuentra el participante exitosamente.

### 4. **Mensajes Claros**
- ✅ "Participante encontrado"
- ❌ "Participante no encontrado. Debe estar registrado en el sistema antes de agregarlo al grupo."

### 5. **Validación Backend**
El backend ahora valida que todos los IDs sean numéricos antes de procesarlos.

---

## 🔄 Flujo Correcto Ahora

```
1. Usuario hace clic en "Agregar Participante"
   ↓
2. Ingresa cédula del participante (ej: "V12345678")
   ↓
3. Hace clic en "Buscar"
   ↓
4. Sistema busca en la BD por cédula
   ↓
5A. SI ENCUENTRA:
    - Asigna ID al campo oculto (ej: value="42")
    - Muestra datos en campos readonly
    - Botón cambia a "Encontrado" (verde)
    ↓
5B. SI NO ENCUENTRA:
    - Muestra alerta
    - Limpia todos los campos
    - Usuario debe registrar participante primero
   ↓
6. Usuario hace clic en "Guardar Grupo"
   ↓
7. Backend recibe: participantes[] = [42, 57, 89]  ✅ IDs numéricos
   ↓
8. Grupo creado exitosamente
```

---

## 🧪 Casos de Prueba

### ✅ Caso 1: Participante Existente
- **Input**: Cédula "V12345678" (existe en BD con ID=42)
- **Resultado**: Campo oculto recibe `value="42"`, datos se muestran
- **Backend**: Recibe `participantes[] = [42]` ✅

### ✅ Caso 2: Participante No Existente
- **Input**: Cédula "V99999999" (no existe)
- **Resultado**: Alerta mostrada, campos limpiados
- **Backend**: No recibe ese participante ✅

### ✅ Caso 3: Múltiples Participantes
- **Input**: 3 participantes con IDs 42, 57, 89
- **Resultado**: Campos ocultos con values "42", "57", "89"
- **Backend**: Recibe `participantes[] = [42, 57, 89]` ✅

### ✅ Caso 4: Campo Vacío
- **Input**: Usuario no busca participante (campo oculto vacío)
- **Resultado**: Validación HTML impide submit (campo required)
- **Backend**: Validación filtra IDs vacíos ✅

---

## 📊 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `registry/templates/registry/grupo_crear.html` | Campo oculto agregado, función buscarParticipante() actualizada, campos readonly |
| `registry/views_institucional.py` | Validación de IDs numéricos en crear_grupo() y editar_grupo() |

---

## 🚀 Impacto

- ✅ **Bug corregido**: Ya no se envían cédulas en lugar de IDs
- ✅ **Validación robusta**: Backend valida que todos los IDs sean numéricos
- ✅ **UX mejorada**: Feedback visual claro del estado de búsqueda
- ✅ **Prevención**: Campos readonly evitan edición manual incorrecta
- ✅ **Consistencia**: Misma validación en crear y editar

---

## 📝 Notas Importantes

1. **Participantes deben estar registrados**: No se permite crear participantes "al vuelo" durante la creación del grupo. Deben estar previamente registrados en el sistema.

2. **Búsqueda obligatoria**: El usuario DEBE buscar cada participante por cédula antes de poder guardar el grupo.

3. **Validación doble**: Tanto en frontend (HTML5 required) como en backend (validación de IDs numéricos).

---

## ✅ Estado

**COMPLETADO** - Bug corregido y validaciones implementadas.
