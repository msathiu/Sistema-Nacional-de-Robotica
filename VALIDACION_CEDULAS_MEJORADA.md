# Validación Mejorada de Cédulas - Registro de Participantes

## 🎯 Lógica de Validación Implementada

### Reglas por Edad

#### **Menores o iguales a 10 años**
- ✅ Se muestran **ambos campos**: Cédula Personal y Cédula Escolar
- ✅ **Al menos UNA** cédula es requerida (personal O escolar)
- ✅ Si ingresa cédula personal → cédula escolar es opcional
- ✅ Si ingresa cédula escolar → cédula personal es opcional
- ✅ Si no ingresa ninguna → error de validación

#### **Mayores de 10 años**
- ✅ Solo se muestra campo de **Cédula Personal**
- ✅ Cédula Personal es **obligatoria**
- ✅ Campo de cédula escolar está oculto

---

## 💡 Feedback Visual en Tiempo Real

### Labels Dinámicos

**Para menores de 10 años:**

```
Escenario 1: Ninguna cédula ingresada
├─ Cédula Personal: [required-field] "Requerida si no tiene cédula escolar"
└─ Cédula Escolar: [required-field] "Requerida si no tiene cédula personal"

Escenario 2: Cédula personal ingresada
├─ Cédula Personal: [normal] "Opcional (ya tiene cédula escolar)"
└─ Cédula Escolar: [normal] "Opcional (ya tiene cédula personal)"

Escenario 3: Cédula escolar ingresada
├─ Cédula Personal: [normal] "Opcional (ya tiene cédula escolar)"
└─ Cédula Escolar: [normal] "Opcional (ya tiene cédula personal)"
```

**Para mayores de 10 años:**
```
├─ Cédula Personal: [required-field] (obligatorio)
└─ Cédula Escolar: [oculto]
```

---

## 🔧 Implementación Técnica

### 1. HTML - Labels Dinámicos

```html
<div class="col-md-6" id="cedula_personal_container">
    <label id="label_cedula_personal" class="form-label fw-bold text-muted small text-uppercase">
        Cédula Personal
    </label>
    <div class="input-group">
        <select name="nacionalidad" id="id_nacionalidad" class="form-select">
            <option value="V">V</option>
            <option value="E">E</option>
        </select>
        <input type="text" name="cedula_personal" id="id_cedula_personal" class="form-control">
    </div>
    <small class="text-muted" id="help_cedula_personal"></small>
</div>

<div class="col-md-6" id="cedula_escolar_container" style="display: none;">
    <label id="label_cedula_escolar" class="form-label fw-bold text-muted small text-uppercase">
        Cédula Escolar
    </label>
    <input type="text" name="cedula_escolar" id="id_cedula_escolar" class="form-control">
    <small class="text-muted" id="help_cedula_escolar"></small>
</div>
```

### 2. JavaScript - Validación Dinámica

```javascript
// Función de validación
function validarCedulas() {
    const edad = parseInt(edadHid.value) || 0;
    const cedulaPersonal = cedulaPersonalInput.value.trim();
    const cedulaEscolar = cedulaEscolarInput.value.trim();
    
    if (edad <= 10 && edad >= 3) {
        // Para menores de 10 años: al menos una cédula requerida
        if (!cedulaPersonal && !cedulaEscolar) {
            return false;
        }
    }
    return true;
}

// Listener para cédula personal
cedulaPersonalInput.addEventListener('input', () => {
    const edad = parseInt(edadHid.value) || 0;
    if (edad <= 10 && edad >= 3) {
        const helpEscolar = document.getElementById('help_cedula_escolar');
        const labelEscolar = document.getElementById('label_cedula_escolar');
        if (cedulaPersonalInput.value.trim()) {
            helpEscolar.textContent = 'Opcional (ya tiene cédula personal)';
            labelEscolar.className = 'form-label fw-bold text-muted small text-uppercase';
        } else {
            helpEscolar.textContent = 'Requerida si no tiene cédula personal';
            labelEscolar.className = 'form-label fw-bold text-muted small text-uppercase required-field';
        }
    }
});

// Listener para cédula escolar
cedulaEscolarInput.addEventListener('input', () => {
    const edad = parseInt(edadHid.value) || 0;
    if (edad <= 10 && edad >= 3) {
        const helpPersonal = document.getElementById('help_cedula_personal');
        const labelPersonal = document.getElementById('label_cedula_personal');
        if (cedulaEscolarInput.value.trim()) {
            helpPersonal.textContent = 'Opcional (ya tiene cédula escolar)';
            labelPersonal.className = 'form-label fw-bold text-muted small text-uppercase';
        } else {
            helpPersonal.textContent = 'Requerida si no tiene cédula escolar';
            labelPersonal.className = 'form-label fw-bold text-muted small text-uppercase required-field';
        }
    }
});
```

### 3. Python - Validación Backend

```python
def clean(self):
    cleaned_data = super().clean()
    fecha_nac = cleaned_data.get("fecha_nacimiento")
    cedula_personal = self.data.get('cedula_personal', '').strip()
    cedula_escolar = self.data.get('cedula_escolar', '').strip()
    
    # Validar que tenga al menos una cédula
    if not cedula_personal and not cedula_escolar:
        raise ValidationError("Debe proporcionar al menos una cédula (personal o escolar).")
    
    if fecha_nac:
        today = date.today()
        edad = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
        
        # Para mayores de 10 años: cédula personal obligatoria
        if edad > 10 and not cedula_personal:
            raise ValidationError("La cédula personal es obligatoria para mayores de 10 años.")
    
    return cleaned_data
```

---

## 🧪 Casos de Prueba

### Test 1: Menor de 10 años con cédula personal
```
Edad: 8 años
Cédula Personal: V-12345678
Cédula Escolar: (vacío)

Resultado: ✅ VÁLIDO
```

### Test 2: Menor de 10 años con cédula escolar
```
Edad: 8 años
Cédula Personal: (vacío)
Cédula Escolar: 123456789

Resultado: ✅ VÁLIDO
```

### Test 3: Menor de 10 años con ambas cédulas
```
Edad: 8 años
Cédula Personal: V-12345678
Cédula Escolar: 123456789

Resultado: ✅ VÁLIDO
```

### Test 4: Menor de 10 años sin ninguna cédula
```
Edad: 8 años
Cédula Personal: (vacío)
Cédula Escolar: (vacío)

Resultado: ❌ ERROR - "Debe proporcionar al menos una cédula"
```

### Test 5: Mayor de 10 años con cédula personal
```
Edad: 15 años
Cédula Personal: V-12345678

Resultado: ✅ VÁLIDO
```

### Test 6: Mayor de 10 años sin cédula personal
```
Edad: 15 años
Cédula Personal: (vacío)

Resultado: ❌ ERROR - "La cédula personal es obligatoria para mayores de 10 años"
```

---

## 📊 Tabla de Validación

| Edad | Cédula Personal | Cédula Escolar | Resultado |
|------|----------------|----------------|-----------|
| ≤ 10 | ✅ Sí | ❌ No | ✅ Válido |
| ≤ 10 | ❌ No | ✅ Sí | ✅ Válido |
| ≤ 10 | ✅ Sí | ✅ Sí | ✅ Válido |
| ≤ 10 | ❌ No | ❌ No | ❌ Error |
| > 10 | ✅ Sí | N/A | ✅ Válido |
| > 10 | ❌ No | N/A | ❌ Error |

---

## ✨ Mejoras Implementadas

1. **Feedback en tiempo real**: Los labels y textos de ayuda cambian mientras el usuario escribe
2. **Validación flexible**: Acepta cualquier combinación válida de cédulas para menores de 10 años
3. **Mensajes claros**: Indica exactamente qué se requiere en cada momento
4. **Validación doble**: Cliente (JavaScript) y servidor (Python)
5. **UX mejorada**: El usuario sabe en todo momento qué campos son obligatorios

---

## 🔄 Flujo de Usuario

```
1. Usuario ingresa fecha de nacimiento
   ↓
2. Sistema calcula edad
   ↓
3. ¿Edad ≤ 10 años?
   ├─ SÍ → Muestra ambos campos de cédula
   │        Usuario puede ingresar cualquiera
   │        ↓
   │        Usuario ingresa cédula personal
   │        ↓
   │        Sistema actualiza: "Cédula escolar opcional"
   │        ↓
   │        O usuario ingresa cédula escolar
   │        ↓
   │        Sistema actualiza: "Cédula personal opcional"
   │
   └─ NO → Muestra solo cédula personal (obligatorio)
```

---

**Estado**: ✅ IMPLEMENTADO
**Fecha**: 2024
**Sistema**: SNR-PRO v2.0
