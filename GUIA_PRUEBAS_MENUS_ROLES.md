# 🧪 Guía de Pruebas: Menús por Roles

## 📋 Checklist de Verificación

### ✅ Preparación

- [ ] Servidor Django corriendo
- [ ] Base de datos con usuarios de diferentes roles
- [ ] Navegador web abierto

---

## 🧑‍💼 Prueba 1: Usuario Federación Regional

### Datos de Prueba
```
Rol: fed_regional
Estado asignado: [Tu estado]
```

### Pasos:
1. **Iniciar sesión** con usuario regional
2. **Verificar menú lateral** debe mostrar SOLO:
   - [ ] ✅ Inicio
   - [ ] ✅ Mi Perfil Profesional
   - [ ] ✅ Instituciones
   - [ ] ✅ Participantes
   - [ ] ✅ Métricas Clubes

3. **Verificar que NO aparezcan:**
   - [ ] ❌ Revisar Clubes
   - [ ] ❌ Solicitudes Eliminación
   - [ ] ❌ Papelera
   - [ ] ❌ Gestionar Sedes

4. **Probar acceso directo por URL:**
   ```
   http://localhost:8000/revisar-clubes/
   ```
   - [ ] Debe mostrar: "No tienes permiso para acceder a esta página"

5. **Verificar filtrado por estado:**
   - Ir a "Instituciones"
   - [ ] Solo debe mostrar instituciones del estado asignado
   - Ir a "Métricas Clubes"
   - [ ] Solo debe mostrar datos del estado asignado

### ✅ Resultado Esperado
```
✓ Menú limpio sin opciones administrativas
✓ Acceso directo bloqueado por decoradores
✓ Datos filtrados por estado
```

---

## 👨‍💼 Prueba 2: Usuario Federación Central

### Datos de Prueba
```
Rol: fed_central
```

### Pasos:
1. **Iniciar sesión** con usuario central
2. **Verificar menú lateral** debe mostrar TODO:
   - [ ] ✅ Inicio
   - [ ] ✅ Mi Perfil Profesional
   - [ ] ✅ Instituciones
   - [ ] ✅ Participantes
   - [ ] ✅ Revisar Clubes
   - [ ] ✅ Solicitudes Eliminación
   - [ ] ✅ Papelera
   - [ ] ✅ Métricas Clubes
   - [ ] ✅ Gestionar Sedes

3. **Probar acceso a funciones administrativas:**
   - Ir a "Revisar Clubes"
   - [ ] Debe cargar correctamente
   - [ ] Debe mostrar clubes de todos los estados
   - Ir a "Gestionar Sedes"
   - [ ] Debe cargar correctamente

4. **Verificar datos sin filtro:**
   - Ir a "Instituciones"
   - [ ] Debe mostrar instituciones de TODOS los estados
   - Ir a "Métricas Clubes"
   - [ ] Debe mostrar datos de TODOS los estados

### ✅ Resultado Esperado
```
✓ Menú completo con todas las opciones
✓ Acceso a todas las funciones administrativas
✓ Datos sin filtrar por estado
```

---

## 🏢 Prueba 3: Usuario Institucional

### Datos de Prueba
```
Rol: institucional
Institución asignada: [Tu institución]
```

### Pasos:
1. **Iniciar sesión** con usuario institucional
2. **Verificar menú lateral** debe mostrar:
   - [ ] ✅ Inicio
   - [ ] ✅ Perfil Sede
   - [ ] ✅ Notificaciones
   - [ ] ✅ Mis Clubes
   - [ ] ✅ Directorio Clubes
   - [ ] ✅ Búsqueda Avanzada
   - [ ] ✅ Eventos
   - [ ] ✅ Mis Grupos
   - [ ] ✅ Participantes

3. **Verificar que NO aparezcan:**
   - [ ] ❌ Revisar Clubes
   - [ ] ❌ Solicitudes Eliminación
   - [ ] ❌ Papelera
   - [ ] ❌ Gestionar Sedes
   - [ ] ❌ Métricas Clubes

4. **Verificar filtrado por institución:**
   - Ir a "Mis Clubes"
   - [ ] Solo debe mostrar clubes de su institución
   - Ir a "Participantes"
   - [ ] Solo debe mostrar participantes de su institución

### ✅ Resultado Esperado
```
✓ Menú enfocado en gestión de su institución
✓ Sin opciones administrativas
✓ Datos filtrados por institución
```

---

## 🔍 Prueba 4: Verificación de Seguridad

### Intentar acceso no autorizado

#### Como Usuario Regional:
```bash
# Intentar acceder a URLs administrativas
http://localhost:8000/revisar-clubes/
http://localhost:8000/revisar-solicitudes-eliminacion/
http://localhost:8000/clubes-eliminados/
http://localhost:8000/gestionar-sedes/
```

**Resultado esperado:**
- [ ] Todas deben redirigir o mostrar "Sin permiso"
- [ ] No debe haber errores 500

#### Como Usuario Institucional:
```bash
# Intentar acceder a URLs de federación
http://localhost:8000/lista-instituciones/
http://localhost:8000/dashboard-metricas-clubes/
```

**Resultado esperado:**
- [ ] Debe redirigir o mostrar "Sin permiso"
- [ ] No debe haber errores 500

---

## 📊 Prueba 5: Context Processor

### Verificar variables en template

1. **Agregar temporalmente en cualquier template:**
```django
<!-- DEBUG: Variables de rol -->
<div style="background: yellow; padding: 10px;">
    <p>es_central: {{ es_central }}</p>
    <p>es_regional: {{ es_regional }}</p>
    <p>es_institucional: {{ es_institucional }}</p>
    <p>perfil.user_type: {{ perfil.user_type }}</p>
</div>
```

2. **Verificar que las variables:**
   - [ ] Existen (no están vacías)
   - [ ] Tienen valores correctos según el rol
   - [ ] Se actualizan al cambiar de usuario

3. **Eliminar el código de debug**

---

## 🐛 Problemas Comunes y Soluciones

### Problema 1: Variables no definidas
```
NameError: 'es_central' is not defined
```

**Solución:**
```bash
# Verificar que el context processor está registrado
grep "user_roles" SistemaRegistro/SistemaRegistro/settings.py

# Reiniciar el servidor
python manage.py runserver
```

### Problema 2: Menú no cambia
```
El menú sigue mostrando todas las opciones
```

**Solución:**
```bash
# Limpiar cache del navegador
Ctrl + Shift + R (Chrome/Firefox)

# Verificar que el template usa las variables correctas
grep "es_regional" SistemaRegistro/templates/users/base_dashboard.html
```

### Problema 3: Error 500 al acceder
```
Internal Server Error
```

**Solución:**
```bash
# Ver logs del servidor
tail -f SistemaRegistro/logs/django.log

# Verificar decoradores en las vistas
grep "@role_required" SistemaRegistro/users/views.py
```

---

## ✅ Checklist Final

### Funcionalidad
- [ ] Menú regional no muestra opciones administrativas
- [ ] Menú central muestra todas las opciones
- [ ] Menú institucional muestra opciones de gestión
- [ ] Acceso directo por URL está bloqueado
- [ ] Filtrado por estado/institución funciona

### Seguridad
- [ ] Decoradores protegen las vistas
- [ ] No hay errores 500 en accesos no autorizados
- [ ] Variables de contexto no exponen información sensible

### UX/UI
- [ ] Menús son claros y concisos
- [ ] No hay opciones confusas o engañosas
- [ ] Mensajes de error son informativos

### Código
- [ ] Context processor registrado en settings
- [ ] Template usa lógica correcta de roles
- [ ] No hay código duplicado

---

## 📝 Reporte de Pruebas

### Plantilla de Reporte

```markdown
## Reporte de Pruebas - Menús por Roles

**Fecha:** [Fecha]
**Probador:** [Nombre]
**Versión:** [Versión del sistema]

### Resultados

#### Usuario Regional
- Menú: ✅ / ❌
- Filtrado: ✅ / ❌
- Seguridad: ✅ / ❌

#### Usuario Central
- Menú: ✅ / ❌
- Acceso completo: ✅ / ❌

#### Usuario Institucional
- Menú: ✅ / ❌
- Filtrado: ✅ / ❌

### Problemas Encontrados
1. [Descripción del problema]
2. [Descripción del problema]

### Observaciones
[Comentarios adicionales]
```

---

## 🚀 Siguiente Paso

Una vez completadas todas las pruebas:

```bash
# Ejecutar verificación automática
./verificar_menus_roles.sh

# Si todo está OK, hacer commit
git add .
git commit -m "fix: Corregir visualización de menús según roles de usuario"
```

---

## 📚 Referencias

- `CORRECCION_MENUS_ROLES.md` - Documentación técnica
- `RESUMEN_CORRECCION_MENUS.md` - Resumen ejecutivo
- `MEJORES_PRACTICAS.md` - Mejores prácticas del proyecto
