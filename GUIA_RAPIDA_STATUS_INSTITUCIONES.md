# 🚀 Guía Rápida: Gestión de Status de Instituciones

## 📋 Resumen del Problema Resuelto

**Problema**: Las instituciones nuevas aparecían con status "aprobado" y activas por defecto.

**Solución**: Ahora todas las instituciones nuevas se registran con:
- ✅ `activa = False` (desactivada)
- ✅ `estatus = 'pendiente'` (esperando aprobación)
- ✅ Usuario de Django con `is_active = False` (no puede iniciar sesión)

## 🎯 Flujo de Aprobación

### Para Usuarios Públicos

1. **Registro**: Usuario completa formulario en `/registrar-institucion/`
2. **Estado Inicial**:
   - Institución creada con status "pendiente"
   - Código temporal: `TEMP-XXXXXXXX`
   - No puede iniciar sesión
3. **Confirmación**: Ve página "Registro Pendiente de Aprobación"
4. **Espera**: Hasta que un administrador apruebe la solicitud

### Para Administradores

#### Opción 1: Registro Directo desde Admin
1. Accede al panel de administración
2. Ve a "Gestión de Instituciones"
3. Clic en "Registrar Nueva Sede"
4. Completa el formulario
5. La institución se crea **automáticamente aprobada** y activa

#### Opción 2: Aprobar Solicitudes Pendientes
1. Accede al panel de administración Django: `/admin/`
2. Ve a **Registry → Instituciones**
3. Filtra por **Estatus: Pendiente**
4. Selecciona las instituciones a aprobar
5. En "Acciones", elige **"✅ Aprobar y generar códigos RNR"**
6. Clic en "Ejecutar"

**Resultado**:
- ✅ Status cambia a "aprobado"
- ✅ Campo `activa` cambia a `True`
- ✅ Se genera código RNR permanente: `RNR24-001002003-ABC12345`
- ✅ Usuario puede iniciar sesión
- ✅ Se envía correo de activación automáticamente

## 🛠️ Herramientas de Gestión

### Script de Verificación

Verifica el estado actual de las instituciones:

```bash
# Windows
gestionar_instituciones.bat
# Opción 1: Verificar status

# O manualmente:
cd SistemaRegistro
python manage.py shell < ..\verificar_status_instituciones.py
```

**Muestra**:
- Instituciones registradas recientemente
- Resumen general (pendientes, aprobadas, rechazadas)
- Instituciones pendientes de aprobación
- Inconsistencias detectadas

### Script de Corrección

Corrige instituciones con estados inconsistentes:

```bash
# Windows
gestionar_instituciones.bat
# Opción 2: Corregir inconsistencias

# O manualmente:
cd SistemaRegistro
python manage.py shell < ..\corregir_status_instituciones.py
```

**Corrige**:
- Instituciones pendientes marcadas como activas
- Instituciones aprobadas con códigos temporales
- Usuarios desactivados con instituciones aprobadas

## 📊 Panel de Administración Django

### Vista de Lista Mejorada

Ahora muestra:
- **Nombre**: Nombre de la institución
- **RIF**: Registro de Información Fiscal
- **Código**: Código RNR o temporal
- **Estatus**: Pendiente / Aprobado / Rechazado
- **Activa**: Sí / No
- **Federado**: Sí / No

### Filtros Disponibles

- Por **Estatus** (Pendiente, Aprobado, Rechazado)
- Por **Activa** (Sí, No)
- Por **Federado** (Sí, No)
- Por **Estado** (geográfico)

### Acciones Disponibles

1. **✅ Aprobar y generar códigos RNR**: Aprueba instituciones pendientes
2. **⬇️ Exportar a Excel**: Exporta instituciones seleccionadas

## 🔍 Verificación Manual

### Desde Django Shell

```python
# Abrir shell
python manage.py shell

# Verificar última institución registrada
from registry.models import Institucion
inst = Institucion.objects.latest('fecha_registro')

print(f"Nombre: {inst.nombre}")
print(f"Código: {inst.codigo}")
print(f"Estatus: {inst.estatus}")
print(f"Activa: {inst.activa}")
print(f"Usuario activo: {inst.usuario.is_active if inst.usuario else 'Sin usuario'}")

# Ver instituciones pendientes
pendientes = Institucion.objects.filter(estatus='pendiente')
print(f"\nInstituciones pendientes: {pendientes.count()}")
for p in pendientes:
    print(f"  - {p.nombre} ({p.codigo})")
```

## 📧 Notificaciones por Correo

Cuando una institución es aprobada, el sistema automáticamente:

1. Genera código RNR permanente
2. Activa la cuenta de usuario
3. Envía correo con:
   - Código RNR (username para login)
   - Instrucciones de acceso
   - URL de login

**Nota**: Verifica que las variables de entorno de correo estén configuradas en `.env`:
```
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_app
```

## ⚠️ Problemas Comunes

### Problema 1: Institución aprobada pero usuario no puede loguearse

**Causa**: Usuario de Django no activado

**Solución**:
```python
from registry.models import Institucion
inst = Institucion.objects.get(codigo='RNR24-...')
inst.usuario.is_active = True
inst.usuario.save()
```

### Problema 2: Institución aprobada con código temporal

**Causa**: No se generó código RNR al aprobar

**Solución**:
```python
from registry.models import Institucion
inst = Institucion.objects.get(codigo__startswith='TEMP-')
inst.activa = True
inst.estatus = 'aprobado'
inst.save()  # El modelo genera el código automáticamente
```

### Problema 3: Muchas instituciones pendientes

**Solución**: Usa el filtro en el admin y la acción masiva de aprobación

## 📝 Checklist de Aprobación

Antes de aprobar una institución, verifica:

- [ ] Nombre de la institución es correcto
- [ ] RIF es válido (formato: J-12345678-9)
- [ ] Email es válido y único
- [ ] Ubicación (Estado, Municipio, Parroquia) es correcta
- [ ] Tipo de institución es apropiado
- [ ] Código MPPE (si aplica) es válido

## 🔐 Seguridad

- ✅ Solo administradores pueden aprobar instituciones
- ✅ Usuarios con instituciones pendientes no pueden iniciar sesión
- ✅ Códigos RNR son únicos e irrepetibles
- ✅ Todas las acciones quedan registradas en logs

## 📞 Soporte

Si encuentras problemas:

1. Ejecuta el script de verificación
2. Revisa los logs en `logs/django.log`
3. Consulta la documentación completa en `CORRECCION_STATUS_INSTITUCIONES.md`
4. Contacta al equipo técnico

---

**Última actualización**: 2024
**Versión del sistema**: SNR-PRO v1.0
