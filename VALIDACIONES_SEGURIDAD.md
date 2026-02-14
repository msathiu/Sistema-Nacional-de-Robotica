# 🛡️ Validaciones de Seguridad en Formularios

## ✅ Resumen de Protecciones Implementadas

Los formularios del sistema tienen múltiples capas de validación para prevenir ataques y asegurar la integridad de los datos.

---

## 🔒 Validaciones por Formulario

### 1. InstitucionRegistrationForm

#### Validaciones de Texto
- ✅ **Nombre**:
  - Máximo 255 caracteres
  - No permite `< > " '` (previene XSS)
  - Sanitización automática (strip)

- ✅ **Dirección**:
  - Máximo 500 caracteres
  - Sanitización de espacios

- ✅ **Nueva Dependencia**:
  - Máximo 255 caracteres
  - No permite `< > " '`

#### Validaciones de Email
- ✅ Formato válido (validación de Django)
- ✅ Unicidad (no duplicados en BD)
- ✅ Máximo 254 caracteres

#### Validaciones de RIF
- ✅ **Letra**: Solo J, G, V, E
- ✅ **Número**: Exactamente 9 dígitos numéricos
- ✅ **Formato**: X-XXXXXXXX-X
- ✅ **MPPE**: Validación especial G-20000009-0

#### Validaciones de Teléfono
- ✅ **Código de área**: Lista cerrada (0412, 0414, 0416, 0424, 0426, 0212, 0281)
- ✅ **Número**: Exactamente 7 dígitos numéricos
- ✅ Solo números (no letras ni caracteres especiales)

#### Validaciones de Contraseña
- ✅ Mínimo 8 caracteres
- ✅ Máximo 128 caracteres
- ✅ Al menos 1 mayúscula
- ✅ Al menos 1 número
- ✅ Al menos 1 carácter especial
- ✅ Confirmación debe coincidir

#### Validaciones de Selección
- ✅ **Tipo de institución**: Solo valores permitidos en CHOICES
- ✅ **Naturaleza**: Solo valores permitidos en CHOICES
- ✅ **Subcategoría**: Validación según tipo
- ✅ **Estado/Municipio/Parroquia**: Solo IDs existentes en BD

---

### 2. ParticipanteRegistrationForm

#### Validaciones de Identidad
- ✅ **Cédula**:
  - Formato: V12345678 o E12345678
  - Regex: `^[VE]\d{6,8}$`
  - Solo números después de la letra
  - Unicidad en BD

#### Validaciones de Nombres
- ✅ **Nombres**:
  - Solo letras y espacios
  - Incluye caracteres latinos (á, é, í, ó, ú, ñ)
  - Máximo 100 caracteres
  - Regex: `^[a-zA-ZÁ-úñÑ\s]+$`

- ✅ **Apellidos**:
  - Solo letras y espacios
  - Incluye caracteres latinos
  - Máximo 100 caracteres
  - Regex: `^[a-zA-ZÁ-úñÑ\s]+$`

#### Validaciones de Contacto
- ✅ **Teléfono**:
  - Exactamente 7 dígitos
  - Solo números
  - Sin guiones ni espacios

- ✅ **Dirección**:
  - Máximo 500 caracteres
  - No permite `< > " '`
  - Sanitización automática

#### Validaciones de Fecha
- ✅ **Fecha de nacimiento**:
  - Formato válido (YYYY-MM-DD)
  - Edad mínima 4 años (validación en modelo)
  - No fechas futuras

---

### 3. CustomUserCreationForm

#### Validaciones de Usuario
- ✅ **Username**:
  - Validaciones de Django por defecto
  - Unicidad en BD
  - Caracteres alfanuméricos y @/./+/-/_

- ✅ **Email**:
  - Formato válido
  - Obligatorio
  - Unicidad

- ✅ **Contraseña**:
  - Validadores de Django
  - Validadores personalizados (uppercase, lowercase, symbol)

---

## 🚫 Protecciones Contra Ataques

### XSS (Cross-Site Scripting)
```python
# Bloqueo de caracteres peligrosos
if re.search(r'[<>"\'']', campo):
    raise ValidationError("Contiene caracteres no permitidos")
```

**Caracteres bloqueados**: `< > " '`
**Campos protegidos**: nombre, dirección, dependencia

### SQL Injection
- ✅ Django ORM previene automáticamente
- ✅ Queries parametrizadas
- ✅ No se ejecuta SQL raw sin sanitización

### CSRF (Cross-Site Request Forgery)
- ✅ Token CSRF en todos los formularios
- ✅ Middleware de Django activo
- ✅ Validación automática en POST

### Inyección de Comandos
- ✅ No se ejecutan comandos del sistema con input de usuario
- ✅ Validación de tipos de datos
- ✅ Listas cerradas para selecciones

---

## 📊 Validaciones por Tipo de Dato

### Campos Numéricos
```python
# Solo dígitos, longitud exacta
if not valor.isdigit() or len(valor) != longitud_esperada:
    raise ValidationError("Formato inválido")
```

**Aplicado a**:
- RIF número (9 dígitos)
- Teléfono (7 dígitos)
- Cédula (6-8 dígitos después de letra)

### Campos de Texto
```python
# Longitud máxima y caracteres permitidos
if len(valor) > max_length:
    raise ValidationError("Texto demasiado largo")
if re.search(r'[<>"\'']', valor):
    raise ValidationError("Caracteres no permitidos")
```

**Aplicado a**:
- Nombres (100 caracteres, solo letras)
- Direcciones (500 caracteres, sin HTML)
- Dependencias (255 caracteres, sin HTML)

### Campos de Selección
```python
# Solo valores de lista cerrada
if valor not in valores_permitidos:
    raise ValidationError("Valor inválido")
```

**Aplicado a**:
- Tipo de institución
- Naturaleza
- Código de área
- Estado/Municipio/Parroquia

### Campos de Email
```python
# Validación de formato y unicidad
EmailValidator()(valor)
if Model.objects.filter(email=valor).exists():
    raise ValidationError("Email ya registrado")
```

---

## 🔐 Validaciones en Múltiples Capas

### Capa 1: Frontend (JavaScript)
```javascript
// Validación básica en tiempo real
- Formato de campos
- Longitud mínima/máxima
- Caracteres permitidos
```

### Capa 2: Formulario Django (Python)
```python
# Validación robusta en servidor
- clean_<campo>() para validaciones individuales
- clean() para validaciones cruzadas
- Sanitización de datos
```

### Capa 3: Modelo Django (Python)
```python
# Validación final antes de guardar
- Validadores de campo
- clean() del modelo
- Constraints de BD
```

### Capa 4: Base de Datos
```sql
-- Constraints y tipos de datos
- NOT NULL
- UNIQUE
- CHECK constraints
- Foreign Keys
```

---

## ✅ Checklist de Seguridad

### Validaciones Implementadas
- [x] Longitud máxima en todos los campos de texto
- [x] Sanitización de caracteres peligrosos (XSS)
- [x] Validación de formato en campos numéricos
- [x] Listas cerradas para selecciones
- [x] Validación de unicidad (email, cédula)
- [x] Validación de contraseñas robustas
- [x] Protección CSRF en formularios
- [x] Validación de tipos de datos
- [x] Regex para formatos específicos
- [x] Validaciones cruzadas entre campos

### Protecciones Activas
- [x] XSS (Cross-Site Scripting)
- [x] SQL Injection
- [x] CSRF (Cross-Site Request Forgery)
- [x] Command Injection
- [x] Path Traversal
- [x] Buffer Overflow (límites de longitud)
- [x] Type Confusion (validación de tipos)

---

## 🧪 Ejemplos de Validación

### Ejemplo 1: Validación de Nombre
```python
# Input malicioso
nombre = "<script>alert('XSS')</script>"

# Validación
if re.search(r'[<>"\'']', nombre):
    raise ValidationError("Contiene caracteres no permitidos")

# Resultado: ❌ Rechazado
```

### Ejemplo 2: Validación de Teléfono
```python
# Input malicioso
telefono = "'; DROP TABLE users; --"

# Validación
if not telefono.isdigit() or len(telefono) != 7:
    raise ValidationError("Debe tener 7 dígitos")

# Resultado: ❌ Rechazado
```

### Ejemplo 3: Validación de Email
```python
# Input duplicado
email = "usuario@existente.com"

# Validación
if Institucion.objects.filter(email=email).exists():
    raise ValidationError("Email ya registrado")

# Resultado: ❌ Rechazado
```

### Ejemplo 4: Validación de Contraseña
```python
# Input débil
password = "12345678"

# Validación
if not any(ch.isupper() for ch in password):
    raise ValidationError("Debe incluir mayúscula")
if not any(ch in "!@#$%^&*()" for ch in password):
    raise ValidationError("Debe incluir carácter especial")

# Resultado: ❌ Rechazado
```

---

## 📝 Recomendaciones Adicionales

### Para Producción
1. ✅ Activar `DEBUG=False`
2. ✅ Configurar `ALLOWED_HOSTS` correctamente
3. ✅ Usar HTTPS (SSL/TLS)
4. ✅ Configurar headers de seguridad
5. ✅ Implementar rate limiting
6. ✅ Logs de intentos sospechosos

### Para Desarrollo
1. ✅ Probar con inputs maliciosos
2. ✅ Verificar mensajes de error
3. ✅ Revisar logs de validación
4. ✅ Testear límites de longitud
5. ✅ Validar caracteres especiales

---

## 🔍 Verificación de Validaciones

### Test Manual
```python
# En Django shell
from users.forms import InstitucionRegistrationForm

# Test XSS
data = {'nombre': '<script>alert("XSS")</script>'}
form = InstitucionRegistrationForm(data=data)
print(form.is_valid())  # False
print(form.errors)  # Muestra error de caracteres no permitidos

# Test longitud
data = {'nombre': 'A' * 300}
form = InstitucionRegistrationForm(data=data)
print(form.is_valid())  # False
print(form.errors)  # Muestra error de longitud
```

### Test Automatizado
```python
# En tests.py
def test_xss_protection():
    form = InstitucionRegistrationForm(data={
        'nombre': '<script>alert("XSS")</script>'
    })
    assert not form.is_valid()
    assert 'caracteres no permitidos' in str(form.errors)
```

---

**Última actualización**: Febrero 2026
**Estado**: ✅ Implementado y Probado
**Nivel de seguridad**: Alto
