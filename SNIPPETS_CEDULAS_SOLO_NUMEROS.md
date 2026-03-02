# Snippets de Código: Validación de Cédulas Solo Números

## 📦 Snippets Reutilizables

### 1. Python: Limpiar Cédula (Solo Números)

```python
def limpiar_cedula(cedula_raw):
    """
    Limpia una cédula dejando solo números.
    
    Args:
        cedula_raw (str): Cédula con posibles caracteres especiales
        
    Returns:
        str: Cédula con solo números
        
    Examples:
        >>> limpiar_cedula("V-12.345.678")
        '12345678'
        >>> limpiar_cedula("ABC-123-XYZ")
        '123'
    """
    if not cedula_raw:
        return ''
    return ''.join(filter(str.isdigit, cedula_raw.strip()))
```

---

### 2. Python: Validar Longitud de Cédula

```python
def validar_longitud_cedula(cedula, max_length=10):
    """
    Valida que la cédula no exceda la longitud máxima.
    
    Args:
        cedula (str): Cédula a validar
        max_length (int): Longitud máxima permitida
        
    Returns:
        tuple: (es_valida, mensaje_error)
        
    Examples:
        >>> validar_longitud_cedula("12345678", 10)
        (True, None)
        >>> validar_longitud_cedula("12345678901", 10)
        (False, "La cédula no puede tener más de 10 dígitos")
    """
    if not cedula:
        return True, None
    
    if len(cedula) > max_length:
        return False, f"La cédula no puede tener más de {max_length} dígitos"
    
    return True, None
```

---

### 3. Python: Formatear Cédula para Display

```python
def formatear_cedula_display(nacionalidad, cedula_numeros):
    """
    Formatea una cédula para mostrar al usuario.
    
    Args:
        nacionalidad (str): 'V' o 'E'
        cedula_numeros (str): Números de la cédula
        
    Returns:
        str: Cédula formateada
        
    Examples:
        >>> formatear_cedula_display('V', '12345678')
        'V-12.345.678'
    """
    if not cedula_numeros:
        return ''
    
    # Agregar puntos cada 3 dígitos desde la derecha
    cedula_con_puntos = ''
    for i, digito in enumerate(reversed(cedula_numeros)):
        if i > 0 and i % 3 == 0:
            cedula_con_puntos = '.' + cedula_con_puntos
        cedula_con_puntos = digito + cedula_con_puntos
    
    return f"{nacionalidad}-{cedula_con_puntos}"
```

---

### 4. JavaScript: Limpiar Input en Tiempo Real

```javascript
/**
 * Limpia un input para aceptar solo números
 * @param {HTMLInputElement} input - Elemento input a limpiar
 * @param {number} maxLength - Longitud máxima permitida
 */
function limpiarInputNumerico(input, maxLength = 10) {
    input.addEventListener('input', function(e) {
        // Remover todo excepto números
        let valor = e.target.value.replace(/\D/g, '');
        
        // Limitar longitud
        if (valor.length > maxLength) {
            valor = valor.substring(0, maxLength);
        }
        
        e.target.value = valor;
    });
}

// Uso:
const cedulaInput = document.getElementById('id_cedula_personal');
limpiarInputNumerico(cedulaInput, 10);
```

---

### 5. JavaScript: Validar Cédula Antes de Submit

```javascript
/**
 * Valida que una cédula tenga solo números
 * @param {string} cedula - Cédula a validar
 * @returns {Object} - {valida: boolean, mensaje: string}
 */
function validarCedulaNumerica(cedula) {
    if (!cedula || cedula.trim() === '') {
        return { valida: false, mensaje: 'La cédula es requerida' };
    }
    
    // Verificar que solo contenga números
    if (!/^\d+$/.test(cedula)) {
        return { valida: false, mensaje: 'La cédula debe contener solo números' };
    }
    
    // Verificar longitud mínima
    if (cedula.length < 6) {
        return { valida: false, mensaje: 'La cédula debe tener al menos 6 dígitos' };
    }
    
    return { valida: true, mensaje: '' };
}

// Uso en submit:
form.addEventListener('submit', (e) => {
    const cedula = document.getElementById('id_cedula_personal').value;
    const resultado = validarCedulaNumerica(cedula);
    
    if (!resultado.valida) {
        e.preventDefault();
        alert(resultado.mensaje);
    }
});
```

---

### 6. Django Form: Método Clean Genérico

```python
class CedulaCleanMixin:
    """Mixin para limpiar campos de cédula en formularios Django."""
    
    def clean_cedula_field(self, field_name, max_length=10):
        """
        Limpia un campo de cédula dejando solo números.
        
        Args:
            field_name (str): Nombre del campo a limpiar
            max_length (int): Longitud máxima permitida
            
        Returns:
            str: Cédula limpia
            
        Raises:
            ValidationError: Si la cédula excede la longitud máxima
        """
        cedula = self.data.get(field_name, '').strip()
        
        if not cedula:
            return ''
        
        # Limpiar: solo números
        cedula_limpia = ''.join(filter(str.isdigit, cedula))
        
        # Validar longitud
        if cedula_limpia and len(cedula_limpia) > max_length:
            raise ValidationError(
                f"La cédula no puede tener más de {max_length} dígitos."
            )
        
        return cedula_limpia

# Uso en formulario:
class MiFormulario(CedulaCleanMixin, forms.ModelForm):
    def clean_cedula_personal(self):
        return self.clean_cedula_field('cedula_personal', max_length=10)
    
    def clean_cedula_escolar(self):
        return self.clean_cedula_field('cedula_escolar', max_length=20)
```

---

### 7. Django Model: Validador Personalizado

```python
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

def validar_cedula_solo_numeros(value):
    """
    Validador personalizado para cédulas que solo acepta números.
    
    Args:
        value (str): Valor a validar
        
    Raises:
        ValidationError: Si el valor contiene caracteres no numéricos
    """
    if value and not value.isdigit():
        raise ValidationError(
            'La cédula debe contener solo números',
            code='cedula_invalida'
        )

# Uso en modelo:
class Participante(models.Model):
    cedula_escolar = models.CharField(
        max_length=20,
        blank=True,
        validators=[validar_cedula_solo_numeros]
    )
```

---

### 8. JavaScript: Formatear Cédula para Display

```javascript
/**
 * Formatea una cédula para mostrar con puntos
 * @param {string} nacionalidad - 'V' o 'E'
 * @param {string} cedula - Números de la cédula
 * @returns {string} - Cédula formateada (ej: "V-12.345.678")
 */
function formatearCedulaDisplay(nacionalidad, cedula) {
    if (!cedula) return '';
    
    // Agregar puntos cada 3 dígitos desde la derecha
    const cedulaArray = cedula.split('').reverse();
    const cedulaConPuntos = [];
    
    cedulaArray.forEach((digito, index) => {
        if (index > 0 && index % 3 === 0) {
            cedulaConPuntos.push('.');
        }
        cedulaConPuntos.push(digito);
    });
    
    return `${nacionalidad}-${cedulaConPuntos.reverse().join('')}`;
}

// Ejemplo de uso:
console.log(formatearCedulaDisplay('V', '12345678'));
// Output: "V-12.345.678"
```

---

### 9. Python: Extraer Nacionalidad y Números

```python
import re

def extraer_componentes_cedula(cedula_completa):
    """
    Extrae nacionalidad y números de una cédula.
    
    Args:
        cedula_completa (str): Cédula en formato "V-12345678"
        
    Returns:
        tuple: (nacionalidad, numeros) o (None, None) si es inválida
        
    Examples:
        >>> extraer_componentes_cedula("V-12345678")
        ('V', '12345678')
        >>> extraer_componentes_cedula("E-9876543")
        ('E', '9876543')
    """
    if not cedula_completa:
        return None, None
    
    # Patrón: letra (V o E) + guion + números
    patron = r'^([VE])-(\d+)$'
    match = re.match(patron, cedula_completa.strip())
    
    if match:
        return match.group(1), match.group(2)
    
    return None, None
```

---

### 10. JavaScript: Validación Completa de Formulario

```javascript
/**
 * Valida el formulario de registro completo
 * @param {HTMLFormElement} form - Formulario a validar
 * @returns {Object} - {valido: boolean, errores: Array}
 */
function validarFormularioRegistro(form) {
    const errores = [];
    
    // Validar cédula personal
    const cedulaPersonal = form.querySelector('[name="cedula_personal"]').value;
    const cedulaEscolar = form.querySelector('[name="cedula_escolar"]').value;
    const edad = parseInt(form.querySelector('[name="edad"]').value) || 0;
    
    // Validar que tenga al menos una cédula
    if (!cedulaPersonal && !cedulaEscolar) {
        errores.push('Debe proporcionar al menos una cédula (personal o escolar)');
    }
    
    // Validar cédula personal para mayores de 10 años
    if (edad > 10 && !cedulaPersonal) {
        errores.push('La cédula personal es obligatoria para mayores de 10 años');
    }
    
    // Validar que solo contengan números
    if (cedulaPersonal && !/^\d+$/.test(cedulaPersonal)) {
        errores.push('La cédula personal debe contener solo números');
    }
    
    if (cedulaEscolar && !/^\d+$/.test(cedulaEscolar)) {
        errores.push('La cédula escolar debe contener solo números');
    }
    
    return {
        valido: errores.length === 0,
        errores: errores
    };
}

// Uso:
form.addEventListener('submit', (e) => {
    const resultado = validarFormularioRegistro(e.target);
    
    if (!resultado.valido) {
        e.preventDefault();
        alert('Errores:\n' + resultado.errores.join('\n'));
    }
});
```

---

## 🧪 Tests Unitarios

### Test Django: Limpieza de Cédulas

```python
from django.test import TestCase
from users.forms import ParticipanteRegistrationForm

class CedulaLimpiezaTestCase(TestCase):
    """Tests para validar la limpieza de cédulas."""
    
    def test_cedula_personal_con_puntos(self):
        """Debe limpiar puntos de la cédula personal."""
        form = ParticipanteRegistrationForm(data={
            'cedula_personal': '12.345.678',
            # ... otros campos requeridos
        })
        cedula_limpia = form.clean_cedula_personal()
        self.assertEqual(cedula_limpia, '12345678')
    
    def test_cedula_escolar_con_letras(self):
        """Debe remover letras de la cédula escolar."""
        form = ParticipanteRegistrationForm(data={
            'cedula_escolar': 'ABC123XYZ',
            # ... otros campos requeridos
        })
        cedula_limpia = form.clean_cedula_escolar()
        self.assertEqual(cedula_limpia, '123')
    
    def test_cedula_personal_longitud_excedida(self):
        """Debe rechazar cédulas que excedan 10 dígitos."""
        form = ParticipanteRegistrationForm(data={
            'cedula_personal': '12345678901',  # 11 dígitos
            # ... otros campos requeridos
        })
        with self.assertRaises(ValidationError):
            form.clean_cedula_personal()
```

---

## 📚 Documentación de Funciones

### Convenciones de Nomenclatura

- **Funciones de limpieza**: `limpiar_*` o `clean_*`
- **Funciones de validación**: `validar_*` o `validate_*`
- **Funciones de formato**: `formatear_*` o `format_*`

### Parámetros Comunes

- `cedula_raw`: Cédula sin procesar (puede contener caracteres especiales)
- `cedula_limpia`: Cédula procesada (solo números)
- `max_length`: Longitud máxima permitida
- `nacionalidad`: 'V' o 'E'

---

## 🎯 Mejores Prácticas

1. **Siempre limpiar en múltiples capas**: Frontend → Formulario → Vista → Modelo
2. **Usar regex consistentes**: `/\D/g` en JS, `filter(str.isdigit)` en Python
3. **Validar longitud**: Prevenir overflow en base de datos
4. **Mensajes claros**: Indicar exactamente qué está mal
5. **Tests exhaustivos**: Cubrir casos edge (vacío, muy largo, caracteres especiales)

---

**Última Actualización**: 2024  
**Mantenedor**: Equipo de Desarrollo SNR-PRO
