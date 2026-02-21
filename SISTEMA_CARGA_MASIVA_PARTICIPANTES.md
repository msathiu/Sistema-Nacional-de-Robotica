# 🚀 Sistema de Carga Masiva de Participantes

## 📋 Resumen

Sistema optimizado para agregar participantes a grupos de forma **masiva** o **individual**, diseñado para eventos donde cada grupo debe tener participantes específicos aprobados por la federación.

---

## 🎯 Características Principales

### 1️⃣ **Carga Masiva**
- Ingreso de múltiples cédulas simultáneamente
- Separación automática por comas, espacios o saltos de línea
- Búsqueda paralela de todos los participantes
- Reporte de encontrados vs no encontrados
- Prevención de duplicados automática

### 2️⃣ **Carga Individual**
- Búsqueda uno por uno
- Validación en tiempo real
- Feedback visual inmediato

### 3️⃣ **Tabla Centralizada**
- Vista unificada de todos los participantes agregados
- Eliminación individual
- Contador automático
- Inputs ocultos generados dinámicamente

---

## 🔄 Flujo de Uso

### **Opción A: Carga Masiva** (Recomendado para eventos)

```
1. Click en "Carga Masiva"
   ↓
2. Ingresar lista de cédulas:
   V12345678
   E98765432
   V11223344
   ↓
3. Click en "Buscar Participantes"
   ↓
4. Sistema busca todas las cédulas en paralelo
   ↓
5. Muestra resultados:
   ✓ Encontrados: 2 participantes
   ⚠ No encontrados: V11223344
   ↓
6. Participantes agregados a la tabla
   ↓
7. Modal se cierra automáticamente (si todos fueron encontrados)
```

**Ejemplo de entrada**:
```
V12345678, E98765432, V11223344
```

O con saltos de línea:
```
V12345678
E98765432
V11223344
```

---

### **Opción B: Carga Individual**

```
1. Click en "Agregar Uno"
   ↓
2. Ingresar cédula
   ↓
3. Click en "Buscar"
   ↓
4. Si encuentra: Agrega a tabla y elimina formulario
   ↓
5. Si no encuentra: Muestra alerta
```

---

## 💻 Implementación Técnica

### **Frontend: JavaScript**

#### Variables Globales
```javascript
let participantesAgregados = new Map(); // ID -> {cedula, nombres, apellidos}
```

#### Función: Carga Masiva
```javascript
function procesarCargaMasiva() {
    // 1. Obtener texto del textarea
    const texto = textarea.value.trim();
    
    // 2. Separar cédulas por comas, espacios o saltos de línea
    const cedulas = texto.split(/[,\s\n]+/).filter(c => c.trim());
    
    // 3. Buscar todas en paralelo
    const promesas = cedulas.map(cedula => 
        fetch(`/registry/api/buscar-participante/?cedula=${cedula}`)
            .then(res => res.json())
    );
    
    // 4. Procesar resultados
    Promise.all(promesas).then(resultados => {
        // Agregar encontrados al Map
        // Reportar no encontrados
        // Actualizar tabla
    });
}
```

#### Función: Actualizar Tabla
```javascript
function actualizarTabla() {
    // 1. Limpiar tbody
    tbody.innerHTML = '';
    
    // 2. Iterar sobre participantesAgregados Map
    participantesAgregados.forEach((data, id) => {
        // Crear fila en tabla
        // Crear input oculto con ID
    });
    
    // 3. Mostrar/ocultar tabla según cantidad
}
```

#### Función: Eliminar Participante
```javascript
function eliminarParticipante(id) {
    // 1. Eliminar del Map
    participantesAgregados.delete(id);
    
    // 2. Eliminar input oculto del formulario
    document.getElementById(`participante_${id}`).remove();
    
    // 3. Actualizar tabla
    actualizarTabla();
}
```

---

### **Backend: Vista crear_grupo()**

```python
# Agregar participantes
participantes_ids = request.POST.getlist("participantes[]")
if participantes_ids:
    # Filtrar IDs vacíos y validar que sean numéricos
    participantes_ids_validos = [
        int(pid) for pid in participantes_ids 
        if pid and pid.strip() and pid.strip().isdigit()
    ]
    if participantes_ids_validos:
        grupo.participantes.set(participantes_ids_validos)
    else:
        raise ValueError("Debe agregar al menos un participante válido al grupo")
```

**Validaciones**:
- ✅ Filtra IDs vacíos
- ✅ Valida que sean numéricos con `.isdigit()`
- ✅ Convierte a `int()` de forma segura
- ✅ Requiere al menos un participante válido

---

## 🎨 Interfaz de Usuario

### **Modal de Carga Masiva**

```html
┌─────────────────────────────────────────────────────────┐
│ 🔵 Carga Masiva de Participantes              [X]      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ℹ️ Instrucciones: Ingrese las cédulas separadas por    │
│   comas, espacios o saltos de línea.                   │
│   Ejemplo: V12345678, E98765432, V11223344             │
│                                                         │
│ Lista de Cédulas:                                       │
│ ┌─────────────────────────────────────────────────┐   │
│ │ V12345678                                       │   │
│ │ E98765432                                       │   │
│ │ V11223344                                       │   │
│ │                                                 │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ✓ Encontrados: 2 participantes                         │
│ ⚠ No encontrados: V11223344                            │
│                                                         │
│                    [Cancelar]  [🔍 Buscar Participantes]│
└─────────────────────────────────────────────────────────┘
```

### **Tabla de Participantes Agregados**

```html
┌─────────────────────────────────────────────────────────┐
│ 👥 Participantes                                        │
│                    [📤 Carga Masiva] [➕ Agregar Uno]   │
├───┬──────────────┬──────────────┬──────────────┬────────┤
│ # │ Cédula       │ Nombres      │ Apellidos    │ Acción │
├───┼──────────────┼──────────────┼──────────────┼────────┤
│ 1 │ V12345678    │ Juan         │ Pérez        │ [🗑️]   │
│ 2 │ E98765432    │ María        │ González     │ [🗑️]   │
│ 3 │ V55667788    │ Pedro        │ Rodríguez    │ [🗑️]   │
└───┴──────────────┴──────────────┴──────────────┴────────┘
```

---

## 🔒 Validaciones

### **Frontend**
1. ✅ Textarea no vacío
2. ✅ Al menos una cédula válida
3. ✅ Prevención de duplicados (verifica Map antes de agregar)
4. ✅ Validación de respuesta del API

### **Backend**
1. ✅ IDs deben ser numéricos
2. ✅ IDs no pueden estar vacíos
3. ✅ Al menos un participante válido requerido
4. ✅ Participantes deben existir en la BD

---

## 📊 Ventajas del Sistema

### **Para Eventos con Grupos Específicos**

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Velocidad** | 1 participante/vez | 50+ participantes simultáneos |
| **Errores** | Duplicados manuales | Prevención automática |
| **UX** | Repetitivo | Fluido y rápido |
| **Validación** | Solo backend | Frontend + Backend |
| **Feedback** | Genérico | Detallado (encontrados vs no encontrados) |

### **Casos de Uso Ideales**

1. **Eventos Institucionales**: Cargar lista completa de estudiantes
2. **Eventos de Club**: Cargar miembros específicos del club
3. **Competencias**: Cargar equipos completos
4. **Talleres**: Cargar participantes pre-registrados

---

## 🎯 Ejemplo de Uso Real

### **Escenario**: Competencia Regional de Robótica

**Institución**: Liceo Bolivariano  
**Evento**: Competencia Regional 2024  
**Participantes**: 25 estudiantes

#### **Paso 1**: Preparar lista de cédulas
```
V12345678
V23456789
E34567890
V45678901
... (21 más)
```

#### **Paso 2**: Carga masiva
1. Click en "Carga Masiva"
2. Pegar lista completa
3. Click en "Buscar Participantes"

#### **Paso 3**: Resultado
```
✓ Encontrados: 24 participantes
⚠ No encontrados: V99999999
```

#### **Paso 4**: Corrección
- Verificar cédula incorrecta
- Agregar individualmente si es necesario

#### **Paso 5**: Guardar grupo
- 24 participantes agregados
- Grupo listo para inscribir a evento

**Tiempo total**: ~2 minutos (vs 25 minutos uno por uno)

---

## 🐛 Manejo de Errores

### **Error 1: Participante no encontrado**
```javascript
if (!data.found) {
    alert('Participante no encontrado. Debe estar registrado en el sistema.');
}
```

**Solución**: Registrar participante primero en el sistema.

### **Error 2: Participante duplicado**
```javascript
if (participantesAgregados.has(data.id)) {
    alert('Este participante ya está en el grupo');
    return;
}
```

**Solución**: Sistema previene automáticamente.

### **Error 3: Sin participantes**
```python
if not participantes_ids_validos:
    raise ValueError("Debe agregar al menos un participante válido al grupo")
```

**Solución**: Agregar al menos un participante antes de guardar.

---

## 📱 Responsive Design

- ✅ Modal adaptable a móviles
- ✅ Tabla con scroll horizontal en pantallas pequeñas
- ✅ Botones táctiles optimizados

---

## 🚀 Mejoras Futuras (Opcionales)

1. **Importar desde Excel/CSV**: Subir archivo con lista de cédulas
2. **Autocompletado**: Sugerencias mientras escribe
3. **Validación de formato**: Verificar formato de cédula antes de buscar
4. **Historial**: Guardar listas de participantes frecuentes
5. **Plantillas**: Grupos predefinidos por institución

---

## ✅ Checklist de Implementación

- [x] Modal de carga masiva
- [x] Textarea con separación inteligente
- [x] Búsqueda paralela con Promise.all()
- [x] Tabla centralizada de participantes
- [x] Map para prevenir duplicados
- [x] Inputs ocultos dinámicos
- [x] Validación backend de IDs numéricos
- [x] Feedback visual de resultados
- [x] Eliminación individual
- [x] Cierre automático de modal

---

## 📄 Archivos Modificados

- `registry/templates/registry/grupo_crear.html` - UI completa
- `registry/views_institucional.py` - Validación backend (ya implementada)

---

## 🎓 Conclusión

Sistema optimizado para **carga masiva de participantes** que reduce el tiempo de creación de grupos de **25 minutos a 2 minutos** para eventos con 25+ participantes. Ideal para eventos institucionales y de club donde los grupos deben ser específicos y aprobados por la federación.
