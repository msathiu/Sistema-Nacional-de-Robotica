# 🎯 Mejores Prácticas - Sistema Nacional de Robótica

## 📚 Guía de Desarrollo

Este documento establece las mejores prácticas para el desarrollo y mantenimiento del Sistema Nacional de Robótica.

---

## 1. 🔐 Seguridad

### 1.1 Variables de Entorno

**✅ HACER:**
```python
# settings.py
SECRET_KEY = os.getenv("SECRET_KEY", "default-for-dev-only")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

**❌ NO HACER:**
```python
# settings.py
SECRET_KEY = "mi-clave-secreta-123"  # ¡NUNCA!
DEBUG = True  # ¡NUNCA en producción!
```

### 1.2 Contraseñas y Credenciales

- ✅ Usar variables de entorno para todas las credenciales
- ✅ Nunca commitear archivos `.env` al repositorio
- ✅ Mantener `.env.example` actualizado sin valores reales
- ✅ Usar gestores de secretos en producción (AWS Secrets Manager, Azure Key Vault, etc.)

### 1.3 Validación de Entrada

**✅ HACER:**
```python
def clean_cedula(self):
    cedula = self.cleaned_data.get('cedula')
    if not validar_cedula_venezolana(cedula):
        raise ValidationError("Cédula inválida")
    return cedula
```

**❌ NO HACER:**
```python
def save(self):
    # Guardar sin validar
    super().save()
```

---

## 2. 📊 Base de Datos

### 2.1 Índices

**Cuándo agregar índices:**
- ✅ Campos usados frecuentemente en `WHERE`, `JOIN`, `ORDER BY`
- ✅ Claves foráneas
- ✅ Campos únicos
- ✅ Campos usados en búsquedas

**Ejemplo:**
```python
class Meta:
    indexes = [
        models.Index(fields=['campo_frecuente'], name='idx_modelo_campo'),
        models.Index(fields=['campo1', 'campo2'], name='idx_modelo_compuesto'),
    ]
```

### 2.2 Consultas Optimizadas

**✅ HACER:**
```python
# Usar select_related para ForeignKey
participantes = Participante.objects.select_related(
    'institucion', 'estado', 'municipio'
).all()

# Usar prefetch_related para ManyToMany
grupos = Grupo.objects.prefetch_related('participantes').all()

# Usar only() para campos específicos
instituciones = Institucion.objects.only('nombre', 'codigo').all()
```

**❌ NO HACER:**
```python
# N+1 queries
for participante in Participante.objects.all():
    print(participante.institucion.nombre)  # Query por cada iteración
```

### 2.3 Transacciones

**✅ HACER:**
```python
from django.db import transaction

@transaction.atomic
def crear_participante_completo(datos):
    user = User.objects.create(**datos['user'])
    participante = Participante.objects.create(user=user, **datos['participante'])
    return participante
```

---

## 3. 🏗️ Modelos

### 3.1 Documentación

**✅ HACER:**
```python
class Participante(models.Model):
    """
    Modelo para representar participantes del sistema.

    Attributes:
        cedula: Cédula de identidad venezolana
        nombres: Nombres del participante
        edad: Propiedad calculada que retorna la edad actual
    """

    @property
    def edad(self):
        """Calcula y retorna la edad actual del participante."""
        today = date.today()
        return today.year - self.fecha_nacimiento.year
```

### 3.2 Validaciones

**✅ HACER:**
```python
def clean(self):
    """Valida los datos del modelo antes de guardar."""
    super().clean()

    if self.fecha_nacimiento:
        if self.edad < 4:
            raise ValidationError({
                'fecha_nacimiento': 'Edad mínima: 4 años'
            })
```

### 3.3 Propiedades vs Métodos

**Usar @property para:**
- Cálculos simples sin parámetros
- Valores derivados de campos del modelo

**Usar métodos para:**
- Operaciones complejas
- Funciones que requieren parámetros
- Operaciones que modifican datos

```python
# ✅ Propiedad
@property
def nombre_completo(self):
    return f"{self.nombres} {self.apellidos}"

# ✅ Método
def calcular_edad_en_fecha(self, fecha):
    return fecha.year - self.fecha_nacimiento.year
```

---

## 4. 📝 Formularios

### 4.1 Validación en Formularios

**✅ HACER:**
```python
class ParticipanteForm(forms.ModelForm):
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if Participante.objects.filter(cedula=cedula).exists():
            raise ValidationError("Esta cédula ya está registrada")
        return cedula

    def clean(self):
        cleaned_data = super().clean()
        # Validaciones que involucran múltiples campos
        return cleaned_data
```

### 4.2 Widgets Personalizados

**✅ HACER:**
```python
class Meta:
    widgets = {
        'fecha_nacimiento': forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        'descripcion': forms.Textarea(
            attrs={'rows': 3, 'class': 'form-control'}
        ),
    }
```

---

## 5. 🎨 Vistas

### 5.1 Manejo de Errores

**✅ HACER:**
```python
import logging

logger = logging.getLogger(__name__)

def mi_vista(request):
    try:
        # Lógica de la vista
        resultado = operacion_compleja()
        return render(request, 'template.html', {'resultado': resultado})
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        messages.error(request, "Datos inválidos")
        return redirect('formulario')
    except Exception as e:
        logger.exception(f"Error inesperado: {e}")
        messages.error(request, "Error del sistema")
        return redirect('home')
```

### 5.2 Decoradores

**✅ HACER:**
```python
from django.contrib.auth.decorators import login_required, user_passes_test

def es_admin(user):
    return user.is_authenticated and user.userprofile.user_type == 'admin'

@login_required
@user_passes_test(es_admin)
def vista_admin(request):
    # Solo accesible para administradores
    pass
```

### 5.3 Mensajes al Usuario

**✅ HACER:**
```python
from django.contrib import messages

def crear_participante(request):
    if form.is_valid():
        form.save()
        messages.success(request, "Participante creado exitosamente")
        return redirect('lista_participantes')
    else:
        messages.error(request, "Por favor corrige los errores")
```

---

## 6. 🧪 Testing

### 6.1 Tests de Modelos

**✅ HACER:**
```python
from django.test import TestCase

class ParticipanteModelTest(TestCase):
    def setUp(self):
        self.participante = Participante.objects.create(
            cedula="V12345678",
            nombres="Juan",
            apellidos="Pérez",
            fecha_nacimiento=date(2010, 1, 1)
        )

    def test_edad_calculada_correctamente(self):
        """Verifica que la edad se calcule correctamente"""
        edad_esperada = date.today().year - 2010
        self.assertEqual(self.participante.edad, edad_esperada)

    def test_validacion_edad_minima(self):
        """Verifica que no se permitan menores de 4 años"""
        participante = Participante(
            fecha_nacimiento=date.today()
        )
        with self.assertRaises(ValidationError):
            participante.clean()
```

### 6.2 Tests de Vistas

**✅ HACER:**
```python
class VistaParticipanteTest(TestCase):
    def test_lista_participantes_requiere_login(self):
        """Verifica que la vista requiera autenticación"""
        response = self.client.get('/participantes/')
        self.assertEqual(response.status_code, 302)  # Redirect a login

    def test_crear_participante_exitoso(self):
        """Verifica la creación exitosa de un participante"""
        self.client.login(username='test', password='test123')
        response = self.client.post('/participantes/crear/', {
            'cedula': 'V12345678',
            'nombres': 'Juan',
            # ... más datos
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Participante.objects.filter(cedula='V12345678').exists())
```

---

## 7. 📖 Documentación

### 7.1 Docstrings

**Formato recomendado:**
```python
def funcion_compleja(parametro1, parametro2, opcional=None):
    """
    Descripción breve de la función.

    Descripción más detallada si es necesario, explicando
    el propósito y comportamiento de la función.

    Args:
        parametro1 (str): Descripción del parámetro 1
        parametro2 (int): Descripción del parámetro 2
        opcional (bool, optional): Descripción del parámetro opcional.
            Defaults to None.

    Returns:
        dict: Descripción del valor retornado

    Raises:
        ValueError: Cuándo y por qué se lanza esta excepción

    Example:
        >>> resultado = funcion_compleja("test", 42)
        >>> print(resultado)
        {'status': 'success'}
    """
    pass
```

### 7.2 Comentarios en Código

**✅ HACER:**
```python
# Calcular el total considerando descuentos especiales
# para instituciones educativas públicas
if institucion.tipo == 'educativa' and institucion.naturaleza == 'publica':
    total = calcular_con_descuento(monto, 0.15)
```

**❌ NO HACER:**
```python
# Sumar 1
contador = contador + 1  # Comentario obvio e innecesario
```

---

## 8. 🚀 Despliegue

### 8.1 Checklist Pre-Producción

- [ ] `DEBUG = False`
- [ ] SECRET_KEY única y segura
- [ ] ALLOWED_HOSTS configurado correctamente
- [ ] Base de datos de producción configurada
- [ ] Archivos estáticos recolectados (`collectstatic`)
- [ ] Migraciones aplicadas
- [ ] Variables de entorno configuradas
- [ ] HTTPS habilitado
- [ ] Backups configurados
- [ ] Monitoreo configurado
- [ ] Logs configurados

### 8.2 Comandos Útiles

```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Verificar configuración
python manage.py check --deploy

# Limpiar sesiones expiradas
python manage.py clearsessions
```

---

## 9. 🔄 Git y Control de Versiones

### 9.1 Commits

**✅ Formato recomendado:**
```
tipo(alcance): descripción breve

Descripción más detallada si es necesario.

- Cambio 1
- Cambio 2
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formato, punto y coma faltante, etc.
- `refactor`: Refactorización de código
- `test`: Agregar tests
- `chore`: Mantenimiento

**Ejemplo:**
```
feat(participantes): agregar validación de edad mínima

Implementa validación para asegurar que los participantes
tengan al menos 4 años de edad.

- Agregar método clean() en modelo Participante
- Agregar tests para validación
- Actualizar formulario con mensaje de error
```

### 9.2 Branches

**Estrategia recomendada:**
- `main`: Código en producción
- `develop`: Código en desarrollo
- `feature/nombre`: Nuevas funcionalidades
- `fix/nombre`: Correcciones de bugs
- `hotfix/nombre`: Correcciones urgentes en producción

---

## 10. 📊 Monitoreo y Logging

### 10.1 Niveles de Log

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: Información detallada para diagnóstico
logger.debug("Valor de variable: %s", variable)

# INFO: Confirmación de que las cosas funcionan
logger.info("Usuario %s inició sesión", username)

# WARNING: Algo inesperado pero no crítico
logger.warning("Intento de acceso no autorizado desde IP %s", ip)

# ERROR: Error que impide una función específica
logger.error("Error al procesar pago: %s", error)

# CRITICAL: Error grave que puede detener la aplicación
logger.critical("Base de datos no disponible")
```

### 10.2 Métricas Importantes

**Monitorear:**
- Tiempo de respuesta de vistas
- Tasa de errores
- Uso de memoria y CPU
- Consultas lentas a la base de datos
- Intentos de acceso no autorizado
- Tasa de conversión de registros

---

## 📚 Recursos Adicionales

- [Documentación oficial de Django](https://docs.djangoproject.com/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [Django Security Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

---

**Última actualización:** Febrero 2026
**Mantenido por:** Equipo de Desarrollo SNR
